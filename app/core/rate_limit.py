"""Redis-backed fixed-window rate limiting middleware (fail-open)."""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import settings
from app.core.redis import get_redis

EXEMPT_PREFIXES = ("/docs", "/redoc", "/openapi.json", "/health", "/webhooks")


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if not settings.RATE_LIMIT_ENABLED or request.url.path.startswith(EXEMPT_PREFIXES):
            return await call_next(request)

        redis = await get_redis()
        if redis is None:  # fail open when Redis is down
            return await call_next(request)

        identity = self._identity(request)
        # 60-second fixed window keyed per identity.
        key = f"ratelimit:{identity}"
        try:
            current = await redis.incr(key)
            if current == 1:
                await redis.expire(key, 60)
            if current > settings.RATE_LIMIT_PER_MINUTE:
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": {
                            "code": "rate_limited",
                            "message": "Too many requests. Please slow down.",
                            "details": {},
                        }
                    },
                )
        except Exception:  # noqa: BLE001 — never block traffic on limiter errors
            return await call_next(request)

        return await call_next(request)

    @staticmethod
    def _identity(request: Request) -> str:
        auth = request.headers.get("authorization", "")
        if auth.startswith("Bearer "):
            return f"token:{auth[7:27]}"
        client = request.client.host if request.client else "anon"
        return f"ip:{client}"
