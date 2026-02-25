"""Workflows service layer."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.workflows.models import WorkflowDefinition, WorkflowInstance


async def list_definitions(db: AsyncSession) -> list[WorkflowDefinition]:
    result = await db.execute(
        select(WorkflowDefinition)
        .where(WorkflowDefinition.is_active == True)  # noqa: E712
        .order_by(WorkflowDefinition.name)
    )
    return result.scalars().all()


async def list_instances(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    entity_type: str | None = None,
    entity_id: UUID | None = None,
) -> tuple[list[WorkflowInstance], int]:
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
    return result.scalars().all(), total
