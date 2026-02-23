from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import PaginatedResponse, paginate
from app.database import get_db
from app.dependencies import get_current_user
from app.modules.events.models import Event
from app.modules.events.schemas import EventOut
from app.modules.users.models import User

router = APIRouter(prefix="/events", tags=["Events"])


@router.get("/", response_model=PaginatedResponse[EventOut])
async def api_list_events(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    entity_type: str | None = None,
    entity_id: UUID | None = None,
    event_type: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Event)
    count_stmt = select(func.count()).select_from(Event)

    if entity_type:
        stmt = stmt.where(Event.entity_type == entity_type)
        count_stmt = count_stmt.where(Event.entity_type == entity_type)
    if entity_id:
        stmt = stmt.where(Event.entity_id == entity_id)
        count_stmt = count_stmt.where(Event.entity_id == entity_id)
    if event_type:
        stmt = stmt.where(Event.event_type == event_type)
        count_stmt = count_stmt.where(Event.event_type == event_type)

    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.offset((page - 1) * size).limit(size).order_by(Event.created_at.desc())
    result = await db.execute(stmt)
    return {**paginate(total, page, size), "items": result.scalars().all()}
