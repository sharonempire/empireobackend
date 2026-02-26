from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.events.models import Event


async def log_event(
    db: AsyncSession,
    event_type: str,
    actor_id: UUID | None,
    entity_type: str,
    entity_id: str | None = None,
    metadata: dict | None = None,
    actor_type: str = "user",
) -> Event:
    event = Event(
        event_type=event_type,
        actor_type=actor_type,
        actor_id=actor_id,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        event_metadata=metadata or {},
    )
    db.add(event)
    await db.flush()
    return event
