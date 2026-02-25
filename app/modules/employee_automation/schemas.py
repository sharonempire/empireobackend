from datetime import date, datetime, time
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# --------------- File Ingestion ---------------

class FileIngestionOut(BaseModel):
    id: UUID
    file_name: str
    file_key: str
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    source_type: str
    processing_status: str
    processing_error: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[UUID] = None
    employee_id: Optional[UUID] = None
    uploaded_by: Optional[UUID] = None
    extracted_data: Any = {}
    ai_model_used: Optional[str] = None
    ai_tokens_used: Optional[int] = None
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    tags: Optional[list[str]] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class FileIngestionCreate(BaseModel):
    file_name: str
    file_key: str
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    source_type: str = "upload"
    entity_type: Optional[str] = None
    entity_id: Optional[UUID] = None
    employee_id: Optional[UUID] = None
    tags: Optional[list[str]] = []


# --------------- Call Analysis ---------------

class CallAnalysisOut(BaseModel):
    id: UUID
    call_event_id: Optional[int] = None
    call_uuid: Optional[str] = None
    employee_id: Optional[UUID] = None
    recording_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    transcription: Optional[str] = None
    transcription_status: str
    transcription_model: Optional[str] = None
    sentiment_score: Optional[float] = None
    quality_score: Optional[float] = None
    professionalism_score: Optional[float] = None
    resolution_score: Optional[float] = None
    summary: Optional[str] = None
    topics: Any = []
    action_items: Any = []
    flags: Any = []
    key_phrases: Any = []
    caller_intent: Optional[str] = None
    outcome: Optional[str] = None
    language_detected: Optional[str] = None
    ai_model_used: Optional[str] = None
    ai_tokens_used: Optional[int] = None
    analyzed_at: Optional[datetime] = None
    file_ingestion_id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CallAnalysisCreate(BaseModel):
    call_event_id: Optional[int] = None
    call_uuid: Optional[str] = None
    employee_id: Optional[UUID] = None
    recording_url: Optional[str] = None
    duration_seconds: Optional[int] = None


# --------------- Employee Metric ---------------

class EmployeeMetricOut(BaseModel):
    id: UUID
    employee_id: UUID
    period_type: str
    period_start: date
    period_end: date
    calls_made: Optional[int] = 0
    calls_received: Optional[int] = 0
    calls_missed: Optional[int] = 0
    total_call_duration_mins: Optional[float] = 0
    avg_call_duration_mins: Optional[float] = 0
    avg_call_quality_score: Optional[float] = None
    avg_call_sentiment: Optional[float] = None
    leads_contacted: Optional[int] = 0
    leads_converted: Optional[int] = 0
    new_students_onboarded: Optional[int] = 0
    cases_progressed: Optional[int] = 0
    cases_closed: Optional[int] = 0
    applications_submitted: Optional[int] = 0
    documents_processed: Optional[int] = 0
    documents_verified: Optional[int] = 0
    days_present: Optional[int] = 0
    days_absent: Optional[int] = 0
    days_late: Optional[int] = 0
    avg_checkin_time: Optional[time] = None
    avg_checkout_time: Optional[time] = None
    total_hours_worked: Optional[float] = 0
    tasks_completed: Optional[int] = 0
    tasks_overdue: Optional[int] = 0
    avg_task_completion_hours: Optional[float] = None
    ai_performance_score: Optional[float] = None
    ai_efficiency_score: Optional[float] = None
    ai_quality_score: Optional[float] = None
    raw_data: Any = {}
    computed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# --------------- Performance Review ---------------

class PerformanceReviewOut(BaseModel):
    id: UUID
    employee_id: UUID
    reviewer_id: Optional[UUID] = None
    review_type: str
    period_start: date
    period_end: date
    scores: Any = {}
    overall_score: Optional[float] = None
    ai_summary: Optional[str] = None
    ai_strengths: Any = []
    ai_improvements: Any = []
    ai_recommendations: Any = []
    ai_comparison: Any = {}
    metrics_snapshot: Any = {}
    call_analysis_ids: Optional[list[UUID]] = None
    file_ingestion_ids: Optional[list[UUID]] = None
    status: str
    submitted_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    employee_feedback: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PerformanceReviewCreate(BaseModel):
    employee_id: UUID
    review_type: str = "monthly"
    period_start: date
    period_end: date
    scores: Any = {}
    overall_score: Optional[float] = None


class PerformanceReviewUpdate(BaseModel):
    scores: Optional[Any] = None
    overall_score: Optional[float] = None
    status: Optional[str] = None
    employee_feedback: Optional[str] = None


# --------------- Employee Goal ---------------

class EmployeeGoalOut(BaseModel):
    id: UUID
    employee_id: UUID
    title: str
    description: Optional[str] = None
    goal_type: str
    target_value: float
    current_value: Optional[float] = 0
    unit: Optional[str] = "count"
    period_start: date
    period_end: date
    status: str
    progress_percentage: Optional[float] = 0
    auto_track: Optional[bool] = True
    tracking_query: Any = None
    created_by: Optional[UUID] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class EmployeeGoalCreate(BaseModel):
    employee_id: UUID
    title: str
    description: Optional[str] = None
    goal_type: str
    target_value: float
    unit: str = "count"
    period_start: date
    period_end: date
    auto_track: bool = True
    tracking_query: Any = None


class EmployeeGoalUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    target_value: Optional[float] = None
    current_value: Optional[float] = None
    status: Optional[str] = None


# --------------- Work Log ---------------

class WorkLogOut(BaseModel):
    id: UUID
    employee_id: UUID
    activity_type: str
    entity_type: Optional[str] = None
    entity_id: Optional[UUID] = None
    description: Optional[str] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_minutes: Optional[float] = None
    source: str
    metadata: Any = Field(default={}, validation_alias="meta")
    event_id: Optional[UUID] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class WorkLogCreate(BaseModel):
    employee_id: UUID
    activity_type: str
    entity_type: Optional[str] = None
    entity_id: Optional[UUID] = None
    description: Optional[str] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_minutes: Optional[float] = None
    source: str = "manual"


# --------------- Employee Pattern ---------------

class EmployeePatternOut(BaseModel):
    id: UUID
    employee_id: UUID
    pattern_type: str
    pattern_data: Any
    summary: Optional[str] = None
    confidence_score: Optional[float] = None
    sample_size: Optional[int] = None
    detected_at: Optional[datetime] = None
    valid_from: Optional[date] = None
    valid_until: Optional[date] = None
    is_active: Optional[bool] = True
    ai_model_used: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# --------------- Employee Schedule ---------------

class EmployeeScheduleOut(BaseModel):
    id: UUID
    employee_id: UUID
    schedule_type: str
    day_of_week: Optional[int] = None
    specific_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    break_minutes: Optional[int] = 60
    is_working_day: Optional[bool] = True
    leave_type: Optional[str] = None
    leave_reason: Optional[str] = None
    approved_by: Optional[UUID] = None
    status: Optional[str] = "active"
    effective_from: date
    effective_until: Optional[date] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class EmployeeScheduleCreate(BaseModel):
    employee_id: UUID
    schedule_type: str = "regular"
    day_of_week: Optional[int] = None
    specific_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    break_minutes: int = 60
    is_working_day: bool = True
    leave_type: Optional[str] = None
    leave_reason: Optional[str] = None
    effective_from: date
    effective_until: Optional[date] = None
    notes: Optional[str] = None


class EmployeeScheduleUpdate(BaseModel):
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    break_minutes: Optional[int] = None
    is_working_day: Optional[bool] = None
    leave_type: Optional[str] = None
    leave_reason: Optional[str] = None
    status: Optional[str] = None
    effective_until: Optional[date] = None
    notes: Optional[str] = None


# --------------- Training Record ---------------

class TrainingRecordOut(BaseModel):
    id: UUID
    employee_id: UUID
    title: str
    training_type: str
    description: Optional[str] = None
    provider: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str
    score: Optional[float] = None
    max_score: Optional[float] = None
    certificate_url: Optional[str] = None
    expiry_date: Optional[date] = None
    assigned_by: Optional[UUID] = None
    metadata: Any = Field(default={}, validation_alias="meta")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TrainingRecordCreate(BaseModel):
    employee_id: UUID
    title: str
    training_type: str
    description: Optional[str] = None
    provider: Optional[str] = None
    started_at: Optional[datetime] = None
    expiry_date: Optional[date] = None


class TrainingRecordUpdate(BaseModel):
    status: Optional[str] = None
    score: Optional[float] = None
    max_score: Optional[float] = None
    completed_at: Optional[datetime] = None
    certificate_url: Optional[str] = None
