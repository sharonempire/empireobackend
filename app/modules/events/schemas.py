from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


class EventOut(BaseModel):
    id: UUID
    event_type: str
    actor_type: str
    actor_id: Optional[UUID] = None
    entity_type: str
    entity_id: UUID
    metadata_: Optional[dict] = None
    created_at: datetime
    model_config = {"from_attributes": True}
