"""Refresh token model for DB-backed token rotation and reuse detection."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class RefreshToken(Base):
    __tablename__ = "eb_refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("eb_users.id"), nullable=False, index=True
    )
    token_hash = Column(String(255), nullable=False, unique=True)
    family_id = Column(
        UUID(as_uuid=True), nullable=False, index=True
    )  # token family for rotation
    is_revoked = Column(Boolean, default=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revoke_reason = Column(
        String(50), nullable=True
    )  # "rotated", "logout", "logout_all", "reuse_detected", "password_changed"
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    user_agent = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
