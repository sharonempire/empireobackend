from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class CourseOut(BaseModel):
    id: int
    created_at: datetime | None = None
    program_name: str | None = None
    university: str | None = None
    country: str | None = None
    city: str | None = None
    campus: str | None = None
    application_fee: str | None = None
    tuition_fee: str | None = None
    deposit_amount: str | None = None
    currency: str | None = None
    duration: str | None = None
    language: str | None = None
    study_type: str | None = None
    program_level: str | None = None
    english_proficiency: str | None = None
    minimum_percentage: str | None = None
    age_limit: str | None = None
    academic_gap: str | None = None
    max_backlogs: str | None = None
    work_experience_requirement: str | None = None
    required_subjects: dict | list | None = None
    intakes: dict | list | None = None
    links: dict | list | None = None
    media_links: dict | list | None = None
    course_description: str | None = None
    special_requirements: str | None = None
    field_of_study: str | None = None
    commission: dict | list | None = None
    domain: str | None = None
    keywords: list[str] | None = None
    application_status: str | None = None
    approval_status: str | None = None
    approved_detail: dict | None = None
    insertion_details: dict | None = None
    # Normalized fields
    program_level_normalized: str | None = None
    age_limit_num: int | None = None
    academic_gap_num: int | None = None
    max_backlogs_num: int | None = None
    min_pct_num: Decimal | None = None
    domain_tags: list[str] | None = None
    field_of_study_ai: str | None = None
    english_proficiency_normalized_v2: dict | None = None
    required_subjects_normalized: dict | None = None

    model_config = {"from_attributes": True}


class CourseSummaryOut(BaseModel):
    """Lightweight course listing without AI/processing fields."""
    id: int
    program_name: str | None = None
    university: str | None = None
    country: str | None = None
    city: str | None = None
    campus: str | None = None
    program_level: str | None = None
    tuition_fee: str | None = None
    currency: str | None = None
    duration: str | None = None
    field_of_study: str | None = None
    application_status: str | None = None
    approval_status: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class UniversityCourseOut(CourseOut):
    source_key: str | None = None
    university_image: str | None = None
    tuition_fee_international_amount: Decimal | None = None
    tuition_fee_international_currency: str | None = None
    tuition_fee_international_basis: str | None = None
    tuition_fee_international_raw: str | None = None


class CourseApprovalRequestOut(BaseModel):
    id: int
    created_at: datetime | None = None
    status: str | None = None
    payload: dict | None = None
    submitted_by: str | None = None
    submitted_designation: str | None = None
    approved_by: str | None = None
    approved_at: datetime | None = None
    approved_course_id: str | None = None

    model_config = {"from_attributes": True}


class SavedCourseOut(BaseModel):
    id: int
    created_at: datetime | None = None
    user_id: int | None = None
    course_id: int | None = None
    course_details: dict | None = None

    model_config = {"from_attributes": True}


class AppliedCourseOut(BaseModel):
    id: str
    user_id: str
    course_id: str
    course_details: dict
    status: str
    applied_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class AppliedCourseUpdate(BaseModel):
    status: str | None = None
    course_details: dict | None = None
