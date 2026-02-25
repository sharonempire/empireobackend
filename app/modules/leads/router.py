from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import log_event
from app.core.pagination import PaginatedResponse, paginate_metadata
from app.database import get_db
from app.dependencies import require_perm
from app.modules.leads import service
from app.modules.leads.schemas import (
    AssignmentTrackerOut,
    LeadCreate,
    LeadDetailOut,
    LeadInfoOut,
    LeadInfoUpdate,
    LeadIntake,
    LeadOut,
    LeadReassign,
    LeadRedistribute,
    LeadUpdate,
)
from app.modules.users.models import User

router = APIRouter(prefix="/leads", tags=["Leads"])


# ── List / Search ────────────────────────────────────────────────────


@router.get("/", response_model=PaginatedResponse[LeadOut])
async def api_list_leads(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    status: str | None = None,
    heat_status: str | None = None,
    lead_tab: str | None = None,
    assigned_to: str | None = None,
    current_user: User = Depends(require_perm("leads", "read")),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_leads(db, page, size, search, status, heat_status, lead_tab, assigned_to)
    return {**paginate_metadata(total, page, size), "items": items}


# ── Specialty Views ──────────────────────────────────────────────────


@router.get("/fresh", response_model=PaginatedResponse[LeadOut])
async def api_list_fresh_leads(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_perm("leads", "read")),
    db: AsyncSession = Depends(get_db),
):
    """Fresh leads — new, uncontacted, no follow-up set."""
    items, total = await service.list_fresh_leads(db, page, size)
    return {**paginate_metadata(total, page, size), "items": items}


@router.get("/backlog", response_model=PaginatedResponse[LeadOut])
async def api_list_backlog_leads(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_perm("leads", "read")),
    db: AsyncSession = Depends(get_db),
):
    """Backlog leads — unassigned, waiting for staff check-in."""
    items, total = await service.list_backlog_leads(db, page, size)
    return {**paginate_metadata(total, page, size), "items": items}


@router.get("/bin", response_model=PaginatedResponse[LeadOut])
async def api_list_bin_leads(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    start_date: str | None = None,
    end_date: str | None = None,
    current_user: User = Depends(require_perm("leads", "read")),
    db: AsyncSession = Depends(get_db),
):
    """Bin/trashed leads — office enquiry or lead trashed."""
    items, total = await service.list_bin_leads(db, page, size, start_date, end_date)
    return {**paginate_metadata(total, page, size), "items": items}


@router.get("/stats")
async def api_lead_stats(
    current_user: User = Depends(require_perm("leads", "read")),
    db: AsyncSession = Depends(get_db),
):
    """Quick stats: total, fresh, backlog, breakdown by heat/status."""
    return await service.get_lead_stats(db)


@router.get("/assignment-tracker", response_model=AssignmentTrackerOut)
async def api_assignment_tracker(
    current_user: User = Depends(require_perm("leads", "read")),
    db: AsyncSession = Depends(get_db),
):
    """Current round-robin assignment tracker state."""
    return await service.get_assignment_tracker(db)


# ── Counselor Scoring (for auto-assignment debugging) ────────────────


@router.get("/auto-assign/scores")
async def api_counselor_scores(
    country_preference: str | None = Query(None, description="Comma-separated country names"),
    current_user: User = Depends(require_perm("leads", "read")),
    db: AsyncSession = Depends(get_db),
):
    """View counselor scoring for auto-assignment debugging.

    Returns ranked list of counselors with their scores and workload.
    """
    from app.core.auto_assign import score_counselors

    countries = [c.strip() for c in country_preference.split(",")] if country_preference else None
    scores = await score_counselors(db, countries)
    return {"counselors": scores, "country_filter": countries}


# ── Single Lead ──────────────────────────────────────────────────────


@router.get("/{lead_id}", response_model=LeadDetailOut)
async def api_get_lead(
    lead_id: int,
    current_user: User = Depends(require_perm("leads", "read")),
    db: AsyncSession = Depends(get_db),
):
    lead = await service.get_lead(db, lead_id)
    lead_info = await service.get_lead_info(db, lead_id)

    lead_data = LeadOut.model_validate(lead).model_dump()
    lead_data["lead_info"] = LeadInfoOut.model_validate(lead_info) if lead_info else None
    return LeadDetailOut(**lead_data)


# ── Create Lead ──────────────────────────────────────────────────────
# DB triggers auto-handle: round-robin assignment, duplicate blocking,
# phone normalization, fresh flag, date, lead_info row, chat conversation


@router.post("/", response_model=LeadOut, status_code=201)
async def api_create_lead(
    data: LeadCreate,
    current_user: User = Depends(require_perm("leads", "create")),
    db: AsyncSession = Depends(get_db),
):
    lead = await service.create_lead(db, data)
    await log_event(db, "lead.created", current_user.id, "lead", str(lead.id), {
        "name": lead.name, "source": lead.source, "assigned_to": str(lead.assigned_to) if lead.assigned_to else None,
    })
    await db.commit()
    return lead


# ── Update Lead ──────────────────────────────────────────────────────


@router.patch("/{lead_id}", response_model=LeadOut)
async def api_update_lead(
    lead_id: int,
    data: LeadUpdate,
    current_user: User = Depends(require_perm("leads", "update")),
    db: AsyncSession = Depends(get_db),
):
    lead = await service.update_lead(db, lead_id, data)
    await log_event(db, "lead.updated", current_user.id, "lead", str(lead_id), data.model_dump(exclude_unset=True))
    await db.commit()
    return lead


# ── Update Lead Info ─────────────────────────────────────────────────


@router.patch("/{lead_id}/info", response_model=LeadInfoOut)
async def api_update_lead_info(
    lead_id: int,
    data: LeadInfoUpdate,
    current_user: User = Depends(require_perm("leads", "update")),
    db: AsyncSession = Depends(get_db),
):
    info = await service.update_lead_info(db, lead_id, data)
    await log_event(db, "lead_info.updated", current_user.id, "lead", str(lead_id), {
        "fields_updated": list(data.model_dump(exclude_unset=True).keys()),
    })
    await db.commit()
    return info


# ── Reassign Lead ────────────────────────────────────────────────────


@router.post("/{lead_id}/reassign", response_model=LeadOut)
async def api_reassign_lead(
    lead_id: int,
    data: LeadReassign,
    current_user: User = Depends(require_perm("leads", "update")),
    db: AsyncSession = Depends(get_db),
):
    """Manually reassign a lead to a different counselor."""
    lead = await service.reassign_lead(db, lead_id, data.assigned_to)
    await log_event(db, "lead.reassigned", current_user.id, "lead", str(lead_id), {
        "new_assignee": str(data.assigned_to),
    })
    await db.commit()
    return lead


# ── Redistribute Leads ───────────────────────────────────────────────


@router.post("/redistribute")
async def api_redistribute_leads(
    data: LeadRedistribute,
    current_user: User = Depends(require_perm("leads", "update")),
    db: AsyncSession = Depends(get_db),
):
    """Redistribute N leads from one counselor to others via round-robin."""
    moved = await service.redistribute_leads(db, data.source_counselor_id, data.leads_to_move)
    await log_event(db, "lead.redistributed", current_user.id, "lead", "bulk", {
        "source_counselor": str(data.source_counselor_id),
        "leads_moved": moved,
    })
    await db.commit()
    return {"moved": moved, "source_counselor": str(data.source_counselor_id)}


# ── Create Lead from Call ────────────────────────────────────────────


@router.post("/from-call")
async def api_create_lead_from_call(
    caller_number: str,
    agent_number: str | None = None,
    current_user: User = Depends(require_perm("leads", "create")),
    db: AsyncSession = Depends(get_db),
):
    """Find or create a lead from an incoming phone call.
    Uses the DB function that matches caller by phone and agent by extension.
    """
    result = await service.create_or_get_lead_from_call(db, caller_number, agent_number)
    if result.get("success"):
        await log_event(db, "lead.from_call", current_user.id, "lead", str(result.get("lead_id")), {
            "caller_number": caller_number, "agent_number": agent_number,
        })
    await db.commit()
    return result


# ── Lead Intake Pipeline ─────────────────────────────────────────────
# Mirrors Supabase Edge Function `eb-lead-intake` (v2)


@router.post("/intake", status_code=201)
async def api_lead_intake(
    data: LeadIntake,
    current_user: User = Depends(require_perm("leads", "create")),
    db: AsyncSession = Depends(get_db),
):
    """Full lead intake pipeline — creates lead, student, auto-assigns counselor.

    Mirrors the eb-lead-intake Edge Function. Orchestrates:
    1. Create lead (DB triggers: duplicate block, phone norm, round-robin, fresh flag)
    2. Update lead_info with detailed data
    3. Create eb_student (DB trigger: auto-creates eb_case)
    4. Smart auto-assign counselor (country scoring from eb-auto-assign)
    5. Verify chat conversation was created
    """
    from app.core.lead_intake import run_lead_intake

    result = await run_lead_intake(db, data.model_dump(exclude_unset=True))
    if result.get("success"):
        await log_event(db, "lead.intake_completed", current_user.id, "lead", str(result.get("lead_id")), {
            "source": data.source,
            "student_id": result.get("student_id"),
            "counselor_id": result.get("counselor_id"),
        })
    await db.commit()
    return result


# ── Auto-Assign Counselor ────────────────────────────────────────────
# Mirrors Supabase Edge Function `eb-auto-assign` (v2)


@router.post("/{lead_id}/auto-assign")
async def api_auto_assign_lead(
    lead_id: int,
    current_user: User = Depends(require_perm("leads", "update")),
    db: AsyncSession = Depends(get_db),
):
    """Smart auto-assign a counselor to a lead based on country match + workload scoring.

    Scoring: +30 country match, -2 per active case, +10 counselor role bonus.
    """
    from app.core.auto_assign import auto_assign_counselor

    lead = await service.get_lead(db, lead_id)
    counselor_id = await auto_assign_counselor(db, lead.country_preference)

    if not counselor_id:
        return {"lead_id": lead_id, "status": "no_counselors_available"}

    lead.assigned_to = counselor_id
    await db.flush()

    from app.modules.users.models import User as UserModel

    from sqlalchemy import select
    counselor_result = await db.execute(select(UserModel).where(UserModel.id == counselor_id))
    counselor = counselor_result.scalar_one_or_none()

    await log_event(db, "lead.auto_assigned", current_user.id, "lead", str(lead_id), {
        "counselor_id": str(counselor_id),
        "counselor_name": counselor.full_name if counselor else "Unknown",
    })
    await db.commit()

    return {
        "lead_id": lead_id,
        "counselor_id": str(counselor_id),
        "counselor_name": counselor.full_name if counselor else "Unknown",
        "status": "assigned",
    }


