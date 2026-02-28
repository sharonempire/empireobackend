"""Auth service with refresh token rotation and reuse detection."""

import logging
import uuid as _uuid
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.events import log_event
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_token,
    verify_password,
    hash_password,
)
from app.modules.auth.models import RefreshToken
from app.modules.users.models import User

logger = logging.getLogger(__name__)


async def _verify_via_supabase_auth(email: str, password: str) -> bool:
    """Verify credentials against Supabase Auth (GoTrue) API.

    Returns True if Supabase Auth accepts the email+password combo.
    Returns False if credentials are invalid or Supabase Auth is unavailable.
    """
    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        return False

    url = f"{settings.SUPABASE_URL}/auth/v1/token?grant_type=password"
    headers = {
        "apikey": settings.SUPABASE_ANON_KEY,
        "Content-Type": "application/json",
    }
    payload = {"email": email, "password": password}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                return True
            # 400/401 = invalid credentials — that's fine, not an error
            return False
    except Exception as exc:
        logger.warning("Supabase Auth check failed (network error): %s", exc)
        return False


async def authenticate(db: AsyncSession, email: str, password: str) -> User | None:
    """Validate email + password. Tries Supabase Auth first, then local bcrypt.

    Flow:
    1. Look up user in eb_users by email
    2. Try verifying password via Supabase Auth API (existing passwords)
    3. If Supabase Auth succeeds, sync password hash to eb_users for local fallback
    4. If Supabase Auth unavailable/not configured, fall back to local bcrypt
    """
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        return None

    # Strategy 1: Verify via Supabase Auth (where existing passwords live)
    supabase_ok = await _verify_via_supabase_auth(email, password)
    if supabase_ok:
        # Sync password hash to eb_users so local bcrypt works in future
        user.hashed_password = hash_password(password)
        user.last_login_at = datetime.now(timezone.utc)
        await db.flush()
        return user

    # Strategy 2: Fall back to local bcrypt (works after password sync or manual set)
    if user.hashed_password and verify_password(password, user.hashed_password):
        user.last_login_at = datetime.now(timezone.utc)
        await db.flush()
        return user

    return None


async def issue_tokens(
    db: AsyncSession,
    user: User,
    family_id: _uuid.UUID | None = None,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> dict:
    """Create access + refresh tokens; store refresh token hash in DB."""
    access = create_access_token(str(user.id))
    refresh = create_refresh_token(str(user.id))

    if family_id is None:
        family_id = _uuid.uuid4()

    token_record = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(refresh),
        family_id=family_id,
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        user_agent=user_agent,
        ip_address=ip_address,
    )
    db.add(token_record)
    await db.flush()

    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}


async def rotate_refresh_token(
    db: AsyncSession,
    refresh_token: str,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> dict | None:
    """Rotate refresh token. Detects reuse and revokes entire family."""
    payload = decode_token(refresh_token)
    if payload is None or payload.get("type") != "refresh":
        return None

    user_id_str = payload.get("sub")
    if not user_id_str:
        return None

    token_h = hash_token(refresh_token)

    # Look up the token record
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_h)
    )
    token_record = result.scalar_one_or_none()

    if token_record is None:
        # Token not in DB -- could be very old or forged
        return None

    if token_record.is_revoked:
        # -- REUSE DETECTED --
        # Revoke the entire token family
        await db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.family_id == token_record.family_id,
                RefreshToken.is_revoked == False,  # noqa: E712
            )
            .values(
                is_revoked=True,
                revoked_at=datetime.now(timezone.utc),
                revoke_reason="reuse_detected",
            )
        )
        # Log security event
        await log_event(
            db=db,
            event_type="auth.refresh_reuse_detected",
            actor_id=token_record.user_id,
            entity_type="user",
            entity_id=token_record.user_id,
            metadata={
                "family_id": str(token_record.family_id),
                "ip_address": ip_address,
                "user_agent": user_agent,
            },
        )
        await db.commit()
        return None

    # -- Normal rotation --
    # Revoke the old token
    token_record.is_revoked = True
    token_record.revoked_at = datetime.now(timezone.utc)
    token_record.revoke_reason = "rotated"

    # Load user
    user_result = await db.execute(
        select(User).where(User.id == token_record.user_id)
    )
    user = user_result.scalar_one_or_none()
    if user is None or not user.is_active:
        return None

    # Issue new tokens in the same family
    new_tokens = await issue_tokens(
        db,
        user,
        family_id=token_record.family_id,
        user_agent=user_agent,
        ip_address=ip_address,
    )
    return new_tokens


async def revoke_token(db: AsyncSession, refresh_token: str) -> bool:
    """Revoke a single refresh token (logout)."""
    token_h = hash_token(refresh_token)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_h)
    )
    token_record = result.scalar_one_or_none()
    if token_record is None:
        return False
    token_record.is_revoked = True
    token_record.revoked_at = datetime.now(timezone.utc)
    token_record.revoke_reason = "logout"
    await db.flush()
    return True


async def revoke_all_user_tokens(
    db: AsyncSession, user_id, reason: str = "logout_all"
) -> int:
    """Revoke all active refresh tokens for a user."""
    result = await db.execute(
        update(RefreshToken)
        .where(
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked == False,  # noqa: E712
        )
        .values(
            is_revoked=True,
            revoked_at=datetime.now(timezone.utc),
            revoke_reason=reason,
        )
    )
    await db.flush()
    return result.rowcount


async def cleanup_expired_tokens(db: AsyncSession) -> int:
    """Delete expired tokens (housekeeping for Celery)."""
    result = await db.execute(
        delete(RefreshToken).where(
            RefreshToken.expires_at < datetime.now(timezone.utc)
        )
    )
    await db.flush()
    return result.rowcount


def verify_user_password(user: User, plain_password: str) -> bool:
    """Helper to verify a plain password against a User object."""
    return verify_password(plain_password, user.hashed_password)


async def update_user_password(db: AsyncSession, user_id, new_password: str) -> bool:
    """Update a user's password (hash and persist). Returns True if updated."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return False
    user.hashed_password = hash_password(new_password)
    await db.flush()
    return True
