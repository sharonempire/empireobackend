"""Courses service layer."""

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.courses.models import Course


async def list_courses(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    country: str | None = None,
    program_level: str | None = None,
) -> tuple[list[Course], int]:
    stmt = select(Course)
    count_stmt = select(func.count()).select_from(Course)

    if country:
        stmt = stmt.where(Course.country == country)
        count_stmt = count_stmt.where(Course.country == country)
    if program_level:
        stmt = stmt.where(Course.program_level == program_level)
        count_stmt = count_stmt.where(Course.program_level == program_level)

    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.offset((page - 1) * size).limit(size).order_by(Course.program_name)
    result = await db.execute(stmt)
    return result.scalars().all(), total


async def search_courses(
    db: AsyncSession,
    q: str,
    page: int = 1,
    size: int = 20,
) -> tuple[list[Course], int]:
    pattern = f"%{q}%"
    condition = or_(
        Course.program_name.ilike(pattern),
        Course.university.ilike(pattern),
        Course.country.ilike(pattern),
    )
    stmt = select(Course).where(condition)
    count_stmt = select(func.count()).select_from(Course).where(condition)

    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.offset((page - 1) * size).limit(size).order_by(Course.program_name)
    result = await db.execute(stmt)
    return result.scalars().all(), total


async def get_course(db: AsyncSession, course_id: int) -> Course:
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise NotFoundError("Course not found")
    return course
