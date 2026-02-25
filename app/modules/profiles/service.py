"""Profiles service layer (legacy read-only)."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.profiles.models import Profile


async def list_profiles(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    user_type: str | None = None,
    designation: str | None = None,
) -> tuple[list[Profile], int]:
    stmt = select(Profile)
    count_stmt = select(func.count()).select_from(Profile)

    if user_type:
        stmt = stmt.where(Profile.user_type == user_type)
        count_stmt = count_stmt.where(Profile.user_type == user_type)
    if designation:
        stmt = stmt.where(Profile.designation == designation)
        count_stmt = count_stmt.where(Profile.designation == designation)

    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.offset((page - 1) * size).limit(size).order_by(Profile.diplay_name)
    result = await db.execute(stmt)
    return result.scalars().all(), total


async def get_profile(db: AsyncSession, profile_id: UUID) -> Profile:
    result = await db.execute(select(Profile).where(Profile.id == profile_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise NotFoundError("Profile not found")
    return profile
