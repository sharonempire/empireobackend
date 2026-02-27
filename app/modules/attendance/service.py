"""Attendance service layer.

On attendance INSERT, the DB trigger `assign_leads_on_checkin` fires:
- If 1 employee present → assigns one backlog lead
- If multiple present → distributes ALL backlog leads round-robin
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
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


async def check_in(
    db: AsyncSession, employee_id: UUID, date_str: str | None = None
) -> Attendance:
    """Record employee check-in. This INSERT triggers `assign_leads_on_checkin`
    in PostgreSQL, which distributes backlog leads to present employees.
    """
    now = datetime.now(timezone.utc)
    if not date_str:
        date_str = now.strftime("%A, %B %d, %Y")  # "Friday, February 25, 2026"

    # Prevent duplicate check-in for the same employee on the same date
    existing = await db.execute(
        select(Attendance).where(
            Attendance.employee_id == employee_id,
            Attendance.date == date_str,
        )
    )
    if existing.scalar_one_or_none():
        raise ConflictError("Already checked in for today")

    record = Attendance(
        employee_id=employee_id,
        checkinat=now.isoformat(),
        attendance_status="present",
        date=date_str,
    )
    db.add(record)
    await db.flush()
    await db.refresh(record)
    return record


async def check_out(db: AsyncSession, attendance_id: UUID) -> Attendance:
    """Record employee check-out."""
    record = await get_attendance(db, attendance_id)
    record.checkoutat = datetime.now(timezone.utc).isoformat()
    await db.flush()
    await db.refresh(record)
    return record


async def check_out_by_employee(db: AsyncSession, employee_id: UUID) -> Attendance:
    """Check out today's record for an employee (finds the open record)."""
    now = datetime.now(timezone.utc)
    today_str = now.strftime("%A, %B %d, %Y")

    result = await db.execute(
        select(Attendance).where(
            Attendance.employee_id == employee_id,
            Attendance.date == today_str,
            Attendance.checkoutat.is_(None),
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise NotFoundError("No open check-in found for today")
    record.checkoutat = now.isoformat()
    await db.flush()
    await db.refresh(record)
    return record


async def ensure_today(db: AsyncSession, user_id: UUID) -> Attendance:
    """Idempotent: create today's attendance record if missing, return existing if present."""
    now = datetime.now(timezone.utc)
    today_str = now.strftime("%A, %B %d, %Y")

    result = await db.execute(
        select(Attendance).where(
            Attendance.employee_id == user_id,
            Attendance.date == today_str,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    record = Attendance(
        employee_id=user_id,
        checkinat=now.isoformat(),
        attendance_status="present",
        date=today_str,
    )
    db.add(record)
    await db.flush()
    await db.refresh(record)
    return record


async def get_today_status(db: AsyncSession, user_id: UUID) -> Attendance | None:
    """Get today's attendance record for a specific user."""
    now = datetime.now(timezone.utc)
    today_str = now.strftime("%A, %B %d, %Y")

    result = await db.execute(
        select(Attendance).where(
            Attendance.employee_id == user_id,
            Attendance.date == today_str,
        )
    )
    return result.scalar_one_or_none()


async def get_history(
    db: AsyncSession, user_id: UUID, page: int = 1, size: int = 20
) -> tuple[list[Attendance], int]:
    """Get attendance history for a specific user."""
    stmt = select(Attendance).where(Attendance.employee_id == user_id)
    count_stmt = select(func.count()).select_from(Attendance).where(Attendance.employee_id == user_id)

    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.order_by(Attendance.created_at.desc()).offset((page - 1) * size).limit(size)
    result = await db.execute(stmt)
    return result.scalars().all(), total


async def get_today_present(db: AsyncSession) -> list[Attendance]:
    """Get all employees who are present today."""
    from sqlalchemy import text

    result = await db.execute(
        select(Attendance).where(
            Attendance.date == text("public.today_text()"),
            func.lower(Attendance.attendance_status) == "present",
        )
    )
    return result.scalars().all()
