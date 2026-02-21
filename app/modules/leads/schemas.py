from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, List


class LeadInfoOut(BaseModel):
    id: UUID
    basic_info: Optional[dict] = None
    education: Optional[dict] = None
    work_experience: Optional[dict] = None
    budget_info: Optional[dict] = None
    preferences: Optional[dict] = None
    english_proficiency: Optional[dict] = None
    model_config = {"from_attributes": True}


class LeadOut(BaseModel):
    id: UUID
    sl_no: int
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    source: Optional[str] = None
    status: str
    lead_tab: str
    heat_status: Optional[str] = None
    assigned_to: Optional[UUID] = None
    country_preference: Optional[List[str]] = None
    remark: Optional[str] = None
    follow_up: Optional[str] = None
    ai_score: Optional[float] = None
    fresh: bool
    lead_info: Optional[LeadInfoOut] = None
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class LeadCreate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    source: Optional[str] = None
    lead_tab: str = "student"
    assigned_to: Optional[UUID] = None
    country_preference: Optional[List[str]] = None
    remark: Optional[str] = None


class LeadUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None
    heat_status: Optional[str] = None
    assigned_to: Optional[UUID] = None
    country_preference: Optional[List[str]] = None
    remark: Optional[str] = None
    follow_up: Optional[str] = None


class LeadInfoUpdate(BaseModel):
    basic_info: Optional[dict] = None
    education: Optional[dict] = None
    work_experience: Optional[dict] = None
    budget_info: Optional[dict] = None
    preferences: Optional[dict] = None
    english_proficiency: Optional[dict] = None
