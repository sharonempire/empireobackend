"""Courses service layer with hybrid search."""

from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.search_engine import hybrid_search
from app.modules.courses.models import AppliedCourse, Course


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


# ── Applied Courses ──────────────────────────────────────────────────


async def list_applied_courses_for_lead(
    db: AsyncSession,
    lead_id: int,
    page: int = 1,
    size: int = 50,
) -> tuple[list[AppliedCourse], int]:
    """Fetch courses applied by a lead. user_id in applied_courses is the lead id (as text)."""
    lead_id_str = str(lead_id)
    stmt = select(AppliedCourse).where(AppliedCourse.user_id == lead_id_str)
    count_stmt = select(func.count()).select_from(AppliedCourse).where(AppliedCourse.user_id == lead_id_str)

    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.order_by(AppliedCourse.created_at.desc()).offset((page - 1) * size).limit(size)
    result = await db.execute(stmt)
    return result.scalars().all(), total


async def get_applied_course(db: AsyncSession, applied_id: str) -> AppliedCourse:
    result = await db.execute(select(AppliedCourse).where(AppliedCourse.id == applied_id))
    item = result.scalar_one_or_none()
    if not item:
        raise NotFoundError("Applied course not found")
    return item


async def update_applied_course(
    db: AsyncSession, applied_id: str, data: dict
) -> AppliedCourse:
    item = await get_applied_course(db, applied_id)
    for key, value in data.items():
        if value is not None:
            setattr(item, key, value)
    item.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(item)
    return item


# ── Course CRUD + Approval ──────────────────────────────────────────


async def create_course(db: AsyncSession, data) -> Course:
    course = Course(**data.model_dump(exclude_unset=True))
    db.add(course)
    await db.flush()
    await db.refresh(course)
    return course


async def update_course(db: AsyncSession, course_id: int, data) -> Course:
    course = await get_course(db, course_id)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(course, key, value)
    await db.flush()
    await db.refresh(course)
    return course


async def bulk_import_courses(db: AsyncSession, items: list[dict]) -> int:
    count = 0
    for item in items:
        course = Course(**item)
        db.add(course)
        count += 1
    await db.flush()
    return count


async def list_pending_courses(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
) -> tuple[list[Course], int]:
    condition = or_(
        func.lower(func.coalesce(Course.approval_status, '')) == 'pending',
    )
    count_stmt = select(func.count()).select_from(Course).where(condition)
    total = (await db.execute(count_stmt)).scalar()

    stmt = (
        select(Course)
        .where(condition)
        .order_by(Course.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    result = await db.execute(stmt)
    return result.scalars().all(), total


async def approve_course(
    db: AsyncSession,
    course_id: int,
    status: str,
    approved_detail: str | None = None,
) -> Course:
    course = await get_course(db, course_id)
    course.approval_status = status
    if approved_detail:
        course.approved_detail = approved_detail
    await db.flush()
    await db.refresh(course)
    return course
