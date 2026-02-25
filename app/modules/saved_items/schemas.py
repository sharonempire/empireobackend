from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class SavedJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int | None = None
    job_id: int | None = None
    job_details: Any | None = None
    created_at: datetime | None = None
