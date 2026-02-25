"""Call events service layer."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.call_events.models import CallEvent


async def list_call_events(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    event_type: str | None = None,
    call_uuid: str | None = None,
    agent_number: str | None = None,
    call_date: str | None = None,
) -> tuple[list[CallEvent], int]:
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
    return result.scalars().all(), total


async def get_call_event(db: AsyncSession, call_event_id: int) -> CallEvent:
    result = await db.execute(select(CallEvent).where(CallEvent.id == call_event_id))
    call_event = result.scalar_one_or_none()
    if not call_event:
        raise NotFoundError("Call event not found")
    return call_event
