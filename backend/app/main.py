from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import get_settings


SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cross-Origin-Resource-Policy": "same-site",
    "Cache-Control": "no-store",  # responses carry per-user data (conversations, profile)
}


class SecurityHeadersMiddleware:
    """Plain ASGI on purpose: @app.middleware("http") wraps the response in a way that hides client disconnects from
    streaming endpoints, and the chat relies on noticing them to save a cancelled answer."""

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        async def send_with_headers(message) -> None:
            if message["type"] == "http.response.start":
                present = {name.lower() for name, _ in message["headers"]}
                message["headers"] = list(message["headers"]) + [
                    (k.lower().encode(), v.encode()) for k, v in SECURITY_HEADERS.items() if k.lower().encode() not in present
                ]
            await send(message)

        await self.app(scope, receive, send_with_headers)


def create_app() -> FastAPI:
    settings = get_settings()
    if settings.environment == "production" and (problems := settings.production_problems()):
        raise RuntimeError("Unsafe production configuration: " + "; ".join(problems))
    production = settings.environment == "production"
    app = FastAPI(title="Avizum API", version="1.0.0", docs_url=None if production else "/docs",
                  redoc_url=None, openapi_url=None if production else "/openapi.json")
    if settings.cors_origin_list:
        app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list, allow_credentials=True, allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"], allow_headers=["Authorization", "Content-Type"])
    app.add_middleware(SecurityHeadersMiddleware)
    app.include_router(router)
    return app


app = create_app()
