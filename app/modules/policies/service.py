"""Policies service layer."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.policies.models import Policy
from app.modules.policies.schemas import PolicyCreate, PolicyUpdate


async def list_policies(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    category: str | None = None,
    department: str | None = None,
    is_active: bool | None = None,
) -> tuple[list[Policy], int]:
    stmt = select(Policy)
    count_stmt = select(func.count()).select_from(Policy)

    if category:
        stmt = stmt.where(Policy.category == category)
        count_stmt = count_stmt.where(Policy.category == category)
    if department:
        stmt = stmt.where(Policy.department == department)
        count_stmt = count_stmt.where(Policy.department == department)
    if is_active is not None:
        stmt = stmt.where(Policy.is_active == is_active)
        count_stmt = count_stmt.where(Policy.is_active == is_active)

    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.offset((page - 1) * size).limit(size).order_by(Policy.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all(), total


async def get_policy(db: AsyncSession, policy_id: UUID) -> Policy:
    result = await db.execute(select(Policy).where(Policy.id == policy_id))
    policy = result.scalar_one_or_none()
    if not policy:
        raise NotFoundError("Policy not found")
    return policy


async def create_policy(db: AsyncSession, data: PolicyCreate) -> Policy:
    policy = Policy(**data.model_dump())
    policy.created_at = datetime.now(timezone.utc)
    db.add(policy)
    await db.flush()
    return policy


async def update_policy(db: AsyncSession, policy_id: UUID, data: PolicyUpdate) -> Policy:
    policy = await get_policy(db, policy_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(policy, field, value)
    policy.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return policy
