from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class ChatConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    counselor_id: Optional[str] = None
    lead_uuid: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ChatMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_id: Optional[int] = None
    sender_id: Optional[str] = None
    message: Optional[str] = None
    message_type: Optional[str] = None
    created_at: Optional[datetime] = None
    voice_duration: Optional[int] = None
    course_id: Optional[str] = None
    course_deatails: Optional[Any] = None  # typo preserved from DB


class ChatMessageCreate(BaseModel):
    conversation_id: int
    sender_id: str
    message: str
    message_type: str = "text"
    voice_duration: Optional[int] = None
    course_id: Optional[str] = None
    course_deatails: Optional[Any] = None
