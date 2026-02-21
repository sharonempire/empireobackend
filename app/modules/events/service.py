from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.modules.events.models import Event


class EventService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(self, event_type: str, actor_type: str, actor_id: UUID | None,
                  entity_type: str, entity_id: UUID, metadata: dict | None = None) -> Event:
        event = Event(
            event_type=event_type, actor_type=actor_type, actor_id=actor_id,
            entity_type=entity_type, entity_id=entity_id, metadata_=metadata,
        )
        self.db.add(event)
        await self.db.flush()
        return event

    async def get_timeline(self, entity_type: str, entity_id: UUID, limit=50, offset=0):
        result = await self.db.execute(
            select(Event)
            .where(Event.entity_type == entity_type, Event.entity_id == entity_id)
            .order_by(Event.created_at.desc()).limit(limit).offset(offset)
        )
        return result.scalars().all()

    async def get_by_type(self, event_type: str, limit=50):
        result = await self.db.execute(
            select(Event).where(Event.event_type == event_type)
            .order_by(Event.created_at.desc()).limit(limit)
        )
        return result.scalars().all()
