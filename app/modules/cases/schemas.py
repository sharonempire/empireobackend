from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CaseOut(BaseModel):
    id: UUID
    student_id: UUID | None = None
    case_type: str
    current_stage: str
    priority: str
    assigned_counselor_id: UUID | None = None
    assigned_processor_id: UUID | None = None
    assigned_visa_officer_id: UUID | None = None
    target_intake: str | None = None
    notes: str | None = None
    is_active: bool
    closed_at: datetime | None = None
    close_reason: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CaseCreate(BaseModel):
    student_id: UUID
    case_type: str = "study_abroad"
    current_stage: str = "initial_consultation"
    priority: str = "normal"
    assigned_counselor_id: UUID | None = None
    assigned_processor_id: UUID | None = None
    assigned_visa_officer_id: UUID | None = None
    target_intake: str | None = None
    notes: str | None = None


class CaseUpdate(BaseModel):
    current_stage: str | None = None
    priority: str | None = None
    assigned_counselor_id: UUID | None = None
    assigned_processor_id: UUID | None = None
    assigned_visa_officer_id: UUID | None = None
    target_intake: str | None = None
    notes: str | None = None
    is_active: bool | None = None
    close_reason: str | None = None
