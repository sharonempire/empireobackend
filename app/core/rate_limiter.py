"""Redis-backed rate limiter for auth and write endpoints.

Provides a low-level `limit_key` helper plus a FastAPI dependency factory
`rate_limit(limit, period)` that can be injected into any endpoint.
"""
from typing import Optional

from fastapi import HTTPException, Request
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


def rate_limit(limit: int = 30, period_seconds: int = 60):
    """FastAPI dependency factory for per-user rate limiting on write endpoints.

    Usage:
        @router.post("/", dependencies=[Depends(rate_limit(limit=10, period_seconds=60))])
        async def create_thing(...): ...
    """

    async def _check(request: Request):
        # Prefer user ID if authenticated, fall back to IP
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            key = f"rate:write:{user_id}:{request.url.path}"
        else:
            ip = request.client.host if request.client else "unknown"
            key = f"rate:write:{ip}:{request.url.path}"

        remaining = await limit_key(key, limit, period_seconds)
        if remaining is not None and remaining <= 0:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later.",
            )

    return _check
