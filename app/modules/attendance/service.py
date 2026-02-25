"""Attendance service layer."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.attendance.models import Attendance


async def list_attendance(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    employee_id: UUID | None = None,
    date: str | None = None,
    attendance_status: str | None = None,
) -> tuple[list[Attendance], int]:
    stmt = select(Attendance)
    count_stmt = select(func.count()).select_from(Attendance)

    if employee_id:
        stmt = stmt.where(Attendance.employee_id == employee_id)
        count_stmt = count_stmt.where(Attendance.employee_id == employee_id)
    if date:
        stmt = stmt.where(Attendance.date == date)
        count_stmt = count_stmt.where(Attendance.date == date)
    if attendance_status:
        stmt = stmt.where(Attendance.attendance_status == attendance_status)
        count_stmt = count_stmt.where(Attendance.attendance_status == attendance_status)

    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.offset((page - 1) * size).limit(size).order_by(Attendance.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all(), total


async def get_attendance(db: AsyncSession, attendance_id: UUID) -> Attendance:
    result = await db.execute(select(Attendance).where(Attendance.id == attendance_id))
    attendance = result.scalar_one_or_none()
    if not attendance:
        raise NotFoundError("Attendance record not found")
    return attendance
