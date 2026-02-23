from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class NotificationOut(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    message: str | None = None
    notification_type: str
    entity_type: str | None = None
    entity_id: UUID | None = None
    data: dict | None = None
    is_read: bool
    read_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
