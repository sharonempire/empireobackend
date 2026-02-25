import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, NotFoundError
from app.modules.approvals.models import ActionDraft, ActionRun

logger = logging.getLogger("empireo.approvals")


async def list_drafts(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    status: str | None = "pending_approval",
) -> tuple[list[ActionDraft], int]:
    stmt = select(ActionDraft)
    count_stmt = select(func.count()).select_from(ActionDraft)

    if status:
        stmt = stmt.where(ActionDraft.status == status)
        count_stmt = count_stmt.where(ActionDraft.status == status)

    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.offset((page - 1) * size).limit(size).order_by(ActionDraft.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all(), total


async def get_draft(db: AsyncSession, draft_id: UUID) -> ActionDraft:
    result = await db.execute(select(ActionDraft).where(ActionDraft.id == draft_id))
    draft = result.scalar_one_or_none()
    if not draft:
        raise NotFoundError("Action draft not found")
    return draft


async def review_draft(db: AsyncSession, draft_id: UUID, action: str, reviewer_id: UUID, rejection_reason: str | None = None) -> ActionDraft:
    draft = await get_draft(db, draft_id)
    if draft.status != "pending_approval":
        raise BadRequestError("Draft is not pending approval")

    if action == "approve":
        draft.status = "approved"
        draft.approved_by = reviewer_id
        draft.approved_at = datetime.now(timezone.utc)
    elif action == "reject":
        draft.status = "rejected"
        draft.approved_by = reviewer_id
        draft.approved_at = datetime.now(timezone.utc)
        draft.rejection_reason = rejection_reason
    else:
        raise BadRequestError("Action must be 'approve' or 'reject'")

    await db.flush()
    return draft


async def execute_draft(db: AsyncSession, draft_id: UUID, executor_id: UUID) -> ActionRun:
    """Execute an approved action draft."""
    draft = await get_draft(db, draft_id)

    if draft.status != "approved":
        raise BadRequestError("Only approved drafts can be executed")

    # Create the ActionRun record
    run = ActionRun(
        action_draft_id=draft.id,
        action_type=draft.action_type,
        status="started",
        started_at=datetime.now(timezone.utc),
    )
    db.add(run)
    await db.flush()

    try:
        result = await _dispatch_action(db, draft)
        run.status = "completed"
        run.completed_at = datetime.now(timezone.utc)
        run.result = result
        draft.status = "executed"
        draft.executed_at = datetime.now(timezone.utc)
        draft.execution_result = result
    except Exception as exc:
        logger.exception("Action execution failed for draft %s", draft_id)
        run.status = "failed"
        run.completed_at = datetime.now(timezone.utc)
        run.error = str(exc)
        draft.status = "execution_failed"
        draft.execution_result = {"error": str(exc)}

    await db.flush()
    return run


async def _dispatch_action(db: AsyncSession, draft: ActionDraft) -> dict:
    """Route an action draft to the correct handler based on action_type."""
    payload = draft.payload or {}
    action_type = draft.action_type

    if action_type == "stage_transition":
        return await _execute_stage_transition(db, draft.entity_id, payload)
    elif action_type == "send_notification":
        return await _execute_send_notification(db, payload)
    elif action_type == "update_student":
        return await _execute_update_student(db, draft.entity_id, payload)
    elif action_type == "assign_counselor":
        return await _execute_assign_counselor(db, draft.entity_id, payload)
    else:
        raise BadRequestError(f"Unknown action_type: {action_type}")


async def _execute_stage_transition(db: AsyncSession, entity_id: UUID, payload: dict) -> dict:
    """Transition a case to a new stage."""
    from app.modules.cases.models import Case, VALID_STAGES

    result = await db.execute(select(Case).where(Case.id == entity_id))
    case = result.scalar_one_or_none()
    if not case:
        raise NotFoundError(f"Case {entity_id} not found")

    new_stage = payload.get("new_stage")
    if not new_stage:
        raise BadRequestError("Payload must include 'new_stage'")
    if new_stage not in VALID_STAGES:
        raise BadRequestError(f"Invalid stage: {new_stage}")

    old_stage = case.current_stage
    case.current_stage = new_stage
    await db.flush()

    return {"old_stage": old_stage, "new_stage": new_stage, "case_id": str(entity_id)}


async def _execute_send_notification(db: AsyncSession, payload: dict) -> dict:
    """Create a notification for the specified user."""
    from app.modules.notifications.models import Notification

    user_id = payload.get("user_id")
    title = payload.get("title", "Notification")
    message = payload.get("message", "")

    if not user_id:
        raise BadRequestError("Payload must include 'user_id'")

    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=payload.get("notification_type", "ai_action"),
        entity_type=payload.get("entity_type"),
        entity_id=payload.get("entity_id"),
    )
    db.add(notification)
    await db.flush()

    return {"notification_id": str(notification.id), "user_id": str(user_id)}


async def _execute_update_student(db: AsyncSession, entity_id: UUID, payload: dict) -> dict:
    """Update student fields from the payload."""
    from app.modules.students.models import Student

    result = await db.execute(select(Student).where(Student.id == entity_id))
    student = result.scalar_one_or_none()
    if not student:
        raise NotFoundError(f"Student {entity_id} not found")

    allowed_fields = {
        "full_name", "email", "phone", "nationality", "education_level",
        "english_test_type", "english_test_score", "preferred_countries",
        "preferred_programs", "work_experience_years",
    }
    updated = {}
    for field, value in payload.get("fields", {}).items():
        if field in allowed_fields:
            setattr(student, field, value)
            updated[field] = value

    if not updated:
        raise BadRequestError("No valid fields to update in payload")

    await db.flush()
    return {"student_id": str(entity_id), "updated_fields": updated}


async def _execute_assign_counselor(db: AsyncSession, entity_id: UUID, payload: dict) -> dict:
    """Assign a counselor to a case."""
    from app.modules.cases.models import Case

    result = await db.execute(select(Case).where(Case.id == entity_id))
    case = result.scalar_one_or_none()
    if not case:
        raise NotFoundError(f"Case {entity_id} not found")

    counselor_id = payload.get("counselor_id")
    if not counselor_id:
        raise BadRequestError("Payload must include 'counselor_id'")

    old_counselor_id = str(case.assigned_counselor_id) if case.assigned_counselor_id else None
    case.assigned_counselor_id = counselor_id
    await db.flush()

    return {
        "case_id": str(entity_id),
        "old_counselor_id": old_counselor_id,
        "new_counselor_id": str(counselor_id),
    }


async def create_ai_draft(
    db: AsyncSession,
    action_type: str,
    entity_type: str,
    entity_id: UUID,
    payload: dict,
    reason: str,
) -> ActionDraft:
    """Create a new action draft from an AI suggestion."""
    draft = ActionDraft(
        action_type=action_type,
        entity_type=entity_type,
        entity_id=entity_id,
        payload={**payload, "ai_reason": reason},
        created_by_type="ai",
        created_by_id=None,
        status="pending_approval",
        requires_approval=True,
    )
    db.add(draft)
    await db.flush()
    return draft
