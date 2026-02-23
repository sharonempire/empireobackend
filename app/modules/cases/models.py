import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base

VALID_STAGES = [
    "initial_consultation",
    "documents_pending",
    "documents_collected",
    "university_shortlisted",
    "applied",
    "offer_received",
    "offer_accepted",
    "visa_processing",
    "visa_approved",
    "visa_rejected",
    "travel_booked",
    "completed",
    "on_hold",
    "cancelled",
]


class Case(Base):
    __tablename__ = "eb_cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("eb_students.id"), nullable=True)
    case_type = Column(String(50), default="study_abroad")
    current_stage = Column(String(50), default="initial_consultation")
    priority = Column(String(20), default="normal")
    assigned_counselor_id = Column(UUID(as_uuid=True), ForeignKey("eb_users.id"), nullable=True)
    assigned_processor_id = Column(UUID(as_uuid=True), ForeignKey("eb_users.id"), nullable=True)
    assigned_visa_officer_id = Column(UUID(as_uuid=True), ForeignKey("eb_users.id"), nullable=True)
    target_intake = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    close_reason = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    student = relationship("Student", back_populates="cases", lazy="selectin")
    applications = relationship("Application", back_populates="case", lazy="selectin")
    counselor = relationship("User", foreign_keys=[assigned_counselor_id], lazy="selectin")
    processor = relationship("User", foreign_keys=[assigned_processor_id], lazy="selectin")
    visa_officer = relationship("User", foreign_keys=[assigned_visa_officer_id], lazy="selectin")
