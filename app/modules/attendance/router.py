from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.pagination import PaginatedResponse, paginate_metadata
from app.database import get_db
from app.dependencies import require_perm
from app.modules.attendance.models import Attendance
from app.modules.attendance.schemas import AttendanceOut
from app.modules.users.models import User

router = APIRouter(prefix="/attendance", tags=["Attendance"])


@router.get("/", response_model=PaginatedResponse[AttendanceOut])
async def api_list_attendance(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    employee_id: UUID | None = None,
    date: str | None = None,
    attendance_status: str | None = None,
    current_user: User = Depends(require_perm("attendance", "read")),
    db: AsyncSession = Depends(get_db),
):
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
    return {**paginate_metadata(total, page, size), "items": result.scalars().all()}


@router.get("/{attendance_id}", response_model=AttendanceOut)
async def api_get_attendance(
    attendance_id: UUID,
    current_user: User = Depends(require_perm("attendance", "read")),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Attendance).where(Attendance.id == attendance_id)
    result = await db.execute(stmt)
    attendance = result.scalar_one_or_none()
    if not attendance:
        raise NotFoundError("Attendance record not found")
    return attendance
