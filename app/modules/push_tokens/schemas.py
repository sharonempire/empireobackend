from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserPushTokenOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    user_id: UUID
    fcm_token: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class UserPushTokenCreate(BaseModel):
    user_id: UUID
    fcm_token: str


class UserFCMTokenOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    user_id: UUID
    fcm_token: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class UserFCMTokenCreate(BaseModel):
    user_id: UUID
    fcm_token: str
