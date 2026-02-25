from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import PaginatedResponse, paginate_metadata
from app.database import get_db
from app.dependencies import require_perm
from app.modules.chat import service
from app.modules.chat.schemas import ChatConversationOut, ChatMessageOut
from app.modules.users.models import User

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.get("/conversations", response_model=PaginatedResponse[ChatConversationOut])
async def api_list_conversations(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    counselor_id: str | None = None,
    lead_uuid: str | None = None,
    current_user: User = Depends(require_perm("chat", "read")),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_conversations(db, page, size, counselor_id, lead_uuid)
    return {**paginate_metadata(total, page, size), "items": items}


@router.get("/conversations/{conversation_id}", response_model=ChatConversationOut)
async def api_get_conversation(
    conversation_id: int,
    current_user: User = Depends(require_perm("chat", "read")),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_conversation(db, conversation_id)


@router.get("/conversations/{conversation_id}/messages", response_model=PaginatedResponse[ChatMessageOut])
async def api_list_messages(
    conversation_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_perm("chat", "read")),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_messages(db, conversation_id, page, size)
    return {**paginate_metadata(total, page, size), "items": items}
