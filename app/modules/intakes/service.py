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


async def create_intake(db: AsyncSession, data) -> Intake:
    intake = Intake(**data.model_dump(exclude_unset=True))
    db.add(intake)
    await db.flush()
    await db.refresh(intake)
    return intake


async def update_intake(db: AsyncSession, intake_id: int, data) -> Intake:
    intake = await get_intake(db, intake_id)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(intake, key, value)
    await db.flush()
    await db.refresh(intake)
    return intake
