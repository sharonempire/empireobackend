from uuid import UUID
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.events import log_event
from app.core.pagination import PaginatedResponse, paginate_metadata
from app.database import get_db
from app.dependencies import require_perm
from app.modules.policies.models import Policy
from app.modules.policies.schemas import PolicyCreate, PolicyOut, PolicyUpdate
from app.modules.users.models import User

router = APIRouter(prefix="/policies", tags=["Policies"])


@router.get("/", response_model=PaginatedResponse[PolicyOut])
async def api_list_policies(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    category: str | None = None,
    department: str | None = None,
    is_active: bool | None = None,
    current_user: User = Depends(require_perm("policies", "read")),
    db: AsyncSession = Depends(get_db),
):
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
    return {**paginate_metadata(total, page, size), "items": result.scalars().all()}


@router.get("/{policy_id}", response_model=PolicyOut)
async def api_get_policy(
    policy_id: UUID,
    current_user: User = Depends(require_perm("policies", "read")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Policy).where(Policy.id == policy_id))
    policy = result.scalar_one_or_none()
    if not policy:
        raise NotFoundError("Policy not found")
    return policy


@router.post("/", response_model=PolicyOut, status_code=201)
async def api_create_policy(
    data: PolicyCreate,
    current_user: User = Depends(require_perm("policies", "create")),
    db: AsyncSession = Depends(get_db),
):
    policy = Policy(**data.model_dump())
    db.add(policy)
    await db.flush()
    await log_event(db, "policy.created", current_user.id, "policy", policy.id, {"title": policy.title})
    await db.commit()
    await db.refresh(policy)
    return policy


@router.patch("/{policy_id}", response_model=PolicyOut)
async def api_update_policy(
    policy_id: UUID,
    data: PolicyUpdate,
    current_user: User = Depends(require_perm("policies", "update")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Policy).where(Policy.id == policy_id))
    policy = result.scalar_one_or_none()
    if not policy:
        raise NotFoundError("Policy not found")

    updates = data.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(policy, field, value)
    policy.updated_at = datetime.now(timezone.utc)

    await db.flush()
    await log_event(db, "policy.updated", current_user.id, "policy", policy.id, updates)
    await db.commit()
    await db.refresh(policy)
    return policy
