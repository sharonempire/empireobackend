import uuid

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.database import Base


class ConversationSession(Base):
    __tablename__ = "conversation_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default="gen_random_uuid()")
    lead_id = Column(BigInteger, nullable=True)
    ig_user_id = Column(Text, nullable=False)
    status = Column(Text, nullable=False, server_default="active")
    messages = Column(JSONB, nullable=False, server_default="'[]'::jsonb")
    extracted_data = Column(JSONB, nullable=False, server_default="'{}'::jsonb")
    conversation_stage = Column(Text, nullable=True, server_default="greeting")
    assigned_counsellor_id = Column(UUID(as_uuid=True), nullable=True)
    handoff_reason = Column(Text, nullable=True)
    last_message_at = Column(DateTime(timezone=True), server_default="now()")
    message_count = Column(Integer, server_default="0")
    retry_count = Column(Integer, server_default="0")
    created_at = Column(DateTime(timezone=True), server_default="now()")
    updated_at = Column(DateTime(timezone=True), server_default="now()")


class DMTemplate(Base):
    __tablename__ = "dm_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default="gen_random_uuid()")
    trigger_type = Column(Text, nullable=False)
    system_prompt = Column(Text, nullable=False)
    opening_message = Column(Text, nullable=False)
    qualification_fields = Column(JSONB, nullable=False)
    is_active = Column(Boolean, server_default="true")
    created_at = Column(DateTime(timezone=True), server_default="now()")
