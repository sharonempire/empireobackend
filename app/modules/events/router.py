from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import PaginatedResponse, paginate_metadata
from app.database import get_db
from app.dependencies import get_current_user, require_perm
from app.modules.events import service
from app.modules.events.schemas import EventOut
from app.modules.users.models import User

router = APIRouter(prefix="/events", tags=["Events"])


@router.get("/", response_model=PaginatedResponse[EventOut])
async def api_list_events(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=500),
    entity_type: str | None = None,
    entity_id: UUID | None = None,
    event_type: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_events(db, page, size, entity_type, entity_id, event_type)
    return {**paginate_metadata(total, page, size), "items": items}
