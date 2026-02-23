from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.pagination import PaginatedResponse, paginate_metadata
from app.database import get_db
from app.dependencies import get_current_user
from app.modules.call_events.models import CallEvent
from app.modules.call_events.schemas import CallEventOut
from app.modules.users.models import User

router = APIRouter(prefix="/call-events", tags=["Call Events"])


@router.get("/", response_model=PaginatedResponse[CallEventOut])
async def api_list_call_events(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    event_type: str | None = None,
    call_uuid: str | None = None,
    agent_number: str | None = None,
    call_date: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(CallEvent)
    count_stmt = select(func.count()).select_from(CallEvent)

    if event_type:
        stmt = stmt.where(CallEvent.event_type == event_type)
        count_stmt = count_stmt.where(CallEvent.event_type == event_type)
    if call_uuid:
        stmt = stmt.where(CallEvent.call_uuid == call_uuid)
        count_stmt = count_stmt.where(CallEvent.call_uuid == call_uuid)
    if agent_number:
        stmt = stmt.where(CallEvent.agent_number == agent_number)
        count_stmt = count_stmt.where(CallEvent.agent_number == agent_number)
    if call_date:
        stmt = stmt.where(CallEvent.call_date == call_date)
        count_stmt = count_stmt.where(CallEvent.call_date == call_date)

    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.offset((page - 1) * size).limit(size).order_by(CallEvent.id.desc())
    result = await db.execute(stmt)
    return {**paginate_metadata(total, page, size), "items": result.scalars().all()}


@router.get("/{call_event_id}", response_model=CallEventOut)
async def api_get_call_event(
    call_event_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(CallEvent).where(CallEvent.id == call_event_id))
    call_event = result.scalar_one_or_none()
    if not call_event:
        raise NotFoundError("Call event not found")
    return call_event
