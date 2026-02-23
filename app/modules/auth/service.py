from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, create_refresh_token, decode_token, verify_password
from app.modules.users.models import User


async def authenticate(db: AsyncSession, email: str, password: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    user.last_login_at = datetime.now(timezone.utc)
    await db.flush()
    return user


def issue_tokens(user: User) -> dict:
    access = create_access_token(str(user.id))
    refresh = create_refresh_token(str(user.id))
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}


def refresh_access_token(refresh_token: str) -> dict | None:
    payload = decode_token(refresh_token)
    if payload is None or payload.get("type") != "refresh":
        return None
    subject = payload.get("sub")
    if not subject:
        return None
    access = create_access_token(subject)
    refresh = create_refresh_token(subject)
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}
