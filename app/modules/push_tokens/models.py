import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class UserPushToken(Base):
    __tablename__ = "user_push_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)
    fcm_token = Column(Text, nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)


class UserFCMToken(Base):
    __tablename__ = "user_fcm_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)
    fcm_token = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)

