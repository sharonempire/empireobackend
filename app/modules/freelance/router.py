from pydantic import BaseModel
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import log_event
from app.core.pagination import PaginatedResponse, paginate_metadata
from app.database import get_db
from app.dependencies import get_current_user, require_perm
from app.modules.freelance import service
from app.modules.freelance.schemas import (
    AgentEndpointOut,
    CommissionOut,
    FreelancerCreate,
    FreelancerOut,
    FreelancerUpdate,
    FreelanceManagerCreate,
    FreelanceManagerOut,
    FreelanceManagerUpdate,
)
from app.modules.users.models import User

router = APIRouter(prefix="/freelance", tags=["Freelance"])


# ── Commissions ──────────────────────────────────────────────────────

@router.get("/commissions", response_model=list[CommissionOut])
async def api_list_commissions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await service.list_commissions(db)


# ── Freelancers ──────────────────────────────────────────────────────

@router.get("/freelancers", response_model=PaginatedResponse[FreelancerOut])
async def api_list_freelancers(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_freelancers(db, page, size)
    return {**paginate_metadata(total, page, size), "items": items}


@router.get("/freelancers/{freelancer_id}", response_model=FreelancerOut)
async def api_get_freelancer(
    freelancer_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_freelancer(db, freelancer_id)


class FreelancerBatchRequest(BaseModel):
    ids: list[int]


@router.post("/freelancers/batch", response_model=list[FreelancerOut])
async def api_batch_freelancers(
    data: FreelancerBatchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Batch fetch freelancers by IDs (max 100)."""
    if len(data.ids) > 100:
        from app.core.exceptions import BadRequestError
        raise BadRequestError("Maximum 100 IDs per batch request")
    return await service.batch_get_freelancers(db, data.ids)


@router.post("/freelancers", response_model=FreelancerOut, status_code=201)
async def api_create_freelancer(
    data: FreelancerCreate,
    current_user: User = Depends(require_perm("freelance", "create")),
    db: AsyncSession = Depends(get_db),
):
    item = await service.create_freelancer(db, data, current_user.id)
    await log_event(db, "freelancer.created", current_user.id, "freelancer", str(item.id), {"name": item.name})
    await db.commit()
    return item


@router.patch("/freelancers/{freelancer_id}", response_model=FreelancerOut)
async def api_update_freelancer(
    freelancer_id: int,
    data: FreelancerUpdate,
    current_user: User = Depends(require_perm("freelance", "update")),
    db: AsyncSession = Depends(get_db),
):
    item = await service.update_freelancer(db, freelancer_id, data)
    await log_event(db, "freelancer.updated", current_user.id, "freelancer", str(item.id), data.model_dump(exclude_unset=True))
    await db.commit()
    return item


# ── Freelance Managers ───────────────────────────────────────────────

@router.get("/managers", response_model=PaginatedResponse[FreelanceManagerOut])
async def api_list_managers(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_managers(db, page, size)
    return {**paginate_metadata(total, page, size), "items": items}


@router.get("/managers/{manager_id}", response_model=FreelanceManagerOut)
async def api_get_manager(
    manager_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_manager(db, manager_id)


class ManagerBatchRequest(BaseModel):
    ids: list[int]


@router.post("/managers/batch", response_model=list[FreelanceManagerOut])
async def api_batch_managers(
    data: ManagerBatchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Batch fetch freelance managers by IDs (max 100)."""
    if len(data.ids) > 100:
        from app.core.exceptions import BadRequestError
        raise BadRequestError("Maximum 100 IDs per batch request")
    return await service.batch_get_managers(db, data.ids)


@router.post("/managers", response_model=FreelanceManagerOut, status_code=201)
async def api_create_manager(
    data: FreelanceManagerCreate,
    current_user: User = Depends(require_perm("freelance", "create")),
    db: AsyncSession = Depends(get_db),
):
    item = await service.create_manager(db, data)
    await log_event(db, "freelance_manager.created", current_user.id, "freelance_manager", str(item.id), {"name": item.name})
    await db.commit()
    return item


@router.patch("/managers/{manager_id}", response_model=FreelanceManagerOut)
async def api_update_manager(
    manager_id: int,
    data: FreelanceManagerUpdate,
    current_user: User = Depends(require_perm("freelance", "update")),
    db: AsyncSession = Depends(get_db),
):
    item = await service.update_manager(db, manager_id, data)
    await log_event(db, "freelance_manager.updated", current_user.id, "freelance_manager", str(item.id), data.model_dump(exclude_unset=True))
    await db.commit()
    return item


# ── Agent Endpoints ──────────────────────────────────────────────────

@router.get("/agent-endpoints", response_model=list[AgentEndpointOut])
async def api_list_agent_endpoints(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await service.list_agent_endpoints(db)
