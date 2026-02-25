"""Intakes service layer."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.intakes.models import Intake


async def list_intakes(
    db: AsyncSession, page: int = 1, size: int = 20
) -> tuple[list[Intake], int]:
    count_stmt = select(func.count()).select_from(Intake)
    total = (await db.execute(count_stmt)).scalar()
    stmt = select(Intake).offset((page - 1) * size).limit(size).order_by(Intake.start_date.desc())
    result = await db.execute(stmt)
    return result.scalars().all(), total


async def get_intake(db: AsyncSession, intake_id: int) -> Intake:
    result = await db.execute(select(Intake).where(Intake.id == intake_id))
    intake = result.scalar_one_or_none()
    if not intake:
        raise NotFoundError("Intake not found")
    return intake
