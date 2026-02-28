from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import log_event
from app.core.pagination import PaginatedResponse, paginate_metadata
from app.database import get_db
from app.dependencies import get_current_user, require_perm
from app.modules.courses import service
from app.modules.courses.schemas import (
    AppliedCourseOut,
    AppliedCourseUpdate,
    CourseApprovalReview,
    CourseApprovalRequestOut,
    CourseCreate,
    CourseOut,
    CourseUpdate,
)
from app.modules.users.models import User

router = APIRouter(prefix="/courses", tags=["Courses"])


@router.get("/", response_model=PaginatedResponse[CourseOut])
async def api_list_courses(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=500),
    country: str | None = None,
    countries: str | None = Query(None, description="Comma-separated country names"),
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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_courses(
        db, page, size,
        country=country,
        countries=countries,
        program_level=program_level,
        program_name=program_name,
        city=city,
        university=university,
        campus=campus,
        study_type=study_type,
        language=language,
        intake=intake,
        currency=currency,
        field_of_study=field_of_study,
    )
    return {**paginate_metadata(total, page, size), "items": items}


@router.get("/search")
async def api_search_courses(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Hybrid search: full-text (TSVECTOR) + trigram fuzzy + ILIKE, ranked by relevance."""
    items, total = await service.search_courses(db, q, page, size)
    return {**paginate_metadata(total, page, size), "items": items}


@router.get("/eligible/{lead_id}")
async def api_eligible_courses(
    lead_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Find courses a student is eligible for based on their profile."""
    items, total = await service.search_eligible_courses(db, lead_id, page, size)
    return {**paginate_metadata(total, page, size), "items": items}


@router.post("/", response_model=CourseOut, status_code=201)
async def api_create_course(
    data: CourseCreate,
    current_user: User = Depends(require_perm("courses", "update")),
    db: AsyncSession = Depends(get_db),
):
    course = await service.create_course(db, data)
    await log_event(db, "course.created", current_user.id, "course", str(course.id), {"program_name": course.program_name})
    await db.commit()
    return course


@router.post("/import", status_code=201)
async def api_import_courses(
    items: list[dict],
    current_user: User = Depends(require_perm("courses", "update")),
    db: AsyncSession = Depends(get_db),
):
    count = await service.bulk_import_courses(db, items)
    await log_event(db, "course.imported", current_user.id, "course", None, {"count": count})
    await db.commit()
    return {"imported": count}


@router.get("/pending", response_model=PaginatedResponse[CourseOut])
async def api_list_pending_courses(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_pending_courses(db, page, size)
    return {**paginate_metadata(total, page, size), "items": items}


@router.get("/{course_id}", response_model=CourseOut)
async def api_get_course(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_course(db, course_id)


# ── Update Course (PATCH + PUT) ──────────────────────────────────────


async def _update_course(course_id: int, data: CourseUpdate, current_user: User, db: AsyncSession):
    course = await service.update_course(db, course_id, data)
    await log_event(db, "course.updated", current_user.id, "course", str(course.id), data.model_dump(exclude_unset=True))
    await db.commit()
    return course


@router.patch("/{course_id}", response_model=CourseOut)
async def api_update_course(
    course_id: int,
    data: CourseUpdate,
    current_user: User = Depends(require_perm("courses", "update")),
    db: AsyncSession = Depends(get_db),
):
    return await _update_course(course_id, data, current_user, db)


@router.put("/{course_id}", response_model=CourseOut)
async def api_update_course_put(
    course_id: int,
    data: CourseUpdate,
    current_user: User = Depends(require_perm("courses", "update")),
    db: AsyncSession = Depends(get_db),
):
    """PUT alias for PATCH course update."""
    return await _update_course(course_id, data, current_user, db)


# ── Approve Course (PATCH + POST) ────────────────────────────────────


async def _approve_course(course_id: int, data: CourseApprovalReview, current_user: User, db: AsyncSession):
    """Handle course approval. Accepts {status, approved_detail} or {approver_name, approver_id}."""
    status = data.status or "approved"
    approved_detail = data.approved_detail
    if data.approver_name or data.approver_id:
        approved_detail = approved_detail or f"{data.approver_name or ''} ({data.approver_id or ''})"
    course = await service.approve_course(db, course_id, status, approved_detail)
    await log_event(db, "course.approval_reviewed", current_user.id, "course", str(course.id), {"status": status})
    await db.commit()
    return course


@router.patch("/{course_id}/approve", response_model=CourseOut)
async def api_approve_course(
    course_id: int,
    data: CourseApprovalReview,
    current_user: User = Depends(require_perm("courses", "update")),
    db: AsyncSession = Depends(get_db),
):
    return await _approve_course(course_id, data, current_user, db)


@router.post("/{course_id}/approve", response_model=CourseOut)
async def api_approve_course_post(
    course_id: int,
    data: CourseApprovalReview,
    current_user: User = Depends(require_perm("courses", "update")),
    db: AsyncSession = Depends(get_db),
):
    """POST alias for course approval."""
    return await _approve_course(course_id, data, current_user, db)


# ── Course Approval Requests ─────────────────────────────────────────


@router.get("/approval-requests", response_model=PaginatedResponse[CourseApprovalRequestOut])
async def api_list_approval_requests(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=500),
    status: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List course approval requests."""
    items, total = await service.list_approval_requests(db, page, size, status)
    return {**paginate_metadata(total, page, size), "items": items}


@router.post("/approval-requests", response_model=CourseApprovalRequestOut, status_code=201)
async def api_create_approval_request(
    data: dict,
    current_user: User = Depends(require_perm("courses", "update")),
    db: AsyncSession = Depends(get_db),
):
    """Submit a course approval request."""
    item = await service.create_approval_request(db, data, current_user)
    await log_event(db, "course_approval.requested", current_user.id, "course_approval_request", str(item.id), {})
    await db.commit()
    return item


@router.post("/approval-requests/{request_id}/approve", response_model=CourseApprovalRequestOut)
async def api_approve_approval_request(
    request_id: int,
    data: dict | None = None,
    current_user: User = Depends(require_perm("courses", "update")),
    db: AsyncSession = Depends(get_db),
):
    """Approve or reject a course approval request."""
    item = await service.review_approval_request(db, request_id, data or {}, current_user)
    await log_event(db, "course_approval.reviewed", current_user.id, "course_approval_request", str(item.id), {"status": item.status})
    await db.commit()
    return item


# ── Applied Courses (PATCH + PUT) ────────────────────────────────────


async def _update_applied_course(applied_id: str, data: AppliedCourseUpdate, current_user: User, db: AsyncSession):
    item = await service.update_applied_course(db, applied_id, data.model_dump(exclude_unset=True))
    await log_event(db, "applied_course.updated", current_user.id, "applied_course", applied_id, data.model_dump(exclude_unset=True))
    await db.commit()
    return item


@router.patch("/applied/{applied_id}", response_model=AppliedCourseOut)
async def api_update_applied_course(
    applied_id: str,
    data: AppliedCourseUpdate,
    current_user: User = Depends(require_perm("courses", "update")),
    db: AsyncSession = Depends(get_db),
):
    """Update a course application (status, course_details)."""
    return await _update_applied_course(applied_id, data, current_user, db)


@router.put("/applied/{applied_id}", response_model=AppliedCourseOut)
async def api_update_applied_course_put(
    applied_id: str,
    data: AppliedCourseUpdate,
    current_user: User = Depends(require_perm("courses", "update")),
    db: AsyncSession = Depends(get_db),
):
    """PUT alias for applied course update."""
    return await _update_applied_course(applied_id, data, current_user, db)
