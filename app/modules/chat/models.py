from sqlalchemy import BigInteger, Column, DateTime, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB

from app.database import Base


class ChatConversation(Base):
    __tablename__ = "chat_conversations"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    counselor_id = Column(Text, nullable=True)
    lead_uuid = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    conversation_id = Column(BigInteger, nullable=True)
    sender_id = Column(Text, nullable=True)
    message = Column(Text, nullable=True)
    message_type = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)
    
    # Missing columns from audit
    voice_duration = Column(Integer, nullable=True)  # Duration of voice message in seconds
    course_id = Column(Text, nullable=True)
    course_deatails = Column(JSONB, nullable=True)  # Note: typo in DB (deatails)

