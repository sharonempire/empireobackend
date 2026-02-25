from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ActionDraftOut(BaseModel):
    id: UUID
    action_type: str
    entity_type: str
    entity_id: UUID
    payload: dict | None = None
    created_by_type: str
    created_by_id: UUID | None = None
    status: str
    requires_approval: bool
    approved_by: UUID | None = None
    approved_at: datetime | None = None
    rejection_reason: str | None = None
    executed_at: datetime | None = None
    execution_result: dict | None = None
    expires_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ActionRunOut(BaseModel):
    id: UUID
    action_draft_id: UUID
    action_type: str
    status: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: dict | None = None
    error: str | None = None
    retry_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class ReviewRequest(BaseModel):
    action: str  # "approve" or "reject"
    rejection_reason: str | None = None
