import uuid

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.database import Base


class ChatConversation(Base):
    __tablename__ = "chat_conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    counselor_id = Column(Text, nullable=True)
    lead_uuid = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)
    last_message_at = Column(DateTime(timezone=True), nullable=True)
    last_message_id = Column(Text, nullable=True)
    last_message_text = Column(Text, nullable=True)
    unread_count_assigned = Column(Integer, nullable=True)
    unread_count_user = Column(Integer, nullable=True)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), nullable=True)
    sender_id = Column(Text, nullable=True)
    message = Column(Text, nullable=True)
    message_type = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)

    # Missing columns from audit
    voice_duration = Column(Integer, nullable=True)  # Duration of voice message in seconds
    course_id = Column(Text, nullable=True)
    course_deatails = Column(JSONB, nullable=True)  # Note: typo in DB (deatails)
    file_name = Column(Text, nullable=True)
    file_size = Column(BigInteger, nullable=True)
    file_url = Column(Text, nullable=True)
    is_read = Column(Boolean, nullable=True)
    message_text = Column(Text, nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    receiver_id = Column(Text, nullable=True)

