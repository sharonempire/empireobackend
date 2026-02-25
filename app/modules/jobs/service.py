"""Jobs service layer."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.jobs.models import AppliedJob, Job, JobProfile


async def list_job_profiles(
    db: AsyncSession, page: int = 1, size: int = 20
) -> tuple[list[JobProfile], int]:
    count_stmt = select(func.count()).select_from(JobProfile)
    total = (await db.execute(count_stmt)).scalar()
    stmt = select(JobProfile).offset((page - 1) * size).limit(size)
    result = await db.execute(stmt)
    return result.scalars().all(), total


async def list_jobs(
    db: AsyncSession, page: int = 1, size: int = 20, status: str | None = None
) -> tuple[list[Job], int]:
    stmt = select(Job)
    count_stmt = select(func.count()).select_from(Job)
    if status:
        stmt = stmt.where(Job.status == status)
        count_stmt = count_stmt.where(Job.status == status)
    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.offset((page - 1) * size).limit(size).order_by(Job.id.desc())
    result = await db.execute(stmt)
    return result.scalars().all(), total


async def get_job(db: AsyncSession, job_id: int) -> Job:
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise NotFoundError("Job not found")
    return job


async def list_applied_jobs(
    db: AsyncSession, page: int = 1, size: int = 20, user_id: str | None = None
) -> tuple[list[AppliedJob], int]:
    stmt = select(AppliedJob)
    count_stmt = select(func.count()).select_from(AppliedJob)
    if user_id:
        stmt = stmt.where(AppliedJob.user_id == user_id)
        count_stmt = count_stmt.where(AppliedJob.user_id == user_id)
    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.offset((page - 1) * size).limit(size).order_by(AppliedJob.id.desc())
    result = await db.execute(stmt)
    return result.scalars().all(), total
