import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, Float, Text, DateTime, ForeignKey, Integer, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from app.database import Base


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sl_no: Mapped[int] = mapped_column(Integer, autoincrement=True, unique=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    phone_norm: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source_detail: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="new")
    lead_tab: Mapped[str] = mapped_column(String(20), default="student")
    heat_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    draft_status: Mapped[str] = mapped_column(String(20), default="draft")
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    freelancer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    freelancer_manager: Mapped[str | None] = mapped_column(String(255), nullable=True)
    country_preference: Mapped[list | None] = mapped_column(ARRAY(String), nullable=True)
    ig_handle: Mapped[str | None] = mapped_column(String(255), nullable=True)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)
    follow_up: Mapped[str | None] = mapped_column(Text, nullable=True)
    info_progress: Mapped[str | None] = mapped_column(String(50), nullable=True)
    documents_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    call_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    changes_history: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    fresh: Mapped[bool] = mapped_column(Boolean, default=True)
    profile_image: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_premium_jobs: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    is_premium_courses: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    is_registered: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    fcm_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    finder_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    current_module: Mapped[str | None] = mapped_column(String(50), nullable=True)
    preferences_completed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    profile_completion: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lead_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ai_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_score_reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    converted_to_student_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=True)
    date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    legacy_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, unique=True)

    assigned_user = relationship("User", foreign_keys=[assigned_to], lazy="selectin")
    lead_info = relationship("LeadInfo", back_populates="lead", uselist=False, lazy="selectin")


class LeadInfo(Base):
    __tablename__ = "lead_info"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), unique=True)
    basic_info: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    education: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    work_experience: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    budget_info: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    preferences: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    english_proficiency: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    call_info: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    documents: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    domain_tags: Mapped[list | None] = mapped_column(ARRAY(String), nullable=True, default=[])
    profile_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    needs_enrichment: Mapped[bool] = mapped_column(Boolean, default=True)
    changes_history: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    legacy_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, unique=True)

    lead = relationship("Lead", back_populates="lead_info")
