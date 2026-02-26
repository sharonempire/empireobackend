from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import PaginatedResponse, paginate_metadata
from app.database import get_db
from app.dependencies import require_perm
from app.modules.users.models import User
from app.modules.workflows import service
from app.modules.workflows.schemas import WorkflowDefinitionOut, WorkflowInstanceOut

router = APIRouter(prefix="/workflows", tags=["Workflows"])


@router.get("/definitions", response_model=list[WorkflowDefinitionOut])
async def api_list_definitions(
    current_user: User = Depends(require_perm("workflows", "read")),
    db: AsyncSession = Depends(get_db),
):
    return await service.list_definitions(db)


@router.get("/instances", response_model=PaginatedResponse[WorkflowInstanceOut])
async def api_list_instances(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=500),
    entity_type: str | None = None,
    entity_id: UUID | None = None,
    current_user: User = Depends(require_perm("workflows", "read")),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_instances(db, page, size, entity_type, entity_id)
    return {**paginate_metadata(total, page, size), "items": items}
