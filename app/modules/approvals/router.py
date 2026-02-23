from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import log_event
from app.core.pagination import PaginatedResponse, paginate_metadata
from app.database import get_db
from app.dependencies import get_current_user, require_perm
from app.modules.approvals.schemas import ActionDraftOut, ReviewRequest
from app.modules.approvals.service import get_draft, list_drafts, review_draft
from app.modules.users.models import User

router = APIRouter(prefix="/approvals", tags=["Approvals"])


@router.get("/", response_model=PaginatedResponse[ActionDraftOut])
async def api_list_drafts(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: str | None = "pending_approval",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    drafts, total = await list_drafts(db, page, size, status)
    return {**paginate_metadata(total, page, size), "items": drafts}


@router.get("/{draft_id}", response_model=ActionDraftOut)
async def api_get_draft(
    draft_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_draft(db, draft_id)


@router.post("/{draft_id}/review", response_model=ActionDraftOut)
async def api_review_draft(
    draft_id: UUID,
    data: ReviewRequest,
    current_user: User = Depends(require_perm("approvals", "review")),
    db: AsyncSession = Depends(get_db),
):
    draft = await review_draft(db, draft_id, data.action, current_user.id, data.rejection_reason)
    await log_event(
        db, f"approval.{data.action}d", current_user.id, "action_draft", draft.id,
        {"action_type": draft.action_type},
    )
    await db.commit()
    return draft
