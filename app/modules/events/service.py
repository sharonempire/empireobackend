"""Events service layer (read-only audit log)."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.events.models import Event


async def list_events(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    entity_type: str | None = None,
    entity_id: UUID | None = None,
    event_type: str | None = None,
) -> tuple[list[Event], int]:
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
    return result.scalars().all(), total
