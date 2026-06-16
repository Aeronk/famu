"""Shared async Redis client (lazy, fail-soft).

Returns ``None`` if Redis is unavailable so callers can degrade gracefully
(e.g. rate limiting fails open, caching is skipped) — the app still boots.
"""

from __future__ import annotations

import redis.asyncio as aioredis

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_client: aioredis.Redis | None = None
_unavailable = False


async def get_redis() -> aioredis.Redis | None:
    global _client, _unavailable
    if _unavailable:
        return None
    if _client is None:
        try:
            _client = aioredis.from_url(
                settings.REDIS_URL, encoding="utf-8", decode_responses=True
            )
            await _client.ping()
        except Exception as exc:  # noqa: BLE001
            logger.warning("redis_unavailable", error=str(exc))
            _client = None
            _unavailable = True
            return None
    return _client


async def close_redis() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
