from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import PaginatedResponse, paginate_metadata
from app.database import get_db
from app.dependencies import require_perm
from app.modules.call_events import service
from app.modules.call_events.schemas import CallEventOut
from app.modules.users.models import User

router = APIRouter(prefix="/call-events", tags=["Call Events"])


@router.get("/", response_model=PaginatedResponse[CallEventOut])
async def api_list_call_events(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    event_type: str | None = None,
    call_uuid: str | None = None,
    agent_number: str | None = None,
    call_date: str | None = None,
    current_user: User = Depends(require_perm("call_events", "read")),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_call_events(db, page, size, event_type, call_uuid, agent_number, call_date)
    return {**paginate_metadata(total, page, size), "items": items}


@router.get("/{call_event_id}", response_model=CallEventOut)
async def api_get_call_event(
    call_event_id: int,
    current_user: User = Depends(require_perm("call_events", "read")),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_call_event(db, call_event_id)
