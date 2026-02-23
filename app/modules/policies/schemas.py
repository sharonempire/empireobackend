from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PolicyOut(BaseModel):
    id: UUID
    title: str
    category: str
    content: str
    department: str | None = None
    is_active: bool
    version: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class PolicyCreate(BaseModel):
    title: str
    category: str
    content: str
    department: str | None = None
    is_active: bool = True


class PolicyUpdate(BaseModel):
    title: str | None = None
    category: str | None = None
    content: str | None = None
    department: str | None = None
    is_active: bool | None = None
