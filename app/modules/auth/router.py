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
    LoginResponse,
    OTPSendRequest,
    OTPVerifyRequest,
    RefreshRequest,
    TokenResponse,
)
from app.dependencies import get_current_user
from app.modules.users.models import Role, User, UserRole
from app.core.security import hash_password
from app.core.rate_limiter import limit_key
from app.core.events import log_event

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.get("/profile")
async def get_profile(current_user: User = Depends(get_current_user)):
    """Return the current user's profile info (used by Flutter frontend)."""
    return {
        "user_id": current_user.id,
        "profile_id": current_user.legacy_supabase_id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "phone": current_user.phone,
        "department": current_user.department,
        "is_active": current_user.is_active,
        "profile_picture": current_user.profile_picture,
        "caller_id": current_user.caller_id,
        "location": current_user.location,
        "countries": current_user.countries,
        "roles": current_user.roles,
        "last_login_at": current_user.last_login_at,
    }


@router.post("/login", response_model=LoginResponse)
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
    return {
        **tokens,
        "user_id": user.id,
        "profile_id": user.legacy_supabase_id,
        "email": user.email,
        "full_name": user.full_name,
        "roles": user.roles,
    }


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


# ── OTP (via Supabase Auth) ─────────────────────────────────────────


@router.post("/otp/send")
async def otp_send(data: OTPSendRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """Send OTP via Supabase Auth (phone SMS or email).

    Provide either `phone` (E.164 format, e.g. +918129130745) or `email`.
    Requires Supabase phone provider configured for SMS OTP.
    """
    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        raise HTTPException(status_code=501, detail="OTP not configured (missing SUPABASE_URL or SUPABASE_ANON_KEY)")

    if not data.phone and not data.email:
        raise HTTPException(status_code=400, detail="Provide either phone or email")

    ip = request.client.host if request.client else "unknown"
    key = f"rate:auth:otp_send:{ip}"
    rem = await limit_key(key, limit=5, period_seconds=60)
    if rem is not None and rem < 0:
        raise HTTPException(status_code=429, detail="Too many OTP requests, try again later")

    from app.core.otp_service import send_phone_otp, send_email_otp

    if data.phone:
        result = await send_phone_otp(data.phone)
    else:
        result = await send_email_otp(data.email)

    if not result["ok"]:
        await log_event(db, "auth.otp_send_failed", actor_id=None, entity_type="otp",
                        entity_id=None, metadata={"phone": data.phone, "email": data.email, "ip": ip, "error": result.get("error")})
        await db.commit()
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to send OTP"))

    await log_event(db, "auth.otp_sent", actor_id=None, entity_type="otp",
                    entity_id=None, metadata={"phone": data.phone, "email": data.email, "ip": ip})
    await db.commit()
    return {"ok": True, "message": result["message"]}


@router.post("/otp/verify", response_model=LoginResponse)
async def otp_verify(data: OTPVerifyRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """Verify OTP and issue JWT tokens.

    On success, looks up the user in eb_users by phone or email,
    and returns the same response as /login (access_token, refresh_token, user info).
    """
    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        raise HTTPException(status_code=501, detail="OTP not configured (missing SUPABASE_URL or SUPABASE_ANON_KEY)")

    if not data.phone and not data.email:
        raise HTTPException(status_code=400, detail="Provide either phone or email")

    ip = request.client.host if request.client else "unknown"
    key = f"rate:auth:otp_verify:{ip}"
    rem = await limit_key(key, limit=10, period_seconds=60)
    if rem is not None and rem < 0:
        raise HTTPException(status_code=429, detail="Too many OTP verification attempts, try again later")

    from app.core.otp_service import verify_phone_otp, verify_email_otp

    if data.phone:
        result = await verify_phone_otp(data.phone, data.otp_code)
    else:
        result = await verify_email_otp(data.email, data.otp_code)

    if not result["ok"]:
        await log_event(db, "auth.otp_verify_failed", actor_id=None, entity_type="otp",
                        entity_id=None, metadata={"phone": data.phone, "email": data.email, "ip": ip})
        await db.commit()
        raise HTTPException(status_code=401, detail=result.get("error", "Invalid OTP"))

    # OTP verified — now find the user in eb_users
    if data.phone:
        # Strip leading + and country code variations for flexible matching
        phone_raw = data.phone.lstrip("+")
        # Try matching phone field (may store with or without country code)
        user = (await db.execute(
            select(User).where(
                (User.phone == data.phone) | (User.phone == phone_raw) |
                (User.phone == phone_raw[-10:])  # last 10 digits
            )
        )).scalar_one_or_none()
    else:
        user = (await db.execute(
            select(User).where(User.email == data.email)
        )).scalar_one_or_none()

    if not user or not user.is_active:
        await log_event(db, "auth.otp_user_not_found", actor_id=None, entity_type="otp",
                        entity_id=None, metadata={"phone": data.phone, "email": data.email, "ip": ip})
        await db.commit()
        raise HTTPException(status_code=404, detail="OTP verified but no matching user account found")

    # Issue our own JWT tokens (same as /login)
    tokens = await auth_service.issue_tokens(db, user, user_agent=request.headers.get("user-agent"), ip_address=ip)
    await log_event(db, "auth.otp_login", actor_id=user.id, entity_type="user",
                    entity_id=user.id, metadata={"method": "phone" if data.phone else "email", "ip": ip})
    await db.commit()
    return {
        **tokens,
        "user_id": user.id,
        "profile_id": user.legacy_supabase_id,
        "email": user.email,
        "full_name": user.full_name,
        "roles": user.roles,
    }
