from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import PaginatedResponse, paginate_metadata
from app.database import get_db
from app.dependencies import get_current_user, require_perm
from app.modules.ig_sessions import service
from app.modules.ig_sessions.schemas import ConversationSessionOut, DMTemplateOut
from app.modules.users.models import User

router = APIRouter(prefix="/ig-sessions", tags=["IG Sessions"])


@router.get("/sessions", response_model=PaginatedResponse[ConversationSessionOut])
async def api_list_sessions(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=500),
    status: str | None = None,
    ig_user_id: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_sessions(db, page, size, status, ig_user_id)
    return {**paginate_metadata(total, page, size), "items": items}


@router.get("/sessions/{session_id}", response_model=ConversationSessionOut)
async def api_get_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_session(db, session_id)


@router.get("/templates", response_model=list[DMTemplateOut])
async def api_list_templates(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await service.list_templates(db)
