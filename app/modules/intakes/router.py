from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import log_event
from app.core.pagination import PaginatedResponse, paginate_metadata
from app.database import get_db
from app.dependencies import require_perm
from app.modules.intakes import service
from app.modules.intakes.schemas import IntakeCreate, IntakeOut, IntakeUpdate
from app.modules.users.models import User

router = APIRouter(prefix="/intakes", tags=["Intakes"])


@router.get("/", response_model=PaginatedResponse[IntakeOut])
async def api_list_intakes(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=500),
    current_user: User = Depends(require_perm("intakes", "read")),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_intakes(db, page, size)
    return {**paginate_metadata(total, page, size), "items": items}


@router.get("/{intake_id}", response_model=IntakeOut)
async def api_get_intake(
    intake_id: int,
    current_user: User = Depends(require_perm("intakes", "read")),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_intake(db, intake_id)


@router.post("/", response_model=IntakeOut)
async def api_create_intake(
    body: IntakeCreate,
    current_user: User = Depends(require_perm("intakes", "read")),
    db: AsyncSession = Depends(get_db),
):
    intake = await service.create_intake(db, body)
    await log_event(
        db=db,
        event_type="intake.created",
        actor_id=current_user.id,
        entity_type="intake",
        entity_id=intake.id,
        metadata={"name": intake.name},
    )
    await db.commit()
    return intake


async def _update_intake(intake_id, body, current_user, db):
    intake = await service.update_intake(db, intake_id, body)
    await log_event(
        db=db, event_type="intake.updated", actor_id=current_user.id,
        entity_type="intake", entity_id=intake.id, metadata={"name": intake.name},
    )
    await db.commit()
    return intake


@router.patch("/{intake_id}", response_model=IntakeOut)
async def api_update_intake(
    intake_id: int, body: IntakeUpdate,
    current_user: User = Depends(require_perm("intakes", "read")),
    db: AsyncSession = Depends(get_db),
):
    return await _update_intake(intake_id, body, current_user, db)


@router.put("/{intake_id}", response_model=IntakeOut)
async def api_update_intake_put(
    intake_id: int, body: IntakeUpdate,
    current_user: User = Depends(require_perm("intakes", "read")),
    db: AsyncSession = Depends(get_db),
):
    """PUT alias for PATCH intake update."""
    return await _update_intake(intake_id, body, current_user, db)
