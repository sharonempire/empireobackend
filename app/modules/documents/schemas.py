from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: UUID
    entity_type: str
    entity_id: UUID
    document_type: str | None = None
    file_name: str
    file_key: str
    file_size_bytes: int | None = None
    mime_type: str | None = None
    uploaded_by: UUID | None = None
    is_verified: bool
    verified_by: UUID | None = None
    verified_at: datetime | None = None
    notes: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentCreate(BaseModel):
    entity_type: str
    entity_id: UUID
    document_type: str | None = None
    file_name: str
    file_key: str
    file_size_bytes: int | None = None
    mime_type: str | None = None
    notes: str | None = None
