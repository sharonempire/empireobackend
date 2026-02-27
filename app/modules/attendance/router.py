from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import log_event
from app.core.pagination import PaginatedResponse, paginate_metadata
from app.database import get_db
from app.dependencies import get_current_user, require_perm
from app.modules.attendance import service
from app.modules.attendance.schemas import AttendanceCheckIn, AttendanceOut
from app.modules.users.models import User

router = APIRouter(prefix="/attendance", tags=["Attendance"])


class EnsureTodayRequest(BaseModel):
    user_id: UUID


@router.get("/", response_model=PaginatedResponse[AttendanceOut])
async def api_list_attendance(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=500),
    employee_id: UUID | None = None,
    date: str | None = None,
    attendance_status: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_attendance(db, page, size, employee_id, date, attendance_status)
    return {**paginate_metadata(total, page, size), "items": items}


@router.get("/today")
async def api_today_present(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all employees who are present today."""
    records = await service.get_today_present(db)
    return {"present": [AttendanceOut.model_validate(r) for r in records]}


@router.get("/today-status/{user_id}", response_model=AttendanceOut | None)
async def api_today_status(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get today's attendance record for a specific user."""
    record = await service.get_today_status(db, user_id)
    if not record:
        return None
    return record


@router.get("/history/{user_id}", response_model=PaginatedResponse[AttendanceOut])
async def api_history(
    user_id: UUID,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get attendance history for a specific user."""
    items, total = await service.get_history(db, user_id, page, size)
    return {**paginate_metadata(total, page, size), "items": items}


@router.get("/{attendance_id}", response_model=AttendanceOut)
async def api_get_attendance(
    attendance_id: UUID,
    current_user: User = Depends(get_current_user),
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


@router.post("/check-out", response_model=AttendanceOut)
async def api_check_out_no_id(
    current_user: User = Depends(require_perm("attendance", "update")),
    db: AsyncSession = Depends(get_db),
):
    """Check out the current user (finds today's open record by employee_id).
    Uses the current user's legacy_supabase_id as the employee_id (profiles.id).
    """
    employee_id = current_user.legacy_supabase_id or current_user.id
    record = await service.check_out_by_employee(db, employee_id)
    await log_event(db, "attendance.check_out", current_user.id, "attendance", str(record.id), {
        "employee_id": str(record.employee_id),
    })
    await db.commit()
    return record


@router.post("/{attendance_id}/check-out", response_model=AttendanceOut)
async def api_check_out(
    attendance_id: UUID,
    current_user: User = Depends(require_perm("attendance", "update")),
    db: AsyncSession = Depends(get_db),
):
    """Record employee check-out by attendance record ID."""
    record = await service.check_out(db, attendance_id)
    await log_event(db, "attendance.check_out", current_user.id, "attendance", str(record.id), {
        "employee_id": str(record.employee_id),
    })
    await db.commit()
    return record


@router.post("/ensure-today", response_model=AttendanceOut)
async def api_ensure_today(
    data: EnsureTodayRequest,
    current_user: User = Depends(require_perm("attendance", "create")),
    db: AsyncSession = Depends(get_db),
):
    """Idempotent: create today's attendance record if missing, return existing if present."""
    record = await service.ensure_today(db, data.user_id)
    await db.commit()
    return record
