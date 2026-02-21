from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.modules.approvals.models import ActionDraft
from app.modules.approvals.schemas import ActionDraftCreate, ApprovalDecision
from app.modules.events.service import EventService
from app.core.exceptions import NotFoundError, BadRequestError


class ApprovalService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.events = EventService(db)

    async def create_draft(self, data: ActionDraftCreate, creator_type: str, creator_id: UUID | None) -> ActionDraft:
        draft = ActionDraft(**data.model_dump(), created_by_type=creator_type, created_by_id=creator_id)
        if not data.requires_approval:
            draft.status = "approved"
            draft.approved_at = datetime.now(timezone.utc)
        self.db.add(draft)
        await self.db.flush()
        await self.events.log(
            "approval_requested" if data.requires_approval else "action_auto_approved",
            creator_type, creator_id, data.entity_type, data.entity_id,
            {"draft_id": str(draft.id), "action": data.action_type},
        )
        return draft

    async def list_pending(self, page=1, size=20):
        q = select(ActionDraft).where(ActionDraft.status == "pending_approval")
        total = (await self.db.execute(select(func.count()).select_from(q.subquery()))).scalar()
        q = q.offset((page - 1) * size).limit(size).order_by(ActionDraft.created_at.desc())
        result = await self.db.execute(q)
        return result.scalars().all(), total

    async def decide(self, draft_id: UUID, decision: ApprovalDecision, approver_id: UUID) -> ActionDraft:
        result = await self.db.execute(select(ActionDraft).where(ActionDraft.id == draft_id))
        draft = result.scalar_one_or_none()
        if not draft:
            raise NotFoundError("ActionDraft", str(draft_id))
        if draft.status != "pending_approval":
            raise BadRequestError(f"Draft is already {draft.status}")
        now = datetime.now(timezone.utc)
        if decision.approved:
            draft.status = "approved"
            draft.approved_by = approver_id
            draft.approved_at = now
            await self.events.log("approval_granted", "user", approver_id, draft.entity_type, draft.entity_id,
                                  {"draft_id": str(draft.id)})
        else:
            draft.status = "rejected"
            draft.rejection_reason = decision.reason
            await self.events.log("approval_rejected", "user", approver_id, draft.entity_type, draft.entity_id,
                                  {"draft_id": str(draft.id), "reason": decision.reason})
        await self.db.flush()
        return draft
