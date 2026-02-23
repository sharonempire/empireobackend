from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Lead(Base):
    __tablename__ = "leadslist"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True))
    name = Column(Text, nullable=True)
    email = Column(Text, nullable=True)
    phone = Column(BigInteger, nullable=True)
    freelancer_manager = Column(Text, nullable=True)
    freelancer = Column(Text, nullable=True)
    source = Column(Text, nullable=True)
    status = Column(Text, nullable=True)
    follow_up = Column(Text, nullable=True)
    remark = Column(Text, nullable=True)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=True)
    draft_status = Column(Text, nullable=True, server_default="draft")
    sl_no = Column(Integer, unique=True, autoincrement=True)
    heat_status = Column(Text, nullable=True)
    info_progress = Column(Text, nullable=True)
    call_summary = Column(Text, nullable=True)
    phone_norm = Column(Text, nullable=True)
    lead_tab = Column(Text, nullable=True, server_default="student")  # enum: student, job
    date = Column(DateTime(timezone=True), nullable=True)
    changes_history = Column(JSONB, nullable=True)
    lead_type = Column(Text, nullable=True)
    documents_status = Column(Text, nullable=True)
    fresh = Column(Boolean, nullable=True, server_default="true")
    profile_image = Column(Text, nullable=True)
    is_premium_jobs = Column(Boolean, nullable=True)
    is_premium_courses = Column(Boolean, nullable=True)
    is_resume_downloaded = Column(Boolean, nullable=True)
    country_preference = Column(ARRAY(Text), nullable=True)
    is_registered = Column(Boolean, nullable=True)
    user_id = Column(String, nullable=True)
    fcm_token = Column(Text, nullable=True)
    finder_type = Column(Text, nullable=True)
    current_module = Column(Text, nullable=True)  # enum: notification, chat, application
    preferences_completed = Column(Boolean, nullable=True)
    profile_completion = Column(BigInteger, nullable=True)
    ig_handle = Column(Text, nullable=True)

    # Relationships
    assigned_profile = relationship("Profile", foreign_keys=[assigned_to], lazy="selectin")
    lead_info = relationship("LeadInfo", foreign_keys="LeadInfo.id", lazy="selectin", uselist=False)


class LeadInfo(Base):
    __tablename__ = "lead_info"

    id = Column(BigInteger, ForeignKey("leadslist.id"), primary_key=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True))
    basic_info = Column(JSONB, nullable=True)
    education = Column(JSONB, nullable=True)
    work_expierience = Column(JSONB, nullable=True)  # Note: typo in DB
    budget_info = Column(JSONB, nullable=True)
    preferences = Column(JSONB, nullable=True)
    english_proficiency = Column(JSONB, nullable=True)
    call_info = Column(JSONB, nullable=True)
    changes_history = Column(JSONB, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    documents = Column(JSONB, nullable=True)
    fcm_token = Column(Text, nullable=True)
    user_id = Column(String, nullable=True)
    domain_tags = Column(ARRAY(Text), nullable=True, server_default="{}")
    interest_embedding = Column(Text, nullable=True)  # VECTOR type
    profile_text = Column(Text, nullable=True)
    needs_enrichment = Column(Boolean, nullable=True, server_default="true")
    enrichment_updated_at = Column(DateTime(timezone=True), nullable=True)


class LeadAssignmentTracker(Base):
    __tablename__ = "lead_assignment_tracker"

    id = Column(Integer, primary_key=True)
    last_assigned_employee = Column(UUID(as_uuid=True), nullable=True)
