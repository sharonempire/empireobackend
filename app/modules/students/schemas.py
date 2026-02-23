from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel


class StudentOut(BaseModel):
    id: UUID
    lead_id: int | None = None
    full_name: str
    email: str | None = None
    phone: str | None = None
    date_of_birth: date | None = None
    nationality: str | None = None
    passport_number: str | None = None
    passport_expiry: date | None = None
    education_level: str | None = None
    education_details: dict | list | None = None
    english_test_type: str | None = None
    english_test_score: str | None = None
    work_experience_years: int = 0
    preferred_countries: list | None = None
    preferred_programs: list | None = None
    assigned_counselor_id: UUID | None = None
    assigned_processor_id: UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class StudentCreate(BaseModel):
    full_name: str
    email: str | None = None
    phone: str | None = None
    date_of_birth: date | None = None
    nationality: str | None = None
    passport_number: str | None = None
    passport_expiry: date | None = None
    education_level: str | None = None
    education_details: dict | list | None = None
    english_test_type: str | None = None
    english_test_score: str | None = None
    work_experience_years: int = 0
    preferred_countries: list | None = None
    preferred_programs: list | None = None
    assigned_counselor_id: UUID | None = None
    assigned_processor_id: UUID | None = None


class StudentUpdate(BaseModel):
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    date_of_birth: date | None = None
    nationality: str | None = None
    passport_number: str | None = None
    passport_expiry: date | None = None
    education_level: str | None = None
    education_details: dict | list | None = None
    english_test_type: str | None = None
    english_test_score: str | None = None
    work_experience_years: int | None = None
    preferred_countries: list | None = None
    preferred_programs: list | None = None
    assigned_counselor_id: UUID | None = None
    assigned_processor_id: UUID | None = None
