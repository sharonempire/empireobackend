"""Courses service layer with hybrid search."""

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.search_engine import hybrid_search
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
) -> tuple[list[dict], int]:
    """Hybrid search on courses — full-text (TSVECTOR) + trigram + ILIKE."""
    return await hybrid_search(
        db=db,
        table_name="courses",
        query=q,
        search_columns=["program_name", "university", "country"],
        tsvector_column="search_vector",
        page=page,
        size=size,
    )


async def get_course(db: AsyncSession, course_id: int) -> Course:
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise NotFoundError("Course not found")
    return course


async def search_eligible_courses(
    db: AsyncSession,
    lead_id: int,
    page: int = 1,
    size: int = 20,
) -> tuple[list[dict], int]:
    """Find courses a student is eligible for using the DB function
    `search_eligible_courses(p_lead_id)`.

    This massive DB function (21K chars) matches student profile
    (education level, percentage, backlogs, English proficiency, budget,
    country preference, domain tags) against the full course catalog
    with normalized eligibility filters.
    """
    from sqlalchemy import text

    # Count eligible courses
    count_sql = text("""
        SELECT COUNT(*) FROM search_eligible_courses(:lead_id)
    """)
    count_result = await db.execute(count_sql, {"lead_id": lead_id})
    total = count_result.scalar() or 0

    if total == 0:
        return [], 0

    # Fetch paginated eligible courses
    offset = (page - 1) * size
    sql = text("""
        SELECT * FROM search_eligible_courses(:lead_id)
        LIMIT :limit OFFSET :offset
    """)
    result = await db.execute(sql, {"lead_id": lead_id, "limit": size, "offset": offset})
    rows = [dict(row._mapping) for row in result.all()]

    return rows, total
