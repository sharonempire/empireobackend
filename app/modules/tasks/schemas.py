from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class TaskOut(BaseModel):
    id: UUID
    entity_type: str | None = None
    entity_id: UUID | None = None
    title: str
    description: str | None = None
    task_type: str
    assigned_to: UUID | None = None
    created_by: UUID | None = None
    due_at: datetime | None = None
    priority: str
    status: str
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskCreate(BaseModel):
    entity_type: str | None = None
    entity_id: UUID | None = None
    title: str
    description: str | None = None
    task_type: str = "general"
    assigned_to: UUID | None = None
    due_at: datetime | None = None
    priority: str = "normal"


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    assigned_to: UUID | None = None
    due_at: datetime | None = None
    priority: str | None = None
    status: str | None = None
