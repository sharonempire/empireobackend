import uuid

from sqlalchemy import BigInteger, Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, String, Text, Time
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID

from app.database import Base


class FileIngestion(Base):
    __tablename__ = "eb_file_ingestions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_name = Column(String, nullable=False)
    file_key = Column(String, nullable=False)
    file_size_bytes = Column(Integer, nullable=True)
    mime_type = Column(String, nullable=True)
    source_type = Column(String, nullable=False, default="upload")
    processing_status = Column(String, nullable=False, default="pending")
    processing_error = Column(Text, nullable=True)
    entity_type = Column(String, nullable=True)
    entity_id = Column(UUID(as_uuid=True), nullable=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("eb_users.id"), nullable=True)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("eb_users.id"), nullable=True)
    extracted_data = Column(JSONB, server_default="'{}'::jsonb")
    ai_model_used = Column(String, nullable=True)
    ai_tokens_used = Column(Integer, nullable=True)
    processing_started_at = Column(DateTime(timezone=True), nullable=True)
    processing_completed_at = Column(DateTime(timezone=True), nullable=True)
    tags = Column(ARRAY(Text), server_default="'[]'::jsonb")
    created_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)


class CallAnalysis(Base):
    __tablename__ = "eb_call_analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    call_event_id = Column(BigInteger, ForeignKey("call_events.id"), nullable=True)
    call_uuid = Column(Text, nullable=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("eb_users.id"), nullable=True)
    recording_url = Column(Text, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    transcription = Column(Text, nullable=True)
    transcription_status = Column(String, nullable=False, default="pending")
    transcription_model = Column(String, nullable=True)
    sentiment_score = Column(Float, nullable=True)
    quality_score = Column(Float, nullable=True)
    professionalism_score = Column(Float, nullable=True)
    resolution_score = Column(Float, nullable=True)
    summary = Column(Text, nullable=True)
    topics = Column(JSONB, server_default="'[]'::jsonb")
    action_items = Column(JSONB, server_default="'[]'::jsonb")
    flags = Column(JSONB, server_default="'[]'::jsonb")
    key_phrases = Column(JSONB, server_default="'[]'::jsonb")
    caller_intent = Column(String, nullable=True)
    outcome = Column(String, nullable=True)
    language_detected = Column(String, nullable=True)
    ai_model_used = Column(String, nullable=True)
    ai_tokens_used = Column(Integer, nullable=True)
    analyzed_at = Column(DateTime(timezone=True), nullable=True)
    file_ingestion_id = Column(UUID(as_uuid=True), ForeignKey("eb_file_ingestions.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)


class EmployeeMetric(Base):
    __tablename__ = "eb_employee_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("eb_users.id"), nullable=False)
    period_type = Column(String, nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    calls_made = Column(Integer, default=0)
    calls_received = Column(Integer, default=0)
    calls_missed = Column(Integer, default=0)
    total_call_duration_mins = Column(Float, default=0)
    avg_call_duration_mins = Column(Float, default=0)
    avg_call_quality_score = Column(Float, nullable=True)
    avg_call_sentiment = Column(Float, nullable=True)
    leads_contacted = Column(Integer, default=0)
    leads_converted = Column(Integer, default=0)
    new_students_onboarded = Column(Integer, default=0)
    cases_progressed = Column(Integer, default=0)
    cases_closed = Column(Integer, default=0)
    applications_submitted = Column(Integer, default=0)
    documents_processed = Column(Integer, default=0)
    documents_verified = Column(Integer, default=0)
    days_present = Column(Integer, default=0)
    days_absent = Column(Integer, default=0)
    days_late = Column(Integer, default=0)
    avg_checkin_time = Column(Time, nullable=True)
    avg_checkout_time = Column(Time, nullable=True)
    total_hours_worked = Column(Float, default=0)
    tasks_completed = Column(Integer, default=0)
    tasks_overdue = Column(Integer, default=0)
    avg_task_completion_hours = Column(Float, nullable=True)
    ai_performance_score = Column(Float, nullable=True)
    ai_efficiency_score = Column(Float, nullable=True)
    ai_quality_score = Column(Float, nullable=True)
    raw_data = Column(JSONB, server_default="'{}'::jsonb")
    computed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)


class PerformanceReview(Base):
    __tablename__ = "eb_performance_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("eb_users.id"), nullable=False)
    reviewer_id = Column(UUID(as_uuid=True), ForeignKey("eb_users.id"), nullable=True)
    review_type = Column(String, nullable=False, default="monthly")
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    scores = Column(JSONB, nullable=False, server_default="'{}'::jsonb")
    overall_score = Column(Float, nullable=True)
    ai_summary = Column(Text, nullable=True)
    ai_strengths = Column(JSONB, server_default="'[]'::jsonb")
    ai_improvements = Column(JSONB, server_default="'[]'::jsonb")
    ai_recommendations = Column(JSONB, server_default="'[]'::jsonb")
    ai_comparison = Column(JSONB, server_default="'{}'::jsonb")
    metrics_snapshot = Column(JSONB, server_default="'{}'::jsonb")
    call_analysis_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=True)
    file_ingestion_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=True)
    status = Column(String, nullable=False, default="draft")
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    employee_feedback = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)


class EmployeeGoal(Base):
    __tablename__ = "eb_employee_goals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("eb_users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    goal_type = Column(String, nullable=False)
    target_value = Column(Float, nullable=False)
    current_value = Column(Float, default=0)
    unit = Column(String, default="count")
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    status = Column(String, nullable=False, default="active")
    progress_percentage = Column(Float, default=0)
    auto_track = Column(Boolean, default=True)
    tracking_query = Column(JSONB, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("eb_users.id"), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)


class WorkLog(Base):
    __tablename__ = "eb_work_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("eb_users.id"), nullable=False)
    activity_type = Column(String, nullable=False)
    entity_type = Column(String, nullable=True)
    entity_id = Column(UUID(as_uuid=True), nullable=True)
    description = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    duration_minutes = Column(Float, nullable=True)
    source = Column(String, nullable=False, default="system")
    meta = Column("metadata", JSONB, server_default="'{}'::jsonb")
    event_id = Column(UUID(as_uuid=True), ForeignKey("eb_events.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)


class EmployeePattern(Base):
    __tablename__ = "eb_employee_patterns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("eb_users.id"), nullable=False)
    pattern_type = Column(String, nullable=False)
    pattern_data = Column(JSONB, nullable=False)
    summary = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True)
    sample_size = Column(Integer, nullable=True)
    detected_at = Column(DateTime(timezone=True), nullable=True)
    valid_from = Column(Date, nullable=True)
    valid_until = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)
    ai_model_used = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)


class EmployeeSchedule(Base):
    __tablename__ = "eb_employee_schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("eb_users.id"), nullable=False)
    schedule_type = Column(String, nullable=False, default="regular")
    day_of_week = Column(Integer, nullable=True)
    specific_date = Column(Date, nullable=True)
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)
    break_minutes = Column(Integer, default=60)
    is_working_day = Column(Boolean, default=True)
    leave_type = Column(String, nullable=True)
    leave_reason = Column(Text, nullable=True)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("eb_users.id"), nullable=True)
    status = Column(String, default="active")
    effective_from = Column(Date, nullable=False)
    effective_until = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)


class TrainingRecord(Base):
    __tablename__ = "eb_training_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("eb_users.id"), nullable=False)
    title = Column(String, nullable=False)
    training_type = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    provider = Column(String, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, nullable=False, default="assigned")
    score = Column(Float, nullable=True)
    max_score = Column(Float, nullable=True)
    certificate_url = Column(Text, nullable=True)
    expiry_date = Column(Date, nullable=True)
    assigned_by = Column(UUID(as_uuid=True), ForeignKey("eb_users.id"), nullable=True)
    meta = Column("metadata", JSONB, server_default="'{}'::jsonb")
    created_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)
