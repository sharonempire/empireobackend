from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import PaginatedResponse, paginate_metadata
from app.database import get_db
from app.dependencies import require_perm
from app.modules.attendance import service
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
    items, total = await service.list_attendance(db, page, size, employee_id, date, attendance_status)
    return {**paginate_metadata(total, page, size), "items": items}


@router.get("/{attendance_id}", response_model=AttendanceOut)
async def api_get_attendance(
    attendance_id: UUID,
    current_user: User = Depends(require_perm("attendance", "read")),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_attendance(db, attendance_id)
