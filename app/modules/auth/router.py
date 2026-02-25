import secrets

from fastapi import APIRouter, Depends, Header, HTTPException, status, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.modules.auth import service as auth_service
from app.modules.auth.schemas import (
    AdminResetPasswordRequest,
    BootstrapRequest,
    ChangePasswordRequest,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
)
from app.dependencies import get_current_user
from app.modules.users.models import Role, User, UserRole
from app.core.security import hash_password
from app.core.rate_limiter import limit_key
from app.core.events import log_event

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    # Basic per-IP rate limiting for login attempts
    ip = request.client.host if request.client else "unknown"
    key = f"rate:auth:login:{ip}"
    rem = await limit_key(key, limit=10, period_seconds=60)
    if rem is not None and rem < 0:
        raise HTTPException(status_code=429, detail="Too many login attempts, try again later")

    user = await auth_service.authenticate(db, data.email, data.password)
    if not user:
        # Audit failed login attempt
        await log_event(db, "auth.login_failed", actor_id=None, entity_type="user_email", entity_id=None, metadata={"email": data.email, "ip": ip})
        await db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    tokens = await auth_service.issue_tokens(db, user, user_agent=request.headers.get("user-agent"), ip_address=ip)
    await log_event(db, "auth.login", actor_id=user.id, entity_type="user", entity_id=user.id, metadata={"ip": ip})
    await db.commit()
    return tokens


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshRequest, request: Request, db: AsyncSession = Depends(get_db)):
    # Rate limit refresh attempts per IP
    ip = request.client.host if request.client else "unknown"
    key = f"rate:auth:refresh:{ip}"
    rem = await limit_key(key, limit=60, period_seconds=60)
    if rem is not None and rem < 0:
        raise HTTPException(status_code=429, detail="Too many refresh attempts, try again later")

    tokens = await auth_service.rotate_refresh_token(db, data.refresh_token, user_agent=request.headers.get("user-agent"), ip_address=ip)
    if not tokens:
        # Rotation failed — could be reuse or invalid token. The service logs reuse events.
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    # Successful rotation
    await log_event(db, "auth.refresh", actor_id=None, entity_type="user", entity_id=None, metadata={"ip": ip})
    await db.commit()
    return tokens


@router.post("/logout", response_model=None)
async def logout(data: RefreshRequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Revoke a single refresh token (logout).

    The client should supply the refresh token to revoke. If token is missing or
    already revoked this returns a 200 with ok=false to avoid leaking token state.
    """
    ok = await auth_service.revoke_token(db, data.refresh_token)
    if ok:
        await log_event(db, "auth.logout", actor_id=current_user.id, entity_type="user", entity_id=current_user.id)
        await db.commit()
    return {"ok": ok}


@router.post("/logout_all", response_model=None)
async def logout_all(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Revoke all refresh tokens for the current user (logout everywhere)."""
    count = await auth_service.revoke_all_user_tokens(db, current_user.id, reason="logout_all")
    await log_event(db, "auth.logout_all", actor_id=current_user.id, entity_type="user", entity_id=current_user.id, metadata={"revoked_count": count})
    await db.commit()
    return {"revoked": count}



@router.post("/change_password", response_model=None)
async def change_password(
    data: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Change the current user's password, revoke all refresh tokens, and log the event."""
    # Verify current password
    if not auth_service.verify_user_password(current_user, data.current_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password incorrect")

    # Update password
    await auth_service.update_user_password(db, current_user.id, data.new_password)

    # Revoke all tokens for this user
    revoked = await auth_service.revoke_all_user_tokens(db, current_user.id, reason="password_changed")
    await log_event(
        db,
        "auth.password_changed",
        actor_id=current_user.id,
        entity_type="user",
        entity_id=current_user.id,
        metadata={"revoked_count": revoked},
    )
    await db.commit()
    return {"ok": True, "revoked": revoked}


@router.post("/bootstrap", response_model=None)
async def bootstrap(
    data: BootstrapRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_bootstrap_token: str = Header(alias="X-Bootstrap-Token"),
):
    """One-time admin bootstrap. Only works when no users exist and a valid
    BOOTSTRAP_TOKEN is configured and supplied via X-Bootstrap-Token header."""

    # Guard: token must be configured on server
    if not settings.BOOTSTRAP_TOKEN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bootstrap not configured")

    # Guard: constant-time comparison to prevent timing attacks
    if not secrets.compare_digest(x_bootstrap_token, settings.BOOTSTRAP_TOKEN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid bootstrap token")

    # Guard: must be a fresh database with zero users
    user_count = (await db.execute(select(func.count()).select_from(User))).scalar()
    if user_count > 0:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bootstrap disabled (users already exist)")

    # Resolve the requested role
    role = (await db.execute(select(Role).where(Role.name == data.role))).scalar_one_or_none()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role '{data.role}' not found. Seed roles first (admin, manager, counselor, processor, viewer).",
        )

    # Create the first user
    user = User(
        email=data.email,
        full_name=data.full_name,
        hashed_password=hash_password(data.password),
        is_active=True,
    )
    db.add(user)
    await db.flush()

    # Assign role
    db.add(UserRole(user_id=user.id, role_id=role.id))
    await db.flush()

    # Audit
    ip = request.client.host if request.client else "unknown"
    await log_event(
        db,
        "auth.bootstrap_created",
        actor_id=user.id,
        entity_type="user",
        entity_id=user.id,
        metadata={"email": data.email, "role": data.role, "ip": ip},
    )
    await db.commit()

    return {"ok": True, "user_id": str(user.id), "email": user.email, "role": data.role}


@router.post("/reset-password", response_model=None)
async def admin_reset_password(
    data: AdminResetPasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_bootstrap_token: str = Header(alias="X-Bootstrap-Token"),
):
    """Admin password reset guarded by BOOTSTRAP_TOKEN. Use this to recover
    access when you cannot log in (e.g. after a hashing scheme migration)."""

    if not settings.BOOTSTRAP_TOKEN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bootstrap not configured")

    if not secrets.compare_digest(x_bootstrap_token, settings.BOOTSTRAP_TOKEN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid bootstrap token")

    user = (await db.execute(select(User).where(User.email == data.email))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.hashed_password = hash_password(data.new_password)
    await db.flush()

    ip = request.client.host if request.client else "unknown"
    await log_event(
        db,
        "auth.admin_reset_password",
        actor_id=user.id,
        entity_type="user",
        entity_id=user.id,
        metadata={"email": data.email, "ip": ip},
    )
    await db.commit()

    return {"ok": True, "email": user.email}
