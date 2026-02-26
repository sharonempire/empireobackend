from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import PaginatedResponse, paginate_metadata
from app.database import get_db
from app.dependencies import require_perm
from app.modules.courses import service
from app.core.events import log_event
from app.modules.courses.schemas import (
    AppliedCourseOut,
    AppliedCourseUpdate,
    CourseApprovalReview,
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
    program_level: str | None = None,
    current_user: User = Depends(require_perm("courses", "read")),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_courses(db, page, size, country, program_level)
    return {**paginate_metadata(total, page, size), "items": items}


@router.get("/search")
async def api_search_courses(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=500),
    current_user: User = Depends(require_perm("courses", "read")),
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
    current_user: User = Depends(require_perm("courses", "read")),
    db: AsyncSession = Depends(get_db),
):
    """Find courses a student is eligible for based on their profile.

    Uses the DB function `search_eligible_courses` which matches
    education level, percentage, backlogs, English proficiency,
    budget, country preference, and domain tags against the full catalog.
    """
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
    current_user: User = Depends(require_perm("courses", "read")),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_pending_courses(db, page, size)
    return {**paginate_metadata(total, page, size), "items": items}


@router.get("/{course_id}", response_model=CourseOut)
async def api_get_course(
    course_id: int,
    current_user: User = Depends(require_perm("courses", "read")),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_course(db, course_id)


@router.patch("/{course_id}", response_model=CourseOut)
async def api_update_course(
    course_id: int,
    data: CourseUpdate,
    current_user: User = Depends(require_perm("courses", "update")),
    db: AsyncSession = Depends(get_db),
):
    course = await service.update_course(db, course_id, data)
    await log_event(db, "course.updated", current_user.id, "course", str(course.id), data.model_dump(exclude_unset=True))
    await db.commit()
    return course


@router.patch("/{course_id}/approve", response_model=CourseOut)
async def api_approve_course(
    course_id: int,
    data: CourseApprovalReview,
    current_user: User = Depends(require_perm("courses", "update")),
    db: AsyncSession = Depends(get_db),
):
    course = await service.approve_course(db, course_id, data.status, data.approved_detail)
    await log_event(db, "course.approval_reviewed", current_user.id, "course", str(course.id), {"status": data.status})
    await db.commit()
    return course


# ── Applied Courses ──────────────────────────────────────────────────


@router.patch("/applied/{applied_id}", response_model=AppliedCourseOut)
async def api_update_applied_course(
    applied_id: str,
    data: AppliedCourseUpdate,
    current_user: User = Depends(require_perm("courses", "update")),
    db: AsyncSession = Depends(get_db),
):
    """Update a course application (status, course_details)."""
    item = await service.update_applied_course(db, applied_id, data.model_dump(exclude_unset=True))
    await log_event(db, "applied_course.updated", current_user.id, "applied_course", applied_id, data.model_dump(exclude_unset=True))
    await db.commit()
    return item
