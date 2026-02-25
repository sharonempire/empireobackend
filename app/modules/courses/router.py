from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import PaginatedResponse, paginate_metadata
from app.database import get_db
from app.dependencies import require_perm
from app.modules.courses import service
from app.modules.courses.schemas import CourseOut
from app.modules.users.models import User

router = APIRouter(prefix="/courses", tags=["Courses"])


@router.get("/", response_model=PaginatedResponse[CourseOut])
async def api_list_courses(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
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
    size: int = Query(20, ge=1, le=100),
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
    size: int = Query(20, ge=1, le=100),
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


@router.get("/{course_id}", response_model=CourseOut)
async def api_get_course(
    course_id: int,
    current_user: User = Depends(require_perm("courses", "read")),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_course(db, course_id)
