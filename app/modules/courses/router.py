from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.pagination import PaginatedResponse, paginate_metadata
from app.database import get_db
from app.dependencies import get_current_user
from app.modules.courses.models import Course
from app.modules.courses.schemas import CourseOut
from app.modules.users.models import User

router = APIRouter(prefix="/courses", tags=["Courses"])


@router.get("/", response_model=PaginatedResponse[CourseOut])
async def api_list_courses(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    country: str | None = None,
    program_level: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
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
    return {**paginate_metadata(total, page, size), "items": result.scalars().all()}


@router.get("/search", response_model=PaginatedResponse[CourseOut])
async def api_search_courses(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pattern = f"%{q}%"
    condition = or_(Course.program_name.ilike(pattern), Course.university.ilike(pattern), Course.country.ilike(pattern))

    stmt = select(Course).where(condition)
    count_stmt = select(func.count()).select_from(Course).where(condition)

    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.offset((page - 1) * size).limit(size).order_by(Course.program_name)
    result = await db.execute(stmt)
    return {**paginate_metadata(total, page, size), "items": result.scalars().all()}


@router.get("/{course_id}", response_model=CourseOut)
async def api_get_course(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise NotFoundError("Course not found")
    return course
