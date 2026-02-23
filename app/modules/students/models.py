import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, Column, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Student(Base):
    __tablename__ = "eb_students"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(BigInteger, unique=True, nullable=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    nationality = Column(String(100), nullable=True)
    passport_number = Column(String(50), nullable=True)
    passport_expiry = Column(Date, nullable=True)
    education_level = Column(String(50), nullable=True)
    education_details = Column(JSONB, nullable=True)
    english_test_type = Column(String(20), nullable=True)
    english_test_score = Column(String(20), nullable=True)
    work_experience_years = Column(Integer, default=0)
    preferred_countries = Column(JSONB, nullable=True)
    preferred_programs = Column(JSONB, nullable=True)
    assigned_counselor_id = Column(UUID(as_uuid=True), ForeignKey("eb_users.id"), nullable=True)
    assigned_processor_id = Column(UUID(as_uuid=True), ForeignKey("eb_users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    cases = relationship("Case", back_populates="student", lazy="selectin")
    counselor = relationship("User", foreign_keys=[assigned_counselor_id], lazy="selectin")
    processor = relationship("User", foreign_keys=[assigned_processor_id], lazy="selectin")
