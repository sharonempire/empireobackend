import uuid
from datetime import datetime

from sqlalchemy import Column, Date, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Application(Base):
    __tablename__ = "eb_applications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("eb_cases.id"), nullable=False)
    university_name = Column(String(255), nullable=False)
    university_country = Column(String(100), nullable=True)
    program_name = Column(String(255), nullable=False)
    program_level = Column(String(50), nullable=True)
    status = Column(String(30), default="draft")
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    response_received_at = Column(DateTime(timezone=True), nullable=True)
    offer_deadline = Column(Date, nullable=True)
    offer_details = Column(JSONB, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    case = relationship("Case", back_populates="applications", lazy="selectin")
