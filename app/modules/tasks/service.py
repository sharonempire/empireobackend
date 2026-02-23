from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.tasks.models import Task
from app.modules.tasks.schemas import TaskCreate, TaskUpdate


async def list_tasks(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    assigned_to: UUID | None = None,
    status: str | None = None,
    entity_type: str | None = None,
    entity_id: UUID | None = None,
) -> tuple[list[Task], int]:
    stmt = select(Task)
    count_stmt = select(func.count()).select_from(Task)

    if assigned_to:
        stmt = stmt.where(Task.assigned_to == assigned_to)
        count_stmt = count_stmt.where(Task.assigned_to == assigned_to)
    if status:
        stmt = stmt.where(Task.status == status)
        count_stmt = count_stmt.where(Task.status == status)
    if entity_type:
        stmt = stmt.where(Task.entity_type == entity_type)
        count_stmt = count_stmt.where(Task.entity_type == entity_type)
    if entity_id:
        stmt = stmt.where(Task.entity_id == entity_id)
        count_stmt = count_stmt.where(Task.entity_id == entity_id)

    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.offset((page - 1) * size).limit(size).order_by(Task.due_at.asc().nullslast(), Task.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all(), total


async def get_task(db: AsyncSession, task_id: UUID) -> Task:
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise NotFoundError("Task not found")
    return task


async def create_task(db: AsyncSession, data: TaskCreate, created_by: UUID) -> Task:
    task = Task(**data.model_dump(), created_by=created_by)
    db.add(task)
    await db.flush()
    return task


async def update_task(db: AsyncSession, task_id: UUID, data: TaskUpdate) -> Task:
    task = await get_task(db, task_id)
    update_data = data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(task, key, value)

    if "status" in update_data and update_data["status"] == "completed":
        task.completed_at = datetime.now(timezone.utc)

    await db.flush()
    return task
