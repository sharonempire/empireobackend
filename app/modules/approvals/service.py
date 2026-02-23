from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, NotFoundError
from app.modules.approvals.models import ActionDraft


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
