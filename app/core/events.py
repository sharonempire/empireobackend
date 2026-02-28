from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.events.models import Event


async def log_event(
    db: AsyncSession,
    event_type: str,
    actor_id: UUID | None,
    entity_type: str,
    entity_id: str | UUID | None = None,
    metadata: dict | None = None,
    actor_type: str = "user",
) -> Event:
    # Ensure entity_id is a UUID (Supabase column is UUID type)
    # Non-UUID values (e.g. "bulk") are stored as None — use metadata for context
    _entity_id = None
    if entity_id is not None:
        if isinstance(entity_id, UUID):
            _entity_id = entity_id
        else:
            try:
                _entity_id = UUID(str(entity_id))
            except ValueError:
                _entity_id = None

    event = Event(
        event_type=event_type,
        actor_type=actor_type,
        actor_id=actor_id,
        entity_type=entity_type,
        entity_id=_entity_id,
        event_metadata=metadata or {},
    )
    db.add(event)
    await db.flush()
    return event
