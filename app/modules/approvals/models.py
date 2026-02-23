import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.database import Base


class ActionDraft(Base):
    __tablename__ = "eb_action_drafts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    action_type = Column(String(50), nullable=False)
    entity_type = Column(String(30), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    payload = Column(JSONB, nullable=True)
    created_by_type = Column(String(10), default="user")
    created_by_id = Column(UUID(as_uuid=True), nullable=True)
    status = Column(String(30), default="pending_approval")
    requires_approval = Column(Boolean, default=True)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("eb_users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    executed_at = Column(DateTime(timezone=True), nullable=True)
    execution_result = Column(JSONB, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    approver = relationship("User", foreign_keys=[approved_by], lazy="selectin")


class ActionRun(Base):
    __tablename__ = "eb_action_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    action_draft_id = Column(UUID(as_uuid=True), ForeignKey("eb_action_drafts.id"), nullable=False)
    action_type = Column(String(50), nullable=False)
    status = Column(String(20), default="started")
    started_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    result = Column(JSONB, nullable=True)
    error = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    draft = relationship("ActionDraft", lazy="selectin")
