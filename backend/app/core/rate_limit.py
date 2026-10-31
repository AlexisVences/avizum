"""Per-client request limits for the public endpoints (login, register, agent search).

A sliding window kept in this process's memory. That is enough while the API runs as one process (the deployment
plan); with several workers each would count on its own and the real limit would be N times higher, so the day
that changes the counters move to the database or Redis behind this same interface.
"""
import math
import threading
import time
from collections import deque
from collections.abc import Callable

from fastapi import HTTPException, Request, status

from app.core.config import get_settings

_MAX_KEYS = 50_000  # bound on memory if someone rotates identities; past it the oldest idle keys are dropped


class SlidingWindowLimiter:
    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self._hits: dict[tuple[str, str], deque[float]] = {}
        self._lock = threading.Lock()
        self._clock = clock

    def hit(self, bucket: str, key: str, limit: int, window: float) -> float | None:
        """Count one request. Returns None if allowed, or the seconds to wait if the limit was exceeded."""
        now = self._clock()
        with self._lock:
            hits = self._hits.setdefault((bucket, key), deque())
            while hits and now - hits[0] >= window:
                hits.popleft()
            if len(hits) >= limit:
                return window - (now - hits[0])
            hits.append(now)
            if len(self._hits) > _MAX_KEYS:
                self._evict(now, window)
            return None

    def _evict(self, now: float, window: float) -> None:
        for key in [k for k, h in self._hits.items() if not h or now - h[-1] >= window]:
            del self._hits[key]

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


limiter = SlidingWindowLimiter()


def client_ip(request: Request) -> str:
    """The caller's address.

    With `trusted_proxy_count` = N, N proxies we control each appended the peer address they saw to X-Forwarded-For, so
    the client is the Nth entry from the right; anything further left was supplied by the client and is ignored (a
    forged `X-Forwarded-For: 1.2.3.4` only adds entries on the left). With N = 0 the header is never read. If the
    header has fewer than N entries the proxy chain is not what was configured, so fall back to the socket address."""
    settings = get_settings()
    count = getattr(settings, "trusted_proxy_count", 0) or (1 if getattr(settings, "trust_proxy_headers", False) else 0)
    if count > 0:
        entries = [part.strip() for part in request.headers.get("x-forwarded-for", "").split(",") if part.strip()]
        if len(entries) >= count:
            return entries[-count]
    return request.client.host if request.client else "unknown"


def too_many(wait: float) -> HTTPException:
    seconds = max(1, math.ceil(wait))
    return HTTPException(
        status.HTTP_429_TOO_MANY_REQUESTS,
        f"Demasiadas solicitudes. Intenta de nuevo en {seconds} segundos.",
        headers={"Retry-After": str(seconds)},
    )


def rate_limit(bucket: str, limit: int, window: float):
    """FastAPI dependency: `Depends(rate_limit("login", 10, 60))` limits by client address."""

    def dependency(request: Request) -> None:
        wait = limiter.hit(bucket, client_ip(request), limit, window)
        if wait is not None:
            raise too_many(wait)

    return dependency
