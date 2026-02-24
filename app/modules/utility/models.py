from sqlalchemy import Column, DateTime, Text

from app.database import Base


class ShortLink(Base):
    __tablename__ = "short_links"

    code = Column(Text, primary_key=True)
    target_url = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=True)


class ChatbotSession(Base):
    __tablename__ = "chatbot_sessions"

    session_id = Column(Text, primary_key=True)
    last_intent = Column(Text, nullable=True)
    last_country = Column(Text, nullable=True)
    last_field = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)
