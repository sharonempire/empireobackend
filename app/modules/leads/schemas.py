from datetime import datetime

from pydantic import BaseModel


class LeadOut(BaseModel):
    id: int
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    source: str | None = None
    status: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class LeadDetailOut(LeadOut):
    info: dict | list | None = None
