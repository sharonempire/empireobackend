from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.database import get_db
from app.dependencies import get_current_user
from app.modules.students.service import StudentService
from app.modules.students.schemas import StudentOut, StudentCreate
from app.modules.users.models import User
from app.core.pagination import PaginatedResponse

router = APIRouter()


@router.get("", response_model=PaginatedResponse[StudentOut])
async def list_students(page: int = Query(1), size: int = Query(20),
                        db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    svc = StudentService(db)
    items, total = await svc.list_students(page, size)
    return PaginatedResponse(items=items, total=total, page=page, size=size, pages=(total + size - 1) // size)


@router.get("/{student_id}", response_model=StudentOut)
async def get_student(student_id: UUID, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    return await StudentService(db).get_by_id(student_id)


@router.post("/convert", response_model=StudentOut, status_code=201)
async def convert_lead(data: StudentCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await StudentService(db).convert_lead(data, actor_id=user.id)
