from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import log_event
from app.core.pagination import PaginatedResponse, paginate_metadata
from app.database import get_db
from app.dependencies import require_perm
from app.modules.chat import service
from app.modules.chat.schemas import ChatConversationOut, ChatMessageCreate, ChatMessageOut
from app.modules.users.models import User

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.get("/conversations", response_model=PaginatedResponse[ChatConversationOut])
async def api_list_conversations(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=500),
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
    size: int = Query(50, ge=1, le=500),
    current_user: User = Depends(require_perm("chat", "read")),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_messages(db, conversation_id, page, size)
    return {**paginate_metadata(total, page, size), "items": items}


@router.post("/conversations/{conversation_id}/messages", response_model=ChatMessageOut, status_code=201)
async def api_send_message(
    conversation_id: int,
    data: ChatMessageCreate,
    current_user: User = Depends(require_perm("chat", "create")),
    db: AsyncSession = Depends(get_db),
):
    """Send a message. DB trigger auto-updates conversation metadata."""
    msg_data = data.model_dump()
    msg_data["conversation_id"] = conversation_id
    msg = await service.send_message(db, msg_data)
    await log_event(db, "chat.message_sent", current_user.id, "chat_message", str(msg.id), {
        "conversation_id": conversation_id,
    })
    await db.commit()
    return msg


@router.post("/conversations/{conversation_id}/read")
async def api_mark_read(
    conversation_id: int,
    current_user: User = Depends(require_perm("chat", "read")),
    db: AsyncSession = Depends(get_db),
):
    """Mark all messages in a conversation as read."""
    count = await service.mark_messages_read(db, conversation_id, str(current_user.id))
    await db.commit()
    return {"marked_read": count}


@router.post("/conversations/get-or-create")
async def api_get_or_create_conversation(
    counselor_id: str,
    lead_uuid: str,
    current_user: User = Depends(require_perm("chat", "create")),
    db: AsyncSession = Depends(get_db),
):
    """Get or create a conversation between a counselor and a lead."""
    result = await service.get_or_create_conversation(db, counselor_id, lead_uuid)
    await db.commit()
    return result
