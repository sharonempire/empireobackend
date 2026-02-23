from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import log_event
from app.core.pagination import PaginatedResponse, paginate
from app.database import get_db
from app.dependencies import get_current_user, require_perm
from app.modules.applications.schemas import ApplicationCreate, ApplicationOut, ApplicationUpdate
from app.modules.applications.service import create_application, get_application, list_applications, update_application
from app.modules.users.models import User

router = APIRouter(prefix="/applications", tags=["Applications"])


@router.get("/", response_model=PaginatedResponse[ApplicationOut])
async def api_list_applications(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    case_id: UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    apps, total = await list_applications(db, page, size, case_id)
    return {**paginate(total, page, size), "items": apps}


@router.get("/{application_id}", response_model=ApplicationOut)
async def api_get_application(
    application_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_application(db, application_id)


@router.post("/", response_model=ApplicationOut, status_code=201)
async def api_create_application(
    data: ApplicationCreate,
    current_user: User = Depends(require_perm("applications", "create")),
    db: AsyncSession = Depends(get_db),
):
    app = await create_application(db, data)
    await log_event(db, "application.created", current_user.id, "application", app.id, {"case_id": str(app.case_id)})
    await db.commit()
    return app


@router.patch("/{application_id}", response_model=ApplicationOut)
async def api_update_application(
    application_id: UUID,
    data: ApplicationUpdate,
    current_user: User = Depends(require_perm("applications", "update")),
    db: AsyncSession = Depends(get_db),
):
    app = await update_application(db, application_id, data)
    await log_event(db, "application.updated", current_user.id, "application", app.id, data.model_dump(exclude_unset=True))
    await db.commit()
    return app
