from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AiArtifactOut(BaseModel):
    id: UUID
    artifact_type: str
    entity_type: str
    entity_id: UUID
    model_used: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    input_summary: str | None = None
    output: Any
    confidence_score: float | None = None
    created_by: UUID | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AiArtifactCreate(BaseModel):
    artifact_type: str
    entity_type: str
    entity_id: UUID
    model_used: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    input_summary: str | None = None
    output: Any
    confidence_score: float | None = None
