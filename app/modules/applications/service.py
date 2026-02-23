from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.applications.models import Application
from app.modules.applications.schemas import ApplicationCreate, ApplicationUpdate


async def list_applications(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    case_id: UUID | None = None,
) -> tuple[list[Application], int]:
    stmt = select(Application)
    count_stmt = select(func.count()).select_from(Application)

    if case_id:
        stmt = stmt.where(Application.case_id == case_id)
        count_stmt = count_stmt.where(Application.case_id == case_id)

    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.offset((page - 1) * size).limit(size).order_by(Application.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all(), total


async def get_application(db: AsyncSession, application_id: UUID) -> Application:
    result = await db.execute(select(Application).where(Application.id == application_id))
    app = result.scalar_one_or_none()
    if not app:
        raise NotFoundError("Application not found")
    return app


async def create_application(db: AsyncSession, data: ApplicationCreate) -> Application:
    application = Application(**data.model_dump())
    db.add(application)
    await db.flush()
    return application


async def update_application(db: AsyncSession, application_id: UUID, data: ApplicationUpdate) -> Application:
    application = await get_application(db, application_id)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(application, key, value)
    await db.flush()
    return application
