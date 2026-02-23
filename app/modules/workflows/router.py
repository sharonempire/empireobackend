from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import PaginatedResponse, paginate
from app.database import get_db
from app.dependencies import get_current_user
from app.modules.users.models import User
from app.modules.workflows.models import WorkflowDefinition, WorkflowInstance
from app.modules.workflows.schemas import WorkflowDefinitionOut, WorkflowInstanceOut

router = APIRouter(prefix="/workflows", tags=["Workflows"])


@router.get("/definitions", response_model=list[WorkflowDefinitionOut])
async def api_list_definitions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(WorkflowDefinition).where(WorkflowDefinition.is_active == True).order_by(WorkflowDefinition.name))
    return result.scalars().all()


@router.get("/instances", response_model=PaginatedResponse[WorkflowInstanceOut])
async def api_list_instances(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    entity_type: str | None = None,
    entity_id: UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(WorkflowInstance)
    count_stmt = select(func.count()).select_from(WorkflowInstance)

    if entity_type:
        stmt = stmt.where(WorkflowInstance.entity_type == entity_type)
        count_stmt = count_stmt.where(WorkflowInstance.entity_type == entity_type)
    if entity_id:
        stmt = stmt.where(WorkflowInstance.entity_id == entity_id)
        count_stmt = count_stmt.where(WorkflowInstance.entity_id == entity_id)

    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.offset((page - 1) * size).limit(size).order_by(WorkflowInstance.created_at.desc())
    result = await db.execute(stmt)
    return {**paginate(total, page, size), "items": result.scalars().all()}
