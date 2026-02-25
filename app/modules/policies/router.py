from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import log_event
from app.core.pagination import PaginatedResponse, paginate_metadata
from app.database import get_db
from app.dependencies import require_perm
from app.modules.policies import service
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
    items, total = await service.list_policies(db, page, size, category, department, is_active)
    return {**paginate_metadata(total, page, size), "items": items}


@router.get("/{policy_id}", response_model=PolicyOut)
async def api_get_policy(
    policy_id: UUID,
    current_user: User = Depends(require_perm("policies", "read")),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_policy(db, policy_id)


@router.post("/", response_model=PolicyOut, status_code=201)
async def api_create_policy(
    data: PolicyCreate,
    current_user: User = Depends(require_perm("policies", "create")),
    db: AsyncSession = Depends(get_db),
):
    policy = await service.create_policy(db, data)
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
    policy = await service.update_policy(db, policy_id, data)
    await log_event(db, "policy.updated", current_user.id, "policy", policy.id, data.model_dump(exclude_unset=True))
    await db.commit()
    await db.refresh(policy)
    return policy
