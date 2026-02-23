from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class WorkflowDefinitionOut(BaseModel):
    id: UUID
    name: str
    stages: dict | list | None = None
    transitions: dict | list | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WorkflowInstanceOut(BaseModel):
    id: UUID
    workflow_definition_id: UUID
    entity_type: str
    entity_id: UUID
    current_stage: str | None = None
    stage_entered_at: datetime | None = None
    history: list | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
