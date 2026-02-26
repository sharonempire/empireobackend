import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    checkinat = Column(Text, nullable=True)
    checkoutat = Column(Text, nullable=True)
    attendance_status = Column(Text, nullable=True)
    date = Column(Text, nullable=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=True)

    profile = relationship("Profile", lazy="selectin")
