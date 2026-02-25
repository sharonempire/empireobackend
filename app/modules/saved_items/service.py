"""Saved items service layer (read-only legacy)."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.saved_items.models import SavedJob


async def list_saved_jobs(
    db: AsyncSession, page: int = 1, size: int = 20, user_id: int | None = None
) -> tuple[list[SavedJob], int]:
    stmt = select(SavedJob)
    count_stmt = select(func.count()).select_from(SavedJob)
    if user_id:
        stmt = stmt.where(SavedJob.user_id == user_id)
        count_stmt = count_stmt.where(SavedJob.user_id == user_id)
    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.offset((page - 1) * size).limit(size).order_by(SavedJob.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all(), total
