from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.modules.students.models import Student
from app.modules.students.schemas import StudentCreate
from app.modules.leads.models import Lead
from app.modules.events.service import EventService
from app.core.exceptions import NotFoundError, BadRequestError


class StudentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.events = EventService(db)

    async def get_by_id(self, student_id: UUID) -> Student:
        result = await self.db.execute(select(Student).where(Student.id == student_id))
        student = result.scalar_one_or_none()
        if not student:
            raise NotFoundError("Student", str(student_id))
        return student

    async def list_students(self, page=1, size=20):
        q = select(Student)
        total = (await self.db.execute(select(func.count()).select_from(q.subquery()))).scalar()
        q = q.offset((page - 1) * size).limit(size).order_by(Student.created_at.desc())
        result = await self.db.execute(q)
        return result.scalars().all(), total

    async def convert_lead(self, data: StudentCreate, actor_id: UUID) -> Student:
        lead = (await self.db.execute(select(Lead).where(Lead.id == data.lead_id))).scalar_one_or_none()
        if not lead:
            raise NotFoundError("Lead", str(data.lead_id))
        if lead.converted_to_student_id:
            raise BadRequestError("Lead already converted")
        student = Student(**data.model_dump(exclude_unset=True), assigned_counselor_id=lead.assigned_to)
        self.db.add(student)
        await self.db.flush()
        lead.converted_to_student_id = student.id
        lead.status = "converted"
        await self.db.flush()
        await self.events.log("lead_converted", "user", actor_id, "lead", lead.id, {"student_id": str(student.id)})
        return student
