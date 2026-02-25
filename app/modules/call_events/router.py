from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import log_event
from app.core.pagination import PaginatedResponse, paginate_metadata
from app.core.websocket import broadcast_table_change
from app.database import get_db
from app.dependencies import require_perm
from app.modules.call_events import service
from app.modules.call_events.schemas import CallEventCreate, CallEventOut, CDRCreate, ClickToCallRequest
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


@router.get("/stats")
async def api_call_stats(
    employee_id: str | None = None,
    current_user: User = Depends(require_perm("call_events", "read")),
    db: AsyncSession = Depends(get_db),
):
    """Call event statistics — total, connected, avg duration, with recording."""
    return await service.get_call_stats(db, employee_id)


@router.get("/{call_event_id}", response_model=CallEventOut)
async def api_get_call_event(
    call_event_id: int,
    current_user: User = Depends(require_perm("call_events", "read")),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_call_event(db, call_event_id)


@router.post("/", response_model=CallEventOut, status_code=201)
async def api_ingest_call_event(
    data: CallEventCreate,
    current_user: User = Depends(require_perm("call_events", "create")),
    db: AsyncSession = Depends(get_db),
):
    """Ingest a call event from the telephony provider webhook.

    DB triggers auto-handle:
    - Phone normalization (caller_phone_norm, agent_phone_norm)
    - Lead creation/matching by phone number
    - Agent resolution from profiles table
    - Call info appended to lead_info.call_info JSONB
    """
    event = await service.ingest_call_event(db, data.model_dump(exclude_unset=True))
    await log_event(db, "call_event.ingested", current_user.id, "call_event", str(event.id), {
        "event_type": event.event_type,
        "call_uuid": event.call_uuid,
    })
    await db.commit()
    await broadcast_table_change("call_events", "INSERT", event.id, {"event_type": event.event_type})
    return event


@router.post("/cdr", response_model=CallEventOut, status_code=201)
async def api_ingest_cdr(
    data: CDRCreate,
    current_user: User = Depends(require_perm("call_events", "create")),
    db: AsyncSession = Depends(get_db),
):
    """Push a CDR (Call Detail Record) from the telephony system.
    Maps CDR fields to call_event columns and inserts a record.
    """
    event = await service.ingest_cdr(db, data.model_dump(exclude_unset=True))
    await log_event(db, "call_event.cdr_ingested", current_user.id, "call_event", str(event.id), {
        "extension": data.extension,
        "destination": data.destination,
    })
    await db.commit()
    return event


@router.post("/click-to-call")
async def api_click_to_call(
    data: ClickToCallRequest,
    current_user: User = Depends(require_perm("call_events", "create")),
    db: AsyncSession = Depends(get_db),
):
    """Trigger a click-to-call via the telephony provider.

    This creates a call event record and could trigger an external API call
    to the telephony provider (Voxbay/Exotel) to initiate the call.
    """
    # Record the click-to-call as a call event
    event_data = {
        "event_type": "click_to_call",
        "caller_number": data.source,
        "called_number": data.destination,
        "extension": data.extension,
        "callerid": data.callerid,
    }
    event = await service.ingest_call_event(db, event_data)
    await log_event(db, "call_event.click_to_call", current_user.id, "call_event", str(event.id), {
        "source": data.source,
        "destination": data.destination,
    })
    await db.commit()
    return {"status": "initiated", "call_event_id": event.id, "source": data.source, "destination": data.destination}
