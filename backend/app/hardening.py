"""Security headers, a small in-memory rate limit for the costly endpoint, safe 500s."""

from __future__ import annotations

import logging
import threading
import time
from collections import deque

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.config import Settings, get_settings

log = logging.getLogger("incidentpilot")


class SlidingWindowLimiter:
    """Allow at most `limit` events per `window_s`. Thread-safe, single process."""

    def __init__(self, limit: int, window_s: float = 60.0) -> None:
        self.limit, self.window_s = limit, window_s
        self._events: deque[float] = deque()
        self._lock = threading.Lock()

    def check(self, now: float | None = None) -> float | None:
        """None if allowed (and recorded); else seconds until a slot frees."""
        if self.limit <= 0:
            return None
        t = time.monotonic() if now is None else now
        with self._lock:
            while self._events and t - self._events[0] >= self.window_s:
                self._events.popleft()
            if len(self._events) >= self.limit:
                return max(0.0, self.window_s - (t - self._events[0]))
            self._events.append(t)
            return None


_limiters: dict[int, SlidingWindowLimiter] = {}


def investigation_rate_limit(request: Request) -> None:
    settings: Settings = request.app.dependency_overrides.get(get_settings, get_settings)()
    limit = settings.max_investigations_per_minute
    lim = getattr(request.app.state, "limiter", None)
    if lim is None or lim.limit != limit:
        lim = request.app.state.limiter = SlidingWindowLimiter(limit)
    wait = lim.check()
    if wait is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many investigations; each one calls Amazon Bedrock. Try again shortly.",
            headers={"Retry-After": str(int(wait) + 1)},
        )


def install(app: FastAPI) -> None:
    @app.middleware("http")
    async def headers(request: Request, call_next):  # type: ignore[no-untyped-def]
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        if request.url.path.startswith("/api/"):
            response.headers.setdefault("Cache-Control", "no-store")
        return response

    @app.exception_handler(Exception)
    async def unhandled(request: Request, exc: Exception) -> JSONResponse:
        # Log the type only: exception text from AWS/SDK calls could carry sensitive details.
        log.error("unhandled %s on %s %s", type(exc).__name__, request.method, request.url.path)
        return JSONResponse(status_code=500, content={"detail": "Internal server error."})
