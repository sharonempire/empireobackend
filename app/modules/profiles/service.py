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


async def list_counselors_with_attendance(db: AsyncSession) -> list[dict]:
    """List counselors (profiles with user_type=counselor) with today's attendance status."""
    from sqlalchemy import text

    sql = text("""
        SELECT p.id, p.diplay_name, p.profilepicture, p.email, p.phone,
               p.designation, p.countries, p.fcm_token,
               a.checkinat, a.checkoutat
        FROM profiles p
        LEFT JOIN attendance a ON a.employee_id = p.id
            AND a.date = to_char(NOW() AT TIME ZONE 'Asia/Kolkata', 'YYYY-MM-DD')
        WHERE p.user_type IN ('counselor', 'Counselor')
           OR p.designation ILIKE '%counselor%'
        ORDER BY p.diplay_name
    """)
    result = await db.execute(sql)
    rows = []
    for row in result.all():
        d = dict(row._mapping)
        d["is_checked_in"] = d.get("checkinat") is not None and d.get("checkoutat") is None
        rows.append(d)
    return rows


async def batch_get_profiles(
    db: AsyncSession, profile_ids: list[UUID]
) -> list[Profile]:
    """Batch fetch profiles by IDs."""
    if not profile_ids:
        return []
    result = await db.execute(
        select(Profile).where(Profile.id.in_(profile_ids))
    )
    return result.scalars().all()


async def get_profile_fcm_token(db: AsyncSession, profile_id: UUID) -> str | None:
    result = await db.execute(
        select(Profile.fcm_token).where(Profile.id == profile_id)
    )
    return result.scalar_one_or_none()
