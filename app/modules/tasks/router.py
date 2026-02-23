from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import log_event
from app.core.pagination import PaginatedResponse, paginate_metadata
from app.database import get_db
from app.dependencies import get_current_user, require_perm
from app.modules.tasks.schemas import TaskCreate, TaskOut, TaskUpdate
from app.modules.tasks.service import create_task, get_task, list_tasks, update_task
from app.modules.users.models import User

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("/", response_model=PaginatedResponse[TaskOut])
async def api_list_tasks(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    assigned_to: UUID | None = None,
    status: str | None = None,
    entity_type: str | None = None,
    entity_id: UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tasks, total = await list_tasks(db, page, size, assigned_to, status, entity_type, entity_id)
    return {**paginate_metadata(total, page, size), "items": tasks}


@router.get("/my", response_model=PaginatedResponse[TaskOut])
async def api_my_tasks(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tasks, total = await list_tasks(db, page, size, assigned_to=current_user.id, status=status)
    return {**paginate_metadata(total, page, size), "items": tasks}


@router.get("/{task_id}", response_model=TaskOut)
async def api_get_task(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_task(db, task_id)


@router.post("/", response_model=TaskOut, status_code=201)
async def api_create_task(
    data: TaskCreate,
    current_user: User = Depends(require_perm("tasks", "create")),
    db: AsyncSession = Depends(get_db),
):
    task = await create_task(db, data, current_user.id)
    await log_event(db, "task.created", current_user.id, "task", task.id, {"title": task.title})
    await db.commit()
    return task


@router.patch("/{task_id}", response_model=TaskOut)
async def api_update_task(
    task_id: UUID,
    data: TaskUpdate,
    current_user: User = Depends(require_perm("tasks", "update")),
    db: AsyncSession = Depends(get_db),
):
    task = await update_task(db, task_id, data)
    await log_event(db, "task.updated", current_user.id, "task", task.id, data.model_dump(exclude_unset=True))
    await db.commit()
    return task
