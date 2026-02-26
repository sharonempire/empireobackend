from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import log_event
from app.core.pagination import PaginatedResponse, paginate_metadata
from app.database import get_db
from app.dependencies import get_current_user, require_perm
from app.modules.students.schemas import StudentCreate, StudentOut, StudentUpdate
from app.modules.students.service import create_student, get_student, list_students, update_student
from app.modules.users.models import User

router = APIRouter(prefix="/students", tags=["Students"])


@router.get("/", response_model=PaginatedResponse[StudentOut])
async def api_list_students(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=500),
    counselor_id: UUID | None = None,
    search: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    students, total = await list_students(db, page, size, counselor_id, search)
    return {**paginate_metadata(total, page, size), "items": students}


@router.get("/{student_id}", response_model=StudentOut)
async def api_get_student(
    student_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_student(db, student_id)


@router.post("/", response_model=StudentOut, status_code=201)
async def api_create_student(
    data: StudentCreate,
    current_user: User = Depends(require_perm("students", "create")),
    db: AsyncSession = Depends(get_db),
):
    student = await create_student(db, data)
    await log_event(db, "student.created", current_user.id, "student", student.id, {"full_name": student.full_name})
    await db.commit()
    return student


@router.patch("/{student_id}", response_model=StudentOut)
async def api_update_student(
    student_id: UUID,
    data: StudentUpdate,
    current_user: User = Depends(require_perm("students", "update")),
    db: AsyncSession = Depends(get_db),
):
    student = await update_student(db, student_id, data)
    await log_event(db, "student.updated", current_user.id, "student", student.id, data.model_dump(exclude_unset=True))
    await db.commit()
    return student
