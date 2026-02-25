"""Push tokens service layer."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.push_tokens.models import UserFCMToken, UserPushToken
from app.modules.push_tokens.schemas import UserFCMTokenCreate, UserPushTokenCreate


async def list_push_tokens(
    db: AsyncSession, page: int = 1, size: int = 20, user_id: UUID | None = None
) -> tuple[list[UserPushToken], int]:
    stmt = select(UserPushToken)
    count_stmt = select(func.count()).select_from(UserPushToken)
    if user_id:
        stmt = stmt.where(UserPushToken.user_id == user_id)
        count_stmt = count_stmt.where(UserPushToken.user_id == user_id)
    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.offset((page - 1) * size).limit(size)
    result = await db.execute(stmt)
    return result.scalars().all(), total


async def create_push_token(db: AsyncSession, data: UserPushTokenCreate) -> UserPushToken:
    token = UserPushToken(**data.model_dump())
    db.add(token)
    await db.flush()
    return token


async def delete_push_token(db: AsyncSession, token_id: UUID) -> None:
    result = await db.execute(select(UserPushToken).where(UserPushToken.id == token_id))
    token = result.scalar_one_or_none()
    if not token:
        raise NotFoundError("Push token not found")
    await db.delete(token)
    await db.flush()


async def list_fcm_tokens(
    db: AsyncSession, page: int = 1, size: int = 20, user_id: UUID | None = None
) -> tuple[list[UserFCMToken], int]:
    stmt = select(UserFCMToken)
    count_stmt = select(func.count()).select_from(UserFCMToken)
    if user_id:
        stmt = stmt.where(UserFCMToken.user_id == user_id)
        count_stmt = count_stmt.where(UserFCMToken.user_id == user_id)
    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.offset((page - 1) * size).limit(size)
    result = await db.execute(stmt)
    return result.scalars().all(), total


async def create_fcm_token(db: AsyncSession, data: UserFCMTokenCreate) -> UserFCMToken:
    token = UserFCMToken(**data.model_dump())
    db.add(token)
    await db.flush()
    return token
