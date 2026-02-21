from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.database import get_db
from app.dependencies import get_current_user
from app.modules.approvals.service import ApprovalService
from app.modules.approvals.schemas import ActionDraftOut, ActionDraftCreate, ApprovalDecision
from app.modules.users.models import User
from app.core.pagination import PaginatedResponse

router = APIRouter()


@router.get("/pending", response_model=PaginatedResponse[ActionDraftOut])
async def list_pending(page: int = Query(1), size: int = Query(20),
                       db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    svc = ApprovalService(db)
    items, total = await svc.list_pending(page, size)
    return PaginatedResponse(items=items, total=total, page=page, size=size, pages=(total + size - 1) // size)


@router.post("", response_model=ActionDraftOut, status_code=201)
async def create_draft(data: ActionDraftCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await ApprovalService(db).create_draft(data, "user", user.id)


@router.post("/{draft_id}/decide", response_model=ActionDraftOut)
async def decide(draft_id: UUID, data: ApprovalDecision, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await ApprovalService(db).decide(draft_id, data, approver_id=user.id)
