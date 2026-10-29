"""Request-id + access-log middleware, unhandled-exception handler and Sentry setup with PII scrubbing."""
import logging
import re
import time
import traceback
import uuid
from typing import Any

import jwt
from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.config import Settings, get_settings
from app.core.logging import SAFE_REQUEST_ID, request_id_var

access_logger = logging.getLogger("app.access")
error_logger = logging.getLogger("app.errors")

REDACTED = "[redacted]"
_EMAIL = re.compile(r"[A-Za-z0-9._%+'-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+")
_JWT = re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]*")
_TOKEN43 = re.compile(r"(?<![A-Za-z0-9_-])[A-Za-z0-9_-]{43}(?![A-Za-z0-9_-])")
_SENSITIVE_KEYS = ("authorization", "cookie", "token", "key", "secret", "password", "set-cookie")
_DROP_KEYS = {"data", "cookies", "query_string"}


def scrub_string(value: str) -> str:
    value = _JWT.sub(REDACTED, value)
    value = _EMAIL.sub(REDACTED, value)
    return _TOKEN43.sub(REDACTED, value)


def _scrub(value: Any, key: str = "") -> Any:
    if any(s in key.lower() for s in _SENSITIVE_KEYS):
        return REDACTED
    if isinstance(value, dict):
        return {k: _scrub(v, str(k)) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_scrub(v) for v in value]
    if isinstance(value, str):
        return scrub_string(value)
    return value


def _scrub_request(request: dict[str, Any]) -> dict[str, Any]:
    clean = {k: v for k, v in request.items() if k not in _DROP_KEYS}
    if "url" in clean and isinstance(clean["url"], str):
        clean["url"] = scrub_string(clean["url"].split("?", 1)[0].split("#", 1)[0])
    return _scrub(clean)


def scrub_event(event: dict[str, Any], hint: Any = None) -> dict[str, Any]:
    """Sentry before_send: pure function; strips bodies, cookies, query strings, sensitive headers and PII-looking values."""
    if "request" in event:
        event["request"] = _scrub_request(event["request"])
    event.pop("user", None)
    # Exception messages can embed SQL parameters (chat text, e-mails): keep the type and stack, drop the text.
    for exc in (event.get("exception") or {}).get("values", []):
        if "value" in exc:
            exc["value"] = REDACTED
    event.pop("message", None)
    event.pop("logentry", None)
    for k in ("extra", "contexts", "breadcrumbs", "exception", "tags", "transaction"):
        if k in event:
            event[k] = _scrub(event[k])
    return event


def scrub_breadcrumb(crumb: dict[str, Any], hint: Any = None) -> dict[str, Any] | None:
    if crumb.get("category") in {"httplib", "http"}:
        data = crumb.get("data") or {}
        crumb["data"] = {k: v for k, v in data.items() if k in {"method", "status_code", "reason"}}
        if "url" in data:
            crumb["data"]["url"] = scrub_string(str(data["url"]).split("?", 1)[0])
    return _scrub(crumb)


def init_sentry(settings: Settings | None = None) -> bool:
    settings = settings or get_settings()
    if settings.sentry_dsn is None or not settings.sentry_dsn.get_secret_value():
        return False
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.starlette import StarletteIntegration

    sentry_sdk.init(
        dsn=settings.sentry_dsn.get_secret_value(),
        environment=settings.sentry_environment or settings.environment,
        release=settings.git_sha or None,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        send_default_pii=False,
        include_local_variables=False,
        max_request_body_size="never",
        before_send=scrub_event,
        before_breadcrumb=scrub_breadcrumb,
        integrations=[StarletteIntegration(), FastApiIntegration()],
    )
    return True


def _user_id_from_header(scope, secret: str, algorithm: str) -> str | None:
    for name, value in scope["headers"]:
        if name == b"authorization":
            parts = value.decode("latin-1").split(" ", 1)
            if len(parts) == 2 and parts[0].lower() == "bearer":
                try:
                    return str(jwt.decode(parts[1], secret, algorithms=[algorithm]).get("sub"))
                except jwt.PyJWTError:
                    return None
    return None


class RequestContextMiddleware:
    """Plain ASGI (see SecurityHeadersMiddleware for why): request id, response header and one access-log line."""

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        incoming = next((v.decode("latin-1") for k, v in scope["headers"] if k == b"x-request-id"), "")
        request_id = incoming if SAFE_REQUEST_ID.match(incoming) else uuid.uuid4().hex
        token = request_id_var.set(request_id)
        scope.setdefault("state", {})["request_id"] = request_id
        status_code = 500
        started = time.perf_counter()

        async def send_with_id(message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                headers = [(k, v) for k, v in message["headers"] if k.lower() != b"x-request-id"]
                headers.append((b"x-request-id", request_id.encode()))
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_with_id)
        finally:
            route = scope.get("route")
            settings = get_settings()
            try:
                access_logger.info("request", extra={
                    "method": scope["method"],
                    "path": getattr(route, "path", None) or "unmatched",
                    "status": status_code,
                    "duration_ms": round((time.perf_counter() - started) * 1000, 1),
                    "user_id": _user_id_from_header(scope, settings.jwt_secret_key, settings.jwt_algorithm),
                })
            finally:
                request_id_var.reset(token)


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = request_id_var.get() or getattr(request.state, "request_id", None)
    token = request_id_var.set(request_id)
    try:
        # Only the exception type and the stack frames are logged: the message of a database or validation error can
        # embed parameters (chat text, e-mails). Sentry gets the event through its integration and the scrubbing hooks.
        error_logger.error("unhandled exception: %s", type(exc).__name__,
                           extra={"traceback": "".join(traceback.format_tb(exc.__traceback__))})
    finally:
        request_id_var.reset(token)
    return JSONResponse({"detail": "Internal server error", "request_id": request_id}, status_code=500,
                        headers={"X-Request-ID": request_id or ""})
