from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import log_event
from app.core.pagination import PaginatedResponse, paginate_metadata
from app.core.websocket import broadcast_table_change
from app.database import get_db
from app.dependencies import get_current_user, require_perm
from app.modules.leads import service
from app.modules.leads.schemas import (
    AssignmentTrackerOut,
    LeadCreate,
    LeadDetailOut,
    LeadInfoBatchRequest,
    LeadInfoCreate,
    LeadInfoOut,
    LeadInfoUpdate,
    LeadIntake,
    LeadOut,
    LeadProfileBatchRequest,
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
    size: int = Query(20, ge=1, le=500),
    search: str | None = None,
    status: str | None = None,
    heat_status: str | None = None,
    lead_tab: str | None = None,
    assigned_to: str | None = None,
    user_id: str | None = Query(None, description="Filter by user_id field"),
    phone: str | None = Query(None, description="Filter by phone number"),
    start_date: str | None = Query(None, description="Filter created_at >= ISO date"),
    end_date: str | None = Query(None, description="Filter created_at <= ISO date"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_leads(
        db, page, size, search, status, heat_status, lead_tab, assigned_to,
        phone, start_date, end_date, user_id=user_id,
    )
    return {**paginate_metadata(total, page, size), "items": items}


# ── Specialty Views (MUST be before /{lead_id}) ──────────────────────


@router.get("/fresh", response_model=PaginatedResponse[LeadOut])
async def api_list_fresh_leads(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fresh leads — new, uncontacted, no follow-up set."""
    items, total = await service.list_fresh_leads(db, page, size)
    return {**paginate_metadata(total, page, size), "items": items}


@router.get("/backlog", response_model=PaginatedResponse[LeadOut])
async def api_list_backlog_leads(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Backlog leads — unassigned, waiting for staff check-in."""
    items, total = await service.list_backlog_leads(db, page, size)
    return {**paginate_metadata(total, page, size), "items": items}


@router.get("/bin", response_model=PaginatedResponse[LeadOut])
async def api_list_bin_leads(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=500),
    start_date: str | None = None,
    end_date: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Bin/trashed leads — office enquiry or lead trashed."""
    items, total = await service.list_bin_leads(db, page, size, start_date, end_date)
    return {**paginate_metadata(total, page, size), "items": items}


@router.get("/follow-ups", response_model=PaginatedResponse[LeadOut])
async def api_list_follow_up_leads(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=500),
    assigned_to: str | None = None,
    start: str | None = Query(None, description="ISO date start"),
    end: str | None = Query(None, description="ISO date end"),
    lead_tab: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Leads with follow_up date in range, excluding completed ones."""
    items, total = await service.list_follow_up_leads(db, page, size, assigned_to, start, end, lead_tab)
    return {**paginate_metadata(total, page, size), "items": items}


@router.get("/new-enquiries", response_model=PaginatedResponse[LeadOut])
async def api_list_new_enquiry_leads(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=500),
    assigned_to: str | None = None,
    start: str | None = Query(None, description="ISO date start"),
    end: str | None = Query(None, description="ISO date end"),
    lead_tab: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Leads created in date range for a specific assignee."""
    items, total = await service.list_new_enquiry_leads(db, page, size, assigned_to, start, end, lead_tab)
    return {**paginate_metadata(total, page, size), "items": items}


@router.get("/drafts", response_model=PaginatedResponse[LeadOut])
async def api_list_draft_leads(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Leads with draft_status in (draft, DRAFT)."""
    items, total = await service.list_draft_leads(db, page, size)
    return {**paginate_metadata(total, page, size), "items": items}


@router.get("/completed", response_model=PaginatedResponse[LeadOut])
async def api_list_completed_leads(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=500),
    assigned_to: str | None = None,
    lead_tab: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Leads with info_progress percentage = 100."""
    items, total = await service.list_completed_leads(db, page, size, assigned_to, lead_tab)
    return {**paginate_metadata(total, page, size), "items": items}


@router.get("/study-abroad", response_model=PaginatedResponse[LeadOut])
async def api_list_study_abroad_leads(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=500),
    lead_tab: str | None = "student",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Study abroad leads — excludes trashed statuses and bad lead types."""
    items, total = await service.list_study_abroad_leads(db, page, size, lead_tab)
    return {**paginate_metadata(total, page, size), "items": items}


@router.get("/count")
async def api_lead_count(
    assigned_to: str | None = None,
    lead_tab: str | None = None,
    start: str | None = Query(None, description="ISO date start"),
    end: str | None = Query(None, description="ISO date end"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Count matching leads (for dashboard counters)."""
    total = await service.count_leads(db, assigned_to, lead_tab, start, end)
    return {"count": total}


@router.get("/stats")
async def api_lead_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Quick stats: total, fresh, backlog, breakdown by heat/status."""
    return await service.get_lead_stats(db)


@router.get("/assignment-tracker", response_model=AssignmentTrackerOut)
async def api_assignment_tracker(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Current round-robin assignment tracker state."""
    return await service.get_assignment_tracker(db)


# ── Counselor Scoring (for auto-assignment debugging) ────────────────


@router.get("/auto-assign/scores")
async def api_counselor_scores(
    country_preference: str | None = Query(None, description="Comma-separated country names"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """View counselor scoring for auto-assignment debugging."""
    from app.core.auto_assign import score_counselors

    countries = [c.strip() for c in country_preference.split(",")] if country_preference else None
    scores = await score_counselors(db, countries)
    return {"counselors": scores, "country_filter": countries}


# ── Batch Lead Info ──────────────────────────────────────────────────


async def _batch_lead_info(data: LeadInfoBatchRequest, current_user, db):
    """Shared handler for batch lead_info fetch."""
    ids = data.ids or data.lead_ids or []
    if len(ids) > 100:
        from app.core.exceptions import BadRequestError
        raise BadRequestError("Maximum 100 lead IDs per batch request")
    return await service.batch_get_lead_infos(db, ids)


@router.post("/batch-info", response_model=list[LeadInfoOut])
async def api_batch_lead_info(
    data: LeadInfoBatchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Batch fetch lead_info records for multiple lead IDs (max 100).
    Accepts body: {"ids": [1,2,3]} or {"lead_ids": [1,2,3]}
    """
    return await _batch_lead_info(data, current_user, db)


@router.post("/info/batch", response_model=list[LeadInfoOut])
async def api_batch_lead_info_legacy(
    data: LeadInfoBatchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Legacy path alias for /batch-info."""
    return await _batch_lead_info(data, current_user, db)


# ── Batch Profile Lookup ────────────────────────────────────────────


@router.post("/batch-profiles")
async def api_batch_lead_profiles(
    data: LeadProfileBatchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Batch fetch profiles for multiple user UUIDs (max 100).
    Accepts body: {"user_ids": ["uuid1", "uuid2"]}
    """
    if len(data.user_ids) > 100:
        from app.core.exceptions import BadRequestError
        raise BadRequestError("Maximum 100 user IDs per batch request")
    return await service.batch_get_profiles_by_user_ids(db, data.user_ids)


# ── Single Lead ──────────────────────────────────────────────────────


@router.get("/{lead_id}", response_model=LeadDetailOut)
async def api_get_lead(
    lead_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    lead = await service.get_lead(db, lead_id)
    lead_info = await service.get_lead_info(db, lead_id)

    lead_data = LeadOut.model_validate(lead).model_dump()
    lead_data["lead_info"] = LeadInfoOut.model_validate(lead_info) if lead_info else None
    return LeadDetailOut(**lead_data)


# ── Lead Info (standalone) ───────────────────────────────────────────


@router.get("/{lead_id}/info", response_model=LeadInfoOut)
async def api_get_lead_info(
    lead_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get standalone lead_info record for a lead."""
    info = await service.get_lead_info(db, lead_id)
    if not info:
        from app.core.exceptions import NotFoundError
        raise NotFoundError(f"Lead info not found for lead {lead_id}")
    return info


@router.post("/{lead_id}/info", response_model=LeadInfoOut, status_code=201)
async def api_create_lead_info(
    lead_id: int,
    data: LeadInfoCreate,
    current_user: User = Depends(require_perm("leads", "create")),
    db: AsyncSession = Depends(get_db),
):
    """Create a lead_info record for a lead.
    Note: DB triggers normally auto-create lead_info on lead INSERT.
    This is for manual creation when needed.
    """
    info = await service.create_lead_info(db, lead_id, data)
    await log_event(db, "lead_info.created", current_user.id, "lead", str(lead_id), {
        "fields": list(data.model_dump(exclude_unset=True).keys()),
    })
    await db.commit()
    return info


# ── Applied Courses (for a lead) ─────────────────────────────────────


@router.get("/{lead_id}/applied-courses")
async def api_list_lead_applied_courses(
    lead_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch courses applied by a lead."""
    from app.modules.courses import service as course_service

    items, total = await course_service.list_applied_courses_for_lead(db, lead_id, page, size)
    return {**paginate_metadata(total, page, size), "items": items}


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
    await broadcast_table_change("leads", "INSERT", lead.id, {"name": lead.name})
    return lead


# ── Update Lead (PATCH + PUT) ────────────────────────────────────────


async def _update_lead(lead_id: int, data: LeadUpdate, current_user: User, db: AsyncSession):
    """Shared handler for PATCH and PUT lead updates."""
    lead = await service.update_lead(db, lead_id, data)
    await log_event(db, "lead.updated", current_user.id, "lead", str(lead_id), data.model_dump(exclude_unset=True))
    await db.commit()
    await broadcast_table_change("leads", "UPDATE", lead_id, data.model_dump(exclude_unset=True))
    return lead


@router.patch("/{lead_id}", response_model=LeadOut)
async def api_update_lead(
    lead_id: int,
    data: LeadUpdate,
    current_user: User = Depends(require_perm("leads", "update")),
    db: AsyncSession = Depends(get_db),
):
    """Partial update — only provided fields are changed."""
    return await _update_lead(lead_id, data, current_user, db)


@router.put("/{lead_id}", response_model=LeadOut)
async def api_update_lead_put(
    lead_id: int,
    data: LeadUpdate,
    current_user: User = Depends(require_perm("leads", "update")),
    db: AsyncSession = Depends(get_db),
):
    """PUT alias for PATCH — partial update, only provided fields are changed."""
    return await _update_lead(lead_id, data, current_user, db)


# ── Delete Lead ──────────────────────────────────────────────────────


@router.delete("/{lead_id}", status_code=204)
async def api_delete_lead(
    lead_id: int,
    current_user: User = Depends(require_perm("leads", "delete")),
    db: AsyncSession = Depends(get_db),
):
    """Delete a lead and its associated lead_info."""
    await service.delete_lead(db, lead_id)
    await log_event(db, "lead.deleted", current_user.id, "lead", str(lead_id), {})
    await db.commit()
    await broadcast_table_change("leads", "DELETE", lead_id, {})


# ── Update Lead Info (PATCH + PUT) ──────────────────────────────────


async def _update_lead_info(lead_id: int, data: LeadInfoUpdate, current_user: User, db: AsyncSession):
    """Shared handler for PATCH and PUT lead_info updates."""
    info = await service.update_lead_info(db, lead_id, data)
    await log_event(db, "lead_info.updated", current_user.id, "lead", str(lead_id), {
        "fields_updated": list(data.model_dump(exclude_unset=True).keys()),
    })
    await db.commit()
    await broadcast_table_change("lead_info", "UPDATE", lead_id, {
        "fields_updated": list(data.model_dump(exclude_unset=True).keys()),
    })
    return info


@router.patch("/{lead_id}/info", response_model=LeadInfoOut)
async def api_update_lead_info(
    lead_id: int,
    data: LeadInfoUpdate,
    current_user: User = Depends(require_perm("leads", "update")),
    db: AsyncSession = Depends(get_db),
):
    return await _update_lead_info(lead_id, data, current_user, db)


@router.put("/{lead_id}/info", response_model=LeadInfoOut)
async def api_update_lead_info_put(
    lead_id: int,
    data: LeadInfoUpdate,
    current_user: User = Depends(require_perm("leads", "update")),
    db: AsyncSession = Depends(get_db),
):
    """PUT alias for PATCH lead_info update."""
    return await _update_lead_info(lead_id, data, current_user, db)


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
    """Find or create a lead from an incoming phone call."""
    result = await service.create_or_get_lead_from_call(db, caller_number, agent_number)
    if result.get("success"):
        await log_event(db, "lead.from_call", current_user.id, "lead", str(result.get("lead_id")), {
            "caller_number": caller_number, "agent_number": agent_number,
        })
    await db.commit()
    return result


# ── Lead Intake Pipeline ─────────────────────────────────────────────


@router.post("/intake", status_code=201)
async def api_lead_intake(
    data: LeadIntake,
    current_user: User = Depends(require_perm("leads", "create")),
    db: AsyncSession = Depends(get_db),
):
    """Full lead intake pipeline — creates lead, student, auto-assigns counselor."""
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


@router.post("/{lead_id}/auto-assign")
async def api_auto_assign_lead(
    lead_id: int,
    current_user: User = Depends(require_perm("leads", "update")),
    db: AsyncSession = Depends(get_db),
):
    """Smart auto-assign a counselor to a lead based on country match + workload scoring."""
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
