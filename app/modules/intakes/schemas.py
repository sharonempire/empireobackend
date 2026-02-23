from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class IntakeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    start_date: date
    end_date: date
    application_deadline: Optional[date] = None
    description: Optional[str] = None
    universities: Optional[Any] = None
    courses: Optional[Any] = None
    requirements: Optional[Any] = None
    fees: Optional[Any] = None
    scholarships: Optional[Any] = None
    additional_info: Optional[Any] = None
    commission: Optional[Any] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
