from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import log_event
from app.core.pagination import PaginatedResponse, paginate_metadata
from app.database import get_db
from app.dependencies import require_perm
from app.modules.attendance import service
from app.modules.attendance.schemas import AttendanceCheckIn, AttendanceOut
from app.modules.users.models import User

router = APIRouter(prefix="/attendance", tags=["Attendance"])


@router.get("/", response_model=PaginatedResponse[AttendanceOut])
async def api_list_attendance(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=500),
    employee_id: UUID | None = None,
    date: str | None = None,
    attendance_status: str | None = None,
    current_user: User = Depends(require_perm("attendance", "read")),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_attendance(db, page, size, employee_id, date, attendance_status)
    return {**paginate_metadata(total, page, size), "items": items}


@router.get("/today")
async def api_today_present(
    current_user: User = Depends(require_perm("attendance", "read")),
    db: AsyncSession = Depends(get_db),
):
    """List all employees who are present today."""
    records = await service.get_today_present(db)
    return {"present": [AttendanceOut.model_validate(r) for r in records]}


@router.get("/{attendance_id}", response_model=AttendanceOut)
async def api_get_attendance(
    attendance_id: UUID,
    current_user: User = Depends(require_perm("attendance", "read")),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_attendance(db, attendance_id)


@router.post("/check-in", response_model=AttendanceOut, status_code=201)
async def api_check_in(
    data: AttendanceCheckIn,
    current_user: User = Depends(require_perm("attendance", "create")),
    db: AsyncSession = Depends(get_db),
):
    """Record employee check-in.

    This triggers the DB function `assign_leads_on_checkin` which
    automatically distributes unassigned (backlog) leads to present staff
    via round-robin.
    """
    record = await service.check_in(db, data.employee_id, data.date)
    await log_event(db, "attendance.check_in", current_user.id, "attendance", str(record.id), {
        "employee_id": str(data.employee_id),
    })
    await db.commit()
    return record


@router.post("/{attendance_id}/check-out", response_model=AttendanceOut)
async def api_check_out(
    attendance_id: UUID,
    current_user: User = Depends(require_perm("attendance", "update")),
    db: AsyncSession = Depends(get_db),
):
    """Record employee check-out."""
    record = await service.check_out(db, attendance_id)
    await log_event(db, "attendance.check_out", current_user.id, "attendance", str(record.id), {
        "employee_id": str(record.employee_id),
    })
    await db.commit()
    return record
