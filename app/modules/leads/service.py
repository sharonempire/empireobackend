"""Leads service layer — full CRUD + assignment + views.

The DB has extensive trigger logic that fires automatically:
- assign_lead_round_robin: auto-assigns new leads to present staff (round-robin)
- leadslist_block_duplicates: blocks duplicate email+phone inserts
- leadslist_norm_maint: normalizes phone numbers
- ensure_lead_info_row: auto-creates lead_info row
- ensure_chat_conversation_for_lead: auto-creates chat conversation
- set_fresh_lead: marks new leads as fresh
- update_lead_type_and_status: maps status values to lead_type
- update_lead_date: parses follow_up text into date timestamp
- notify_leadslist_status_change: sends email on status change

On attendance INSERT:
- assign_leads_on_checkin: distributes backlog leads to present employees

We leverage these triggers — our service just does the INSERT/UPDATE and lets
the DB handle the side effects.
"""

from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.core.search_engine import hybrid_search
from app.modules.leads.models import Lead, LeadAssignmentTracker, LeadInfo
from app.modules.leads.schemas import LeadCreate, LeadInfoCreate, LeadInfoUpdate, LeadUpdate


# ── List / Search ────────────────────────────────────────────────────


async def list_leads(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    search: str | None = None,
    status: str | None = None,
    heat_status: str | None = None,
    lead_tab: str | None = None,
    assigned_to: str | None = None,
    phone: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    user_id: str | None = None,
) -> tuple[list, int]:
    from datetime import datetime as dt

    # Use hybrid search when a search query is provided
    if search:
        filters: dict[str, str] = {}
        if status:
            filters["status"] = status
        if heat_status:
            filters["heat_status"] = heat_status
        if lead_tab:
            filters["lead_tab"] = lead_tab
        if assigned_to:
            filters["assigned_to"] = assigned_to
        return await hybrid_search(
            db=db,
            table_name="leadslist",
            query=search,
            search_columns=["name", "email"],
            filters=filters or None,
            page=page,
            size=size,
        )

    # No search query — standard filtered list
    stmt = select(Lead)
    count_stmt = select(func.count()).select_from(Lead)

    if status:
        stmt = stmt.where(Lead.status == status)
        count_stmt = count_stmt.where(Lead.status == status)
    if heat_status:
        stmt = stmt.where(Lead.heat_status == heat_status)
        count_stmt = count_stmt.where(Lead.heat_status == heat_status)
    if lead_tab:
        stmt = stmt.where(Lead.lead_tab == lead_tab)
        count_stmt = count_stmt.where(Lead.lead_tab == lead_tab)
    if assigned_to:
        stmt = stmt.where(Lead.assigned_to == assigned_to)
        count_stmt = count_stmt.where(Lead.assigned_to == assigned_to)
    if user_id:
        stmt = stmt.where(Lead.user_id == user_id)
        count_stmt = count_stmt.where(Lead.user_id == user_id)
    if phone:
        # Match on normalized phone or raw phone
        phone_clean = phone.lstrip("+").replace(" ", "").replace("-", "")
        stmt = stmt.where(func.coalesce(Lead.phone_norm, "").like(f"%{phone_clean}%"))
        count_stmt = count_stmt.where(func.coalesce(Lead.phone_norm, "").like(f"%{phone_clean}%"))
    if start_date:
        stmt = stmt.where(Lead.created_at >= dt.fromisoformat(start_date))
        count_stmt = count_stmt.where(Lead.created_at >= dt.fromisoformat(start_date))
    if end_date:
        stmt = stmt.where(Lead.created_at <= dt.fromisoformat(end_date))
        count_stmt = count_stmt.where(Lead.created_at <= dt.fromisoformat(end_date))

    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.offset((page - 1) * size).limit(size).order_by(Lead.id.desc())
    result = await db.execute(stmt)
    return result.scalars().all(), total


# ── Single Lead ──────────────────────────────────────────────────────


async def get_lead(db: AsyncSession, lead_id: int) -> Lead:
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise NotFoundError("Lead not found")
    return lead


async def get_lead_info(db: AsyncSession, lead_id: int) -> LeadInfo | None:
    result = await db.execute(select(LeadInfo).where(LeadInfo.id == lead_id))
    return result.scalar_one_or_none()


# ── Create Lead ──────────────────────────────────────────────────────
# DB triggers handle: round-robin assignment, duplicate blocking,
# phone normalization, fresh flag, date, lead_info row, chat conversation


async def create_lead(db: AsyncSession, data: LeadCreate) -> Lead:
    lead = Lead(**data.model_dump(exclude_unset=True))
    db.add(lead)
    await db.flush()
    await db.refresh(lead)
    return lead


# ── Update Lead ──────────────────────────────────────────────────────
# DB triggers handle: status→lead_type mapping, date recalc,
# country sync, email notification on status change


async def update_lead(db: AsyncSession, lead_id: int, data: LeadUpdate) -> Lead:
    lead = await get_lead(db, lead_id)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(lead, key, value)
    await db.flush()
    await db.refresh(lead)
    return lead


# ── Update Lead Info ─────────────────────────────────────────────────


async def update_lead_info(
    db: AsyncSession, lead_id: int, data: LeadInfoUpdate
) -> LeadInfo:
    info = await get_lead_info(db, lead_id)
    if not info:
        raise NotFoundError("Lead info not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(info, key, value)
    await db.flush()
    await db.refresh(info)
    return info


# ── Create Lead Info ─────────────────────────────────────────────────


async def create_lead_info(
    db: AsyncSession, lead_id: int, data: LeadInfoCreate
) -> LeadInfo:
    """Create a lead_info record for a lead.
    Note: DB trigger ensure_lead_info_row normally auto-creates this on lead INSERT.
    This endpoint is for cases where it needs to be created/replaced manually.
    """
    existing = await get_lead_info(db, lead_id)
    if existing:
        raise ConflictError(f"Lead info already exists for lead {lead_id}")

    # Verify the lead exists
    await get_lead(db, lead_id)

    info = LeadInfo(id=lead_id, **data.model_dump(exclude_unset=True))
    db.add(info)
    await db.flush()
    await db.refresh(info)
    return info


# ── Delete Lead ─────────────────────────────────────────────────────


async def delete_lead(db: AsyncSession, lead_id: int) -> None:
    """Delete a lead and its lead_info record."""
    lead = await get_lead(db, lead_id)
    # Delete lead_info first (FK constraint)
    info = await get_lead_info(db, lead_id)
    if info:
        await db.delete(info)
    await db.delete(lead)
    await db.flush()


# ── Batch Lead Info ─────────────────────────────────────────────────


async def batch_get_lead_infos(
    db: AsyncSession, lead_ids: list[int]
) -> list[LeadInfo]:
    """Batch fetch lead_info records for multiple lead IDs."""
    if not lead_ids:
        return []
    result = await db.execute(
        select(LeadInfo).where(LeadInfo.id.in_(lead_ids))
    )
    return result.scalars().all()


# ── Reassign Lead ────────────────────────────────────────────────────


async def reassign_lead(
    db: AsyncSession, lead_id: int, new_assignee: UUID
) -> Lead:
    lead = await get_lead(db, lead_id)
    lead.assigned_to = new_assignee
    await db.flush()
    await db.refresh(lead)
    return lead


# ── Redistribute Leads (calls DB function) ───────────────────────────


async def redistribute_leads(
    db: AsyncSession, source_counselor_id: UUID, leads_to_move: int
) -> int:
    """Move N leads from one counselor to others via round-robin.
    Uses the DB function `redistribute_partial_leads`.
    """
    result = await db.execute(
        text("SELECT redistribute_partial_leads(:src, :n)"),
        {"src": str(source_counselor_id), "n": leads_to_move},
    )
    moved = result.scalar() or 0
    return moved


# ── Create Lead from Call (calls DB function) ────────────────────────


async def create_or_get_lead_from_call(
    db: AsyncSession, caller_number: str, agent_number: str | None = None
) -> dict:
    """Find or create a lead from an incoming call.
    Uses the DB function `create_or_get_lead_from_call`.
    """
    result = await db.execute(
        text("SELECT create_or_get_lead_from_call(:caller, :agent)"),
        {"caller": caller_number, "agent": agent_number},
    )
    import json
    raw = result.scalar()
    if isinstance(raw, str):
        return json.loads(raw)
    return dict(raw) if raw else {"success": False, "error": "no_result"}


# ── Specialty Views ──────────────────────────────────────────────────


async def list_fresh_leads(
    db: AsyncSession, page: int = 1, size: int = 20
) -> tuple[list[Lead], int]:
    """Fresh leads: status='Lead creation', no follow_up, fresh=true."""
    condition = Lead.fresh.is_(True)
    count_stmt = select(func.count()).select_from(Lead).where(condition)
    total = (await db.execute(count_stmt)).scalar()

    stmt = (
        select(Lead)
        .where(condition)
        .order_by(Lead.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    result = await db.execute(stmt)
    return result.scalars().all(), total


async def list_backlog_leads(
    db: AsyncSession, page: int = 1, size: int = 20
) -> tuple[list[Lead], int]:
    """Backlog leads: assigned_to IS NULL."""
    condition = Lead.assigned_to.is_(None)
    count_stmt = select(func.count()).select_from(Lead).where(condition)
    total = (await db.execute(count_stmt)).scalar()

    stmt = (
        select(Lead)
        .where(condition)
        .order_by(Lead.created_at.asc())
        .offset((page - 1) * size)
        .limit(size)
    )
    result = await db.execute(stmt)
    return result.scalars().all(), total


async def list_bin_leads(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    start_date: str | None = None,
    end_date: str | None = None,
) -> tuple[list[Lead], int]:
    """Bin/trash leads: lead_type='Office Enquiry' OR status='Lead trashed'."""
    from sqlalchemy import or_

    condition = or_(
        func.lower(Lead.lead_type) == "office enquiry",
        func.lower(Lead.status) == "lead trashed",
    )
    count_stmt = select(func.count()).select_from(Lead).where(condition)

    stmt = select(Lead).where(condition)

    if start_date and end_date:
        stmt = stmt.where(Lead.date.between(start_date, end_date))
        count_stmt = count_stmt.where(Lead.date.between(start_date, end_date))

    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.order_by(Lead.date.asc(), Lead.created_at.asc()).offset((page - 1) * size).limit(size)
    result = await db.execute(stmt)
    return result.scalars().all(), total


# ── Assignment Tracker ───────────────────────────────────────────────


async def get_assignment_tracker(db: AsyncSession) -> LeadAssignmentTracker:
    result = await db.execute(
        select(LeadAssignmentTracker).where(LeadAssignmentTracker.id == 1)
    )
    tracker = result.scalar_one_or_none()
    if not tracker:
        raise NotFoundError("Assignment tracker not found")
    return tracker


# ── Lead Stats ───────────────────────────────────────────────────────


async def get_lead_stats(db: AsyncSession) -> dict:
    """Quick stats: total, fresh, backlog, by heat_status."""
    total = (await db.execute(select(func.count()).select_from(Lead))).scalar()
    fresh = (
        await db.execute(
            select(func.count()).select_from(Lead).where(Lead.fresh.is_(True))
        )
    ).scalar()
    backlog = (
        await db.execute(
            select(func.count()).select_from(Lead).where(Lead.assigned_to.is_(None))
        )
    ).scalar()

    heat_result = await db.execute(
        select(Lead.heat_status, func.count())
        .group_by(Lead.heat_status)
    )
    by_heat = {row[0] or "unset": row[1] for row in heat_result.all()}

    status_result = await db.execute(
        select(Lead.status, func.count())
        .group_by(Lead.status)
    )
    by_status = {row[0] or "unset": row[1] for row in status_result.all()}

    return {
        "total": total,
        "fresh": fresh,
        "backlog": backlog,
        "by_heat_status": by_heat,
        "by_status": by_status,
    }


# ── Follow-Up / Date-Filtered Views ─────────────────────────────────


async def list_follow_up_leads(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    assigned_to: str | None = None,
    start: str | None = None,
    end: str | None = None,
    lead_tab: str | None = None,
) -> tuple[list[Lead], int]:
    """Leads with follow_up date in range, excluding 100% completed."""
    from sqlalchemy import and_, cast, String

    from datetime import datetime as dt

    conditions = [Lead.date.isnot(None)]

    if assigned_to:
        conditions.append(Lead.assigned_to == assigned_to)
    if start:
        conditions.append(Lead.date >= dt.fromisoformat(start))
    if end:
        conditions.append(Lead.date <= dt.fromisoformat(end))
    if lead_tab:
        conditions.append(Lead.lead_tab == lead_tab)

    # Exclude leads where info_progress indicates 100% complete
    # info_progress is TEXT — may contain JSON like {"percentage": 100}
    conditions.append(
        func.coalesce(Lead.info_progress, "").op("NOT LIKE")("%100%")
    )

    where = and_(*conditions)
    count_stmt = select(func.count()).select_from(Lead).where(where)
    total = (await db.execute(count_stmt)).scalar()

    stmt = (
        select(Lead)
        .where(where)
        .order_by(Lead.date.asc())
        .offset((page - 1) * size)
        .limit(size)
    )
    result = await db.execute(stmt)
    return result.scalars().all(), total


async def list_new_enquiry_leads(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    assigned_to: str | None = None,
    start: str | None = None,
    end: str | None = None,
    lead_tab: str | None = None,
) -> tuple[list[Lead], int]:
    """Leads created in date range for a specific assignee."""
    from datetime import datetime as dt

    from sqlalchemy import and_

    conditions = []

    if assigned_to:
        conditions.append(Lead.assigned_to == assigned_to)
    if start:
        conditions.append(Lead.created_at >= dt.fromisoformat(start))
    if end:
        conditions.append(Lead.created_at <= dt.fromisoformat(end))
    if lead_tab:
        conditions.append(Lead.lead_tab == lead_tab)

    where = and_(*conditions) if conditions else True
    count_stmt = select(func.count()).select_from(Lead).where(where)
    total = (await db.execute(count_stmt)).scalar()

    stmt = (
        select(Lead)
        .where(where)
        .order_by(Lead.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    result = await db.execute(stmt)
    return result.scalars().all(), total


async def list_draft_leads(
    db: AsyncSession,
    page: int = 1,
    size: int = 50,
) -> tuple[list[Lead], int]:
    """Leads with draft_status in (draft, DRAFT)."""
    condition = func.lower(Lead.draft_status) == "draft"
    count_stmt = select(func.count()).select_from(Lead).where(condition)
    total = (await db.execute(count_stmt)).scalar()

    stmt = (
        select(Lead)
        .where(condition)
        .order_by(Lead.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    result = await db.execute(stmt)
    return result.scalars().all(), total


async def list_completed_leads(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    assigned_to: str | None = None,
    lead_tab: str | None = None,
) -> tuple[list[Lead], int]:
    """Leads with info_progress percentage = 100."""
    from sqlalchemy import and_

    conditions = [Lead.info_progress.ilike("%100%")]

    if assigned_to:
        conditions.append(Lead.assigned_to == assigned_to)
    if lead_tab:
        conditions.append(Lead.lead_tab == lead_tab)

    where = and_(*conditions)
    count_stmt = select(func.count()).select_from(Lead).where(where)
    total = (await db.execute(count_stmt)).scalar()

    stmt = (
        select(Lead)
        .where(where)
        .order_by(Lead.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    result = await db.execute(stmt)
    return result.scalars().all(), total


async def list_study_abroad_leads(
    db: AsyncSession,
    page: int = 1,
    size: int = 50,
    lead_tab: str | None = "student",
) -> tuple[list[Lead], int]:
    """Study abroad leads — excludes trashed statuses and bad lead types."""
    from sqlalchemy import and_, or_

    trashed_statuses = ["lead trashed", "office enquiry"]
    conditions = [
        ~func.lower(func.coalesce(Lead.status, "")).in_(trashed_statuses),
        ~func.lower(func.coalesce(Lead.lead_type, "")).in_(["office enquiry"]),
    ]

    if lead_tab:
        conditions.append(Lead.lead_tab == lead_tab)

    where = and_(*conditions)
    count_stmt = select(func.count()).select_from(Lead).where(where)
    total = (await db.execute(count_stmt)).scalar()

    stmt = (
        select(Lead)
        .where(where)
        .order_by(Lead.fresh.desc(), Lead.date.asc(), Lead.created_at.asc())
        .offset((page - 1) * size)
        .limit(size)
    )
    result = await db.execute(stmt)
    return result.scalars().all(), total


async def count_leads(
    db: AsyncSession,
    assigned_to: str | None = None,
    lead_tab: str | None = None,
    start: str | None = None,
    end: str | None = None,
) -> int:
    """Count matching leads (for dashboard counters)."""
    from datetime import datetime as dt

    from sqlalchemy import and_

    conditions = []

    if assigned_to:
        conditions.append(Lead.assigned_to == assigned_to)
    if lead_tab:
        conditions.append(Lead.lead_tab == lead_tab)
    if start:
        conditions.append(Lead.created_at >= dt.fromisoformat(start))
    if end:
        conditions.append(Lead.created_at <= dt.fromisoformat(end))

    where = and_(*conditions) if conditions else True
    count_stmt = select(func.count()).select_from(Lead).where(where)
    return (await db.execute(count_stmt)).scalar()


# ── Batch Profile Lookup ──────────────────────────────────────────────


async def batch_get_profiles_by_user_ids(
    db: AsyncSession, user_ids: list[str]
) -> list[dict]:
    """Batch fetch profiles by user_id strings (UUID strings from leadslist.user_id → profiles)."""
    if not user_ids:
        return []
    from app.modules.profiles.models import Profile
    result = await db.execute(
        select(Profile).where(Profile.id.in_(user_ids))
    )
    profiles = result.scalars().all()
    return [
        {
            "id": str(p.id),
            "diplay_name": p.diplay_name,
            "profilepicture": p.profilepicture,
            "designation": p.designation,
            "email": p.email,
            "phone": p.phone,
            "user_type": p.user_type,
            "countries": p.countries,
            "fcm_token": p.fcm_token,
        }
        for p in profiles
    ]
