from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.search_engine import hybrid_search
from app.modules.students.models import Student
from app.modules.students.schemas import StudentCreate, StudentUpdate


async def list_students(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    counselor_id: UUID | None = None,
    search: str | None = None,
) -> tuple[list, int]:
    # Use hybrid search when a search query is provided
    if search:
        filters: dict[str, str] = {}
        if counselor_id:
            filters["assigned_counselor_id"] = str(counselor_id)
        return await hybrid_search(
            db=db,
            table_name="eb_students",
            query=search,
            search_columns=["full_name", "email", "phone"],
            filters=filters or None,
            page=page,
            size=size,
        )

    # No search query — standard filtered list
    stmt = select(Student)
    count_stmt = select(func.count()).select_from(Student)

    if counselor_id:
        stmt = stmt.where(Student.assigned_counselor_id == counselor_id)
        count_stmt = count_stmt.where(Student.assigned_counselor_id == counselor_id)

    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.offset((page - 1) * size).limit(size).order_by(Student.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all(), total


async def get_student(db: AsyncSession, student_id: UUID) -> Student:
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()
    if not student:
        raise NotFoundError("Student not found")
    return student


async def create_student(db: AsyncSession, data: StudentCreate) -> Student:
    student = Student(**data.model_dump())
    db.add(student)
    await db.flush()
    return student


async def update_student(db: AsyncSession, student_id: UUID, data: StudentUpdate) -> Student:
    student = await get_student(db, student_id)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(student, key, value)
    await db.flush()
    return student
