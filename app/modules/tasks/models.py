import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Task(Base):
    __tablename__ = "eb_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type = Column(String(30), nullable=True)
    entity_id = Column(UUID(as_uuid=True), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    task_type = Column(String(30), default="general")
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("eb_users.id"), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("eb_users.id"), nullable=True)
    due_at = Column(DateTime(timezone=True), nullable=True)
    priority = Column(String(20), default="normal")
    status = Column(String(20), default="pending")
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    assignee = relationship("User", foreign_keys=[assigned_to], lazy="selectin")
    creator = relationship("User", foreign_keys=[created_by], lazy="selectin")
