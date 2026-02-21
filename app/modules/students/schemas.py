from pydantic import BaseModel
from uuid import UUID
from datetime import datetime, date
from typing import Optional


class StudentOut(BaseModel):
    id: UUID
    lead_id: UUID
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    education_level: Optional[str] = None
    preferred_countries: Optional[list] = None
    assigned_counselor_id: Optional[UUID] = None
    created_at: datetime
    model_config = {"from_attributes": True}


class StudentCreate(BaseModel):
    lead_id: UUID
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    nationality: Optional[str] = None
    education_level: Optional[str] = None
    preferred_countries: Optional[list] = None
