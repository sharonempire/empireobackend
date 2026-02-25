from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ShortLinkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    code: str
    target_url: str
    created_at: datetime | None = None


class ShortLinkCreate(BaseModel):
    code: str
    target_url: str


class ChatbotSessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    session_id: str
    last_intent: str | None = None
    last_country: str | None = None
    last_field: str | None = None
    updated_at: datetime | None = None
