"""Redis cache layer for read-heavy queries."""

import json
import logging
from typing import Any

import redis.asyncio as aioredis

from app.config import settings

logger = logging.getLogger("empireo.cache")

_redis_pool: aioredis.Redis | None = None


def _get_redis() -> aioredis.Redis:
    """Lazily initialize and return the async Redis client."""
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
        )
    return _redis_pool


def cache_key(*parts: str) -> str:
    """Build a namespaced cache key from parts.

    Example: cache_key("leads", "list", "page1") -> "empireo:leads:list:page1"
    """
    return "empireo:" + ":".join(parts)


async def get_cache(key: str) -> Any | None:
    """Get a value from Redis and deserialize from JSON.

    Returns None if the key does not exist or on any Redis error.
    """
    try:
        r = _get_redis()
        raw = await r.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception as exc:
        logger.warning("Cache GET failed for key %s: %s", key, exc)
        return None


async def set_cache(key: str, value: Any, ttl: int = 300) -> None:
    """Serialize value to JSON and store in Redis with a TTL (seconds).

    Default TTL is 300 seconds (5 minutes).
    """
    try:
        r = _get_redis()
        serialized = json.dumps(value, default=str)
        await r.set(key, serialized, ex=ttl)
    except Exception as exc:
        logger.warning("Cache SET failed for key %s: %s", key, exc)


async def delete_cache(key: str) -> None:
    """Delete a single key from Redis."""
    try:
        r = _get_redis()
        await r.delete(key)
    except Exception as exc:
        logger.warning("Cache DELETE failed for key %s: %s", key, exc)


async def delete_pattern(pattern: str) -> None:
    """Delete all keys matching a glob pattern (for cache invalidation).

    Example: delete_pattern("empireo:leads:*") removes all cached lead queries.
    Uses SCAN to avoid blocking Redis with KEYS on large datasets.
    """
    try:
        r = _get_redis()
        cursor = 0
        while True:
            cursor, keys = await r.scan(cursor=cursor, match=pattern, count=100)
            if keys:
                await r.delete(*keys)
            if cursor == 0:
                break
    except Exception as exc:
        logger.warning("Cache DELETE PATTERN failed for %s: %s", pattern, exc)
