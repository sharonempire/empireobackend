"""Courses service layer with hybrid search."""

from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.search_engine import hybrid_search
from app.modules.courses.models import AppliedCourse, Course, CourseApprovalRequest


async def list_courses(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    country: str | None = None,
    countries: str | None = None,
    program_level: str | None = None,
    program_name: str | None = None,
    city: str | None = None,
    university: str | None = None,
    campus: str | None = None,
    study_type: str | None = None,
    language: str | None = None,
    intake: str | None = None,
    currency: str | None = None,
    field_of_study: str | None = None,
) -> tuple[list[Course], int]:
    stmt = select(Course)
    count_stmt = select(func.count()).select_from(Course)

    # Single country or comma-separated countries list
    if countries:
        country_list = [c.strip() for c in countries.split(",") if c.strip()]
        if country_list:
            stmt = stmt.where(Course.country.in_(country_list))
            count_stmt = count_stmt.where(Course.country.in_(country_list))
    elif country:
        stmt = stmt.where(Course.country == country)
        count_stmt = count_stmt.where(Course.country == country)

    if program_level:
        stmt = stmt.where(Course.program_level == program_level)
        count_stmt = count_stmt.where(Course.program_level == program_level)
    if program_name:
        stmt = stmt.where(Course.program_name.ilike(f"%{program_name}%"))
        count_stmt = count_stmt.where(Course.program_name.ilike(f"%{program_name}%"))
    if city:
        stmt = stmt.where(Course.city == city)
        count_stmt = count_stmt.where(Course.city == city)
    if university:
        stmt = stmt.where(Course.university.ilike(f"%{university}%"))
        count_stmt = count_stmt.where(Course.university.ilike(f"%{university}%"))
    if campus:
        stmt = stmt.where(Course.campus == campus)
        count_stmt = count_stmt.where(Course.campus == campus)
    if study_type:
        stmt = stmt.where(Course.study_type == study_type)
        count_stmt = count_stmt.where(Course.study_type == study_type)
    if language:
        stmt = stmt.where(Course.language == language)
        count_stmt = count_stmt.where(Course.language == language)
    if currency:
        stmt = stmt.where(Course.currency == currency)
        count_stmt = count_stmt.where(Course.currency == currency)
    if field_of_study:
        stmt = stmt.where(Course.field_of_study.ilike(f"%{field_of_study}%"))
        count_stmt = count_stmt.where(Course.field_of_study.ilike(f"%{field_of_study}%"))
    if intake:
        # intakes is a JSONB column — use cast to text for ILIKE search
        from sqlalchemy import cast, Text
        stmt = stmt.where(cast(Course.intakes, Text).ilike(f"%{intake}%"))
        count_stmt = count_stmt.where(cast(Course.intakes, Text).ilike(f"%{intake}%"))

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
    """
    from sqlalchemy import text

    count_sql = text("SELECT COUNT(*) FROM search_eligible_courses(:lead_id)")
    count_result = await db.execute(count_sql, {"lead_id": lead_id})
    total = count_result.scalar() or 0

    if total == 0:
        return [], 0

    offset = (page - 1) * size
    sql = text("SELECT * FROM search_eligible_courses(:lead_id) LIMIT :limit OFFSET :offset")
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


# ── Course Approval Requests ────────────────────────────────────────


async def list_approval_requests(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    status: str | None = None,
) -> tuple[list[CourseApprovalRequest], int]:
    stmt = select(CourseApprovalRequest)
    count_stmt = select(func.count()).select_from(CourseApprovalRequest)

    if status:
        stmt = stmt.where(CourseApprovalRequest.status == status)
        count_stmt = count_stmt.where(CourseApprovalRequest.status == status)

    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.order_by(CourseApprovalRequest.created_at.desc()).offset((page - 1) * size).limit(size)
    result = await db.execute(stmt)
    return result.scalars().all(), total


async def create_approval_request(db: AsyncSession, data: dict, current_user) -> CourseApprovalRequest:
    item = CourseApprovalRequest(
        status="pending",
        payload=data.get("payload", data),
        submitted_by=data.get("submitted_by", current_user.full_name),
        submitted_designation=data.get("submitted_designation"),
    )
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return item


async def review_approval_request(
    db: AsyncSession,
    request_id: int,
    data: dict,
    current_user,
) -> CourseApprovalRequest:
    result = await db.execute(
        select(CourseApprovalRequest).where(CourseApprovalRequest.id == request_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise NotFoundError("Course approval request not found")

    item.status = data.get("status", "approved")
    item.approved_by = data.get("approved_by", current_user.full_name)
    item.approved_at = datetime.now(timezone.utc)
    if data.get("approved_course_id"):
        item.approved_course_id = data["approved_course_id"]
    await db.flush()
    await db.refresh(item)
    return item
