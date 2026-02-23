from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AttendanceOut(BaseModel):
    id: UUID
    created_at: datetime | None = None
    checkinat: str | None = None
    checkoutat: str | None = None
    attendance_status: str | None = None
    date: str | None = None
    employee_id: UUID | None = None

    model_config = ConfigDict(from_attributes=True)
