from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class EventOut(BaseModel):
    id: UUID
    event_type: str
    actor_type: str | None = None
    actor_id: UUID | None = None
    entity_type: str
    entity_id: UUID
    event_metadata: dict = {}
    created_at: datetime

    model_config = {"from_attributes": True}
