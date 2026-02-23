from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class JobProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_name: Optional[str] = None
    email_address: Optional[str] = None
    profile_id: Optional[str] = None
    status: Optional[str] = None
    company_website: Optional[str] = None
    company_address: Optional[str] = None


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: Optional[datetime] = None
    job_information: Optional[Any] = None
    location_salary_details: Optional[Any] = None
    job_details: Optional[Any] = None
    required_qualification: Optional[Any] = None
    status: Optional[str] = None
    job_profile_id: Optional[int] = None
    application_status: Optional[str] = None


class AppliedJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: Optional[int] = None
    user_id: Optional[int] = None
    status: Optional[str] = None
    applied_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    candidate_name: Optional[str] = None
    job_title: Optional[str] = None
