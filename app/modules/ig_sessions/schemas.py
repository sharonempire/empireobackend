from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ConversationSessionOut(BaseModel):
    id: UUID
    lead_id: int | None = None
    ig_user_id: str
    status: str
    messages: list = []
    extracted_data: dict = {}
    conversation_stage: str | None = None
    assigned_counsellor_id: UUID | None = None
    handoff_reason: str | None = None
    last_message_at: datetime | None = None
    message_count: int | None = None
    retry_count: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class DMTemplateOut(BaseModel):
    id: UUID
    trigger_type: str
    system_prompt: str
    opening_message: str
    qualification_fields: dict | list = {}
    is_active: bool | None = None
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
