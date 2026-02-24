"""Simple Redis-backed rate limiter for critical auth endpoints.

This provides a small helper to increment a key with TTL and enforce a limit.
It is intentionally minimal: it uses Redis INCR and EXPIRE. For robust production
use a proxy rate limiter (e.g., nginx, cloud provider) or a dedicated library.
"""
from typing import Optional
import redis.asyncio as aioredis

from app.config import settings


async def limit_key(key: str, limit: int, period_seconds: int) -> Optional[int]:
    """Increment the key and return remaining allowance or None on error.

    Returns remaining attempts (>=0) or None on Redis error.
    """
    try:
        r = aioredis.from_url(settings.REDIS_URL)
        v = await r.incr(key)
        if v == 1:
            await r.expire(key, period_seconds)
        remaining = max(0, limit - int(v))
        await r.close()
        return remaining
    except Exception:
        return None
