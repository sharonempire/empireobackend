from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


class ActionDraftOut(BaseModel):
    id: UUID
    action_type: str
    entity_type: str
    entity_id: UUID
    payload: dict
    created_by_type: str
    status: str
    requires_approval: bool
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    model_config = {"from_attributes": True}


class ActionDraftCreate(BaseModel):
    action_type: str
    entity_type: str
    entity_id: UUID
    payload: dict
    requires_approval: bool = True


class ApprovalDecision(BaseModel):
    approved: bool
    reason: Optional[str] = None
