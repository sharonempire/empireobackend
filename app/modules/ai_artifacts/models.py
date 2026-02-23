import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.database import Base


class AiArtifact(Base):
    __tablename__ = "eb_ai_artifacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    artifact_type = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    model_used = Column(String, nullable=False)
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    input_summary = Column(Text, nullable=True)
    output = Column(JSONB, nullable=False)
    confidence_score = Column(Float, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("eb_users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
