from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class LeadInfoOut(BaseModel):
    id: int
    created_at: datetime | None = None
    basic_info: dict | None = None
    education: dict | None = None
    work_expierience: dict | list | None = None  # Note: typo matches DB
    budget_info: dict | None = None
    preferences: dict | None = None
    english_proficiency: dict | None = None
    call_info: dict | list | None = None
    changes_history: dict | list | None = None
    updated_at: datetime | None = None
    documents: dict | None = None
    domain_tags: list[str] | None = None
    profile_text: str | None = None
    needs_enrichment: bool | None = None
    enrichment_updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class LeadOut(BaseModel):
    id: int
    sl_no: int | None = None
    created_at: datetime | None = None
    name: str | None = None
    email: str | None = None
    phone: int | None = None
    phone_norm: str | None = None
    freelancer_manager: str | None = None
    freelancer: str | None = None
    source: str | None = None
    status: str | None = None
    heat_status: str | None = None
    follow_up: str | None = None
    remark: str | None = None
    assigned_to: UUID | None = None
    draft_status: str | None = None
    date: datetime | None = None
    info_progress: str | None = None
    call_summary: str | None = None
    lead_tab: str | None = None
    lead_type: str | None = None
    changes_history: list | dict | None = None
    documents_status: str | None = None
    fresh: bool | None = None
    profile_image: str | None = None
    is_premium_jobs: bool | None = None
    is_premium_courses: bool | None = None
    is_resume_downloaded: bool | None = None
    country_preference: list[str] | None = None
    is_registered: bool | None = None
    user_id: str | None = None
    fcm_token: str | None = None
    finder_type: str | None = None
    current_module: str | None = None
    preferences_completed: bool | None = None
    profile_completion: int | None = None
    ig_handle: str | None = None

    model_config = {"from_attributes": True}


class LeadSummaryOut(BaseModel):
    """Lightweight listing without all fields."""
    id: int
    name: str | None = None
    email: str | None = None
    phone: int | None = None
    source: str | None = None
    status: str | None = None
    heat_status: str | None = None
    lead_tab: str | None = None
    assigned_to: UUID | None = None
    fresh: bool | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class LeadDetailOut(LeadOut):
    lead_info: LeadInfoOut | None = None


# ── Write Schemas ────────────────────────────────────────────────────


class LeadCreate(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: int | None = None
    source: str | None = None
    status: str | None = "Lead creation"
    follow_up: str | None = None
    remark: str | None = None
    heat_status: str | None = None
    lead_tab: str | None = "student"
    country_preference: list[str] | None = None
    freelancer_manager: str | None = None
    freelancer: str | None = None
    lead_type: str | None = None
    finder_type: str | None = None


class LeadUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: int | None = None
    source: str | None = None
    status: str | None = None
    follow_up: str | None = None
    remark: str | None = None
    assigned_to: UUID | None = None
    heat_status: str | None = None
    lead_tab: str | None = None
    country_preference: list[str] | None = None
    lead_type: str | None = None
    documents_status: str | None = None
    call_summary: str | None = None
    info_progress: str | None = None
    draft_status: str | None = None
    fresh: bool | None = None
    profile_image: str | None = None
    is_premium_jobs: bool | None = None
    is_premium_courses: bool | None = None
    is_resume_downloaded: bool | None = None
    is_registered: bool | None = None
    finder_type: str | None = None
    current_module: str | None = None
    ig_handle: str | None = None
    freelancer_manager: str | None = None
    freelancer: str | None = None


class LeadInfoCreate(BaseModel):
    """Create a lead_info record. The id matches lead_id (FK to leadslist)."""
    basic_info: dict | None = None
    education: dict | None = None
    work_expierience: dict | list | None = None  # typo matches DB
    budget_info: dict | None = None
    preferences: dict | None = None
    english_proficiency: dict | None = None
    call_info: dict | list | None = None
    changes_history: dict | list | None = None
    documents: dict | None = None
    domain_tags: list[str] | None = None
    profile_text: str | None = None


class LeadInfoUpdate(BaseModel):
    basic_info: dict | None = None
    education: dict | None = None
    work_expierience: dict | list | None = None  # typo matches DB
    budget_info: dict | None = None
    preferences: dict | None = None
    english_proficiency: dict | None = None
    call_info: dict | list | None = None
    documents: dict | None = None
    changes_history: dict | list | None = None
    domain_tags: list[str] | None = None
    profile_text: str | None = None


class LeadReassign(BaseModel):
    """Reassign a lead to a different counselor."""
    assigned_to: UUID


class LeadRedistribute(BaseModel):
    """Redistribute N leads from one counselor to others via round-robin."""
    source_counselor_id: UUID
    leads_to_move: int


class AssignmentTrackerOut(BaseModel):
    id: int
    last_assigned_employee: UUID | None = None

    model_config = {"from_attributes": True}


class LeadIntake(BaseModel):
    """Full lead intake pipeline request — mirrors eb-lead-intake Edge Function.
    Creates lead → lead_info → student → auto-assigns counselor → chat.
    """
    name: str
    email: str | None = None
    phone: int | None = None
    source: str | None = "website"
    country_preference: list[str] | None = None
    lead_tab: str | None = "student"
    basic_info: dict | None = None
    education: dict | None = None
    budget_info: dict | None = None
    preferences: dict | None = None
    english_proficiency: dict | None = None
    domain_tags: list[str] | None = None
