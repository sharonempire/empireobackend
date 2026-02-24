from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.pagination import PaginatedResponse, paginate_metadata
from app.database import get_db
from app.dependencies import require_perm
from app.modules.chat.models import ChatConversation, ChatMessage
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
    stmt = select(ChatConversation)
    count_stmt = select(func.count()).select_from(ChatConversation)

    if counselor_id:
        stmt = stmt.where(ChatConversation.counselor_id == counselor_id)
        count_stmt = count_stmt.where(ChatConversation.counselor_id == counselor_id)
    if lead_uuid:
        stmt = stmt.where(ChatConversation.lead_uuid == lead_uuid)
        count_stmt = count_stmt.where(ChatConversation.lead_uuid == lead_uuid)

    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.offset((page - 1) * size).limit(size).order_by(ChatConversation.updated_at.desc())
    result = await db.execute(stmt)
    return {**paginate_metadata(total, page, size), "items": result.scalars().all()}


@router.get("/conversations/{conversation_id}", response_model=ChatConversationOut)
async def api_get_conversation(
    conversation_id: int,
    current_user: User = Depends(require_perm("chat", "read")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ChatConversation).where(ChatConversation.id == conversation_id))
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise NotFoundError("Conversation not found")
    return conversation


@router.get("/conversations/{conversation_id}/messages", response_model=PaginatedResponse[ChatMessageOut])
async def api_list_messages(
    conversation_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_perm("chat", "read")),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ChatMessage).where(ChatMessage.conversation_id == conversation_id)
    count_stmt = select(func.count()).select_from(ChatMessage).where(ChatMessage.conversation_id == conversation_id)

    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.offset((page - 1) * size).limit(size).order_by(ChatMessage.created_at.asc())
    result = await db.execute(stmt)
    return {**paginate_metadata(total, page, size), "items": result.scalars().all()}
