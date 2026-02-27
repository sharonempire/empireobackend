"""Freelance module service layer."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.freelance.models import AgentEndpoint, Commission, Freelancer, FreelanceManager
from app.modules.freelance.schemas import FreelancerCreate, FreelancerUpdate, FreelanceManagerCreate, FreelanceManagerUpdate, CommissionCreate


async def list_commissions(db: AsyncSession) -> list[Commission]:
    result = await db.execute(select(Commission).order_by(Commission.id))
    return result.scalars().all()


async def list_freelancers(
    db: AsyncSession, page: int = 1, size: int = 20
) -> tuple[list[Freelancer], int]:
    count_stmt = select(func.count()).select_from(Freelancer)
    total = (await db.execute(count_stmt)).scalar()
    stmt = select(Freelancer).offset((page - 1) * size).limit(size).order_by(Freelancer.id.desc())
    result = await db.execute(stmt)
    return result.scalars().all(), total


async def get_freelancer(db: AsyncSession, freelancer_id: int) -> Freelancer:
    result = await db.execute(select(Freelancer).where(Freelancer.id == freelancer_id))
    item = result.scalar_one_or_none()
    if not item:
        raise NotFoundError("Freelancer not found")
    return item


async def batch_get_freelancers(db: AsyncSession, ids: list[int]) -> list[Freelancer]:
    if not ids:
        return []
    result = await db.execute(select(Freelancer).where(Freelancer.id.in_(ids)))
    return result.scalars().all()


async def create_freelancer(db: AsyncSession, data: FreelancerCreate, creator_id: UUID) -> Freelancer:
    item = Freelancer(**data.model_dump(), creator_id=creator_id)
    db.add(item)
    await db.flush()
    return item


async def update_freelancer(db: AsyncSession, freelancer_id: int, data: FreelancerUpdate) -> Freelancer:
    item = await get_freelancer(db, freelancer_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    await db.flush()
    return item


async def list_managers(
    db: AsyncSession, page: int = 1, size: int = 20
) -> tuple[list[FreelanceManager], int]:
    count_stmt = select(func.count()).select_from(FreelanceManager)
    total = (await db.execute(count_stmt)).scalar()
    stmt = select(FreelanceManager).offset((page - 1) * size).limit(size).order_by(FreelanceManager.id.desc())
    result = await db.execute(stmt)
    return result.scalars().all(), total


async def get_manager(db: AsyncSession, manager_id: int) -> FreelanceManager:
    result = await db.execute(select(FreelanceManager).where(FreelanceManager.id == manager_id))
    item = result.scalar_one_or_none()
    if not item:
        raise NotFoundError("Freelance manager not found")
    return item


async def batch_get_managers(db: AsyncSession, ids: list[int]) -> list[FreelanceManager]:
    if not ids:
        return []
    result = await db.execute(select(FreelanceManager).where(FreelanceManager.id.in_(ids)))
    return result.scalars().all()


async def create_manager(db: AsyncSession, data: FreelanceManagerCreate) -> FreelanceManager:
    item = FreelanceManager(**data.model_dump())
    db.add(item)
    await db.flush()
    return item


async def update_manager(db: AsyncSession, manager_id: int, data: FreelanceManagerUpdate) -> FreelanceManager:
    item = await get_manager(db, manager_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    await db.flush()
    return item


async def list_agent_endpoints(db: AsyncSession) -> list[AgentEndpoint]:
    result = await db.execute(select(AgentEndpoint).order_by(AgentEndpoint.agent_key))
    return result.scalars().all()
