from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import PaginatedResponse, paginate_metadata
from app.database import get_db
from app.dependencies import require_perm
from app.modules.jobs import service
from app.modules.jobs.schemas import AppliedJobOut, JobOut, JobProfileOut
from app.modules.users.models import User

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get("/profiles", response_model=PaginatedResponse[JobProfileOut])
async def api_list_job_profiles(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_perm("jobs", "read")),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_job_profiles(db, page, size)
    return {**paginate_metadata(total, page, size), "items": items}


@router.get("/", response_model=PaginatedResponse[JobOut])
async def api_list_jobs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    current_user: User = Depends(require_perm("jobs", "read")),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_jobs(db, page, size, status)
    return {**paginate_metadata(total, page, size), "items": items}


@router.get("/{job_id}", response_model=JobOut)
async def api_get_job(
    job_id: int,
    current_user: User = Depends(require_perm("jobs", "read")),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_job(db, job_id)


@router.get("/applied/list", response_model=PaginatedResponse[AppliedJobOut])
async def api_list_applied_jobs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user_id: str | None = None,
    current_user: User = Depends(require_perm("jobs", "read")),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_applied_jobs(db, page, size, user_id)
    return {**paginate_metadata(total, page, size), "items": items}
