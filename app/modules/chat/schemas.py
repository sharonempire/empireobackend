from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ChatConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    counselor_id: Optional[str] = None
    lead_uuid: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_message_at: Optional[datetime] = None
    last_message_id: Optional[str] = None
    last_message_text: Optional[str] = None
    unread_count_assigned: Optional[int] = None
    unread_count_user: Optional[int] = None


class ChatMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: Optional[UUID] = None
    sender_id: Optional[str] = None
    message: Optional[str] = None
    message_type: Optional[str] = None
    created_at: Optional[datetime] = None
    voice_duration: Optional[int] = None
    course_id: Optional[str] = None
    course_deatails: Optional[Any] = None  # typo preserved from DB
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    file_url: Optional[str] = None
    is_read: Optional[bool] = None
    message_text: Optional[str] = None
    read_at: Optional[datetime] = None
    receiver_id: Optional[str] = None


class ChatMessageCreate(BaseModel):
    conversation_id: UUID
    sender_id: str
    message: str
    message_type: str = "text"
    voice_duration: Optional[int] = None
    course_id: Optional[str] = None
    course_deatails: Optional[Any] = None
