"""Call events service layer."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.call_events.models import CallEvent


async def list_call_events(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    event_type: str | None = None,
    call_uuid: str | None = None,
    agent_number: str | None = None,
    call_date: str | None = None,
) -> tuple[list[CallEvent], int]:
    stmt = select(CallEvent)
    count_stmt = select(func.count()).select_from(CallEvent)

    if event_type:
        stmt = stmt.where(CallEvent.event_type == event_type)
        count_stmt = count_stmt.where(CallEvent.event_type == event_type)
    if call_uuid:
        stmt = stmt.where(CallEvent.call_uuid == call_uuid)
        count_stmt = count_stmt.where(CallEvent.call_uuid == call_uuid)
    if agent_number:
        stmt = stmt.where(CallEvent.agent_number == agent_number)
        count_stmt = count_stmt.where(CallEvent.agent_number == agent_number)
    if call_date:
        stmt = stmt.where(CallEvent.call_date == call_date)
        count_stmt = count_stmt.where(CallEvent.call_date == call_date)

    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.offset((page - 1) * size).limit(size).order_by(CallEvent.id.desc())
    result = await db.execute(stmt)
    return result.scalars().all(), total


async def get_call_event(db: AsyncSession, call_event_id: int) -> CallEvent:
    result = await db.execute(select(CallEvent).where(CallEvent.id == call_event_id))
    call_event = result.scalar_one_or_none()
    if not call_event:
        raise NotFoundError("Call event not found")
    return call_event


async def ingest_call_event(db: AsyncSession, data: dict) -> CallEvent:
    """Ingest a call event from telephony webhook.

    DB triggers auto-handle on INSERT:
    - `call_events_norm_maint`: normalizes caller/agent phone numbers
    - `handle_call_event`: classifies calls, resolves agents from profiles,
      creates or matches leads by phone, appends call info to lead_info
    """
    event = CallEvent(**data)
    db.add(event)
    await db.flush()
    await db.refresh(event)
    return event


async def get_call_stats(db: AsyncSession, employee_id: str | None = None) -> dict:
    """Get call event statistics."""
    from sqlalchemy import text

    base = "SELECT COUNT(*) as total, " \
           "SUM(CASE WHEN total_duration > 0 THEN 1 ELSE 0 END) as connected, " \
           "AVG(CASE WHEN conversation_duration > 0 THEN conversation_duration END) as avg_duration, " \
           "SUM(CASE WHEN recording_url IS NOT NULL THEN 1 ELSE 0 END) as with_recording " \
           "FROM call_events"

    if employee_id:
        result = await db.execute(
            text(base + " WHERE agent_phone_norm = (SELECT phone::text FROM profiles WHERE id = :emp_id LIMIT 1)"),
            {"emp_id": employee_id},
        )
    else:
        result = await db.execute(text(base))

    row = result.first()
    if not row:
        return {"total": 0, "connected": 0, "avg_duration": 0, "with_recording": 0}
    return dict(row._mapping)


async def ingest_cdr(db: AsyncSession, data: dict) -> CallEvent:
    """Ingest a CDR (Call Detail Record) — maps CDR fields to call_event columns."""
    event_data = {
        "event_type": "cdr",
        "extension": data.get("extension"),
        "destination": data.get("destination"),
        "callerid": data.get("callerid"),
        "total_duration": data.get("duration_seconds"),
        "call_status": data.get("status"),
        "call_date": data.get("datetime"),
        "recording_url": data.get("recording_url"),
    }
    event = CallEvent(**{k: v for k, v in event_data.items() if v is not None})
    db.add(event)
    await db.flush()
    await db.refresh(event)
    return event
