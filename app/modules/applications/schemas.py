from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel


class ApplicationOut(BaseModel):
    id: UUID
    case_id: UUID
    university_name: str
    university_country: str | None = None
    program_name: str
    program_level: str | None = None
    status: str
    submitted_at: datetime | None = None
    response_received_at: datetime | None = None
    offer_deadline: date | None = None
    offer_details: dict | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ApplicationCreate(BaseModel):
    case_id: UUID
    university_name: str
    university_country: str | None = None
    program_name: str
    program_level: str | None = None
    status: str = "draft"
    notes: str | None = None


class ApplicationUpdate(BaseModel):
    status: str | None = None
    submitted_at: datetime | None = None
    response_received_at: datetime | None = None
    offer_deadline: date | None = None
    offer_details: dict | None = None
    notes: str | None = None
