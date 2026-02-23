from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.pagination import PaginatedResponse, paginate_metadata
from app.database import get_db
from app.dependencies import get_current_user
from app.modules.jobs.models import AppliedJob, Job, JobProfile
from app.modules.jobs.schemas import AppliedJobOut, JobOut, JobProfileOut
from app.modules.users.models import User

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get("/profiles", response_model=PaginatedResponse[JobProfileOut])
async def api_list_job_profiles(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(JobProfile)
    count_stmt = select(func.count()).select_from(JobProfile)
    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.offset((page - 1) * size).limit(size)
    result = await db.execute(stmt)
    return {**paginate_metadata(total, page, size), "items": result.scalars().all()}


@router.get("/", response_model=PaginatedResponse[JobOut])
async def api_list_jobs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Job)
    count_stmt = select(func.count()).select_from(Job)

    if status:
        stmt = stmt.where(Job.status == status)
        count_stmt = count_stmt.where(Job.status == status)

    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.offset((page - 1) * size).limit(size).order_by(Job.id.desc())
    result = await db.execute(stmt)
    return {**paginate_metadata(total, page, size), "items": result.scalars().all()}


@router.get("/{job_id}", response_model=JobOut)
async def api_get_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise NotFoundError("Job not found")
    return job


@router.get("/applied/list", response_model=PaginatedResponse[AppliedJobOut])
async def api_list_applied_jobs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user_id: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(AppliedJob)
    count_stmt = select(func.count()).select_from(AppliedJob)

    if user_id:
        stmt = stmt.where(AppliedJob.user_id == user_id)
        count_stmt = count_stmt.where(AppliedJob.user_id == user_id)

    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.offset((page - 1) * size).limit(size).order_by(AppliedJob.id.desc())
    result = await db.execute(stmt)
    return {**paginate_metadata(total, page, size), "items": result.scalars().all()}
