from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.pagination import PaginatedResponse, paginate_metadata
from app.database import get_db
from app.dependencies import require_perm
from app.modules.ig_sessions.models import ConversationSession, DMTemplate
from app.modules.ig_sessions.schemas import ConversationSessionOut, DMTemplateOut
from app.modules.users.models import User

router = APIRouter(prefix="/ig-sessions", tags=["IG Sessions"])


@router.get("/sessions", response_model=PaginatedResponse[ConversationSessionOut])
async def api_list_sessions(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    ig_user_id: str | None = None,
    current_user: User = Depends(require_perm("ig_sessions", "read")),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ConversationSession)
    count_stmt = select(func.count()).select_from(ConversationSession)

    if status:
        stmt = stmt.where(ConversationSession.status == status)
        count_stmt = count_stmt.where(ConversationSession.status == status)
    if ig_user_id:
        stmt = stmt.where(ConversationSession.ig_user_id == ig_user_id)
        count_stmt = count_stmt.where(ConversationSession.ig_user_id == ig_user_id)

    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.offset((page - 1) * size).limit(size).order_by(ConversationSession.created_at.desc())
    result = await db.execute(stmt)
    return {**paginate_metadata(total, page, size), "items": result.scalars().all()}


@router.get("/sessions/{session_id}", response_model=ConversationSessionOut)
async def api_get_session(
    session_id: UUID,
    current_user: User = Depends(require_perm("ig_sessions", "read")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ConversationSession).where(ConversationSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise NotFoundError("Conversation session not found")
    return session


@router.get("/templates", response_model=list[DMTemplateOut])
async def api_list_templates(
    current_user: User = Depends(require_perm("ig_sessions", "read")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DMTemplate).order_by(DMTemplate.created_at.desc())
    )
    return result.scalars().all()
