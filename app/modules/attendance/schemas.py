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


class AttendanceCheckIn(BaseModel):
    employee_id: UUID
    date: str | None = None  # "Friday, February 25, 2026" format, or auto-filled


class AttendanceCheckOut(BaseModel):
    pass  # checkout time is set server-side
