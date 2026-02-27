"""Chat service layer."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.chat.models import ChatConversation, ChatMessage


async def list_conversations(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    counselor_id: str | None = None,
    lead_uuid: str | None = None,
) -> tuple[list[ChatConversation], int]:
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
    return result.scalars().all(), total


async def get_conversation(db: AsyncSession, conversation_id: UUID) -> ChatConversation:
    result = await db.execute(
        select(ChatConversation).where(ChatConversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise NotFoundError("Conversation not found")
    return conversation


async def list_messages(
    db: AsyncSession,
    conversation_id: UUID,
    page: int = 1,
    size: int = 50,
) -> tuple[list[ChatMessage], int]:
    stmt = select(ChatMessage).where(ChatMessage.conversation_id == conversation_id)
    count_stmt = (
        select(func.count())
        .select_from(ChatMessage)
        .where(ChatMessage.conversation_id == conversation_id)
    )
    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.offset((page - 1) * size).limit(size).order_by(ChatMessage.created_at.asc())
    result = await db.execute(stmt)
    return result.scalars().all(), total


async def update_conversation(db: AsyncSession, conversation_id: UUID, data) -> ChatConversation:
    result = await db.execute(
        select(ChatConversation).where(ChatConversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise NotFoundError("Conversation not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(conversation, field, value)
    await db.flush()
    return conversation


async def send_message(db: AsyncSession, data: dict) -> ChatMessage:
    """Send a chat message. DB trigger `update_conversation_on_message`
    auto-updates the conversation's last_message_text, last_message_at,
    and increments unread_count.
    """
    msg = ChatMessage(**data)
    db.add(msg)
    await db.flush()
    await db.refresh(msg)
    return msg


async def mark_messages_read(
    db: AsyncSession, conversation_id: UUID, user_id: str
) -> int:
    """Mark all unread messages in a conversation as read for a given user."""
    from datetime import datetime, timezone

    from sqlalchemy import update

    now = datetime.now(timezone.utc)
    stmt = (
        update(ChatMessage)
        .where(
            ChatMessage.conversation_id == conversation_id,
            ChatMessage.receiver_id == user_id,
            ChatMessage.is_read != True,  # noqa: E712
        )
        .values(is_read=True, read_at=now)
    )
    result = await db.execute(stmt)
    return result.rowcount


async def get_or_create_conversation(
    db: AsyncSession, counselor_id: str, lead_uuid: str
) -> dict:
    """Get or create a chat conversation using DB function."""
    from sqlalchemy import text

    result = await db.execute(
        text("SELECT * FROM get_or_create_conversation(:counselor, :lead)"),
        {"counselor": counselor_id, "lead": lead_uuid},
    )
    row = result.first()
    return dict(row._mapping) if row else {}
