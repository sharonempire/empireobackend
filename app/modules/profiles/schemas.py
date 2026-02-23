from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    diplay_name: Optional[str] = None  # typo preserved from DB
    profilepicture: Optional[str] = None
    user_type: Optional[str] = None
    phone: Optional[int] = None
    designation: Optional[str] = None
    freelancer_status: Optional[str] = None
    location: Optional[str] = None
    email: Optional[str] = None
    callerId: Optional[str] = None
    countries: Optional[list[str]] = None
    fcm_token: Optional[str] = None
    user_id: Optional[str] = None
