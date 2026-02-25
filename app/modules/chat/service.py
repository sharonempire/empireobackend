"""Chat service layer."""

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


async def get_conversation(db: AsyncSession, conversation_id: int) -> ChatConversation:
    result = await db.execute(
        select(ChatConversation).where(ChatConversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise NotFoundError("Conversation not found")
    return conversation


async def list_messages(
    db: AsyncSession,
    conversation_id: int,
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
    db: AsyncSession, conversation_id: int, user_id: str
) -> int:
    """Mark all messages in a conversation as read using DB function."""
    from sqlalchemy import text

    result = await db.execute(
        text("SELECT mark_messages_as_read(:conv_id, :user_id)"),
        {"conv_id": conversation_id, "user_id": user_id},
    )
    return result.scalar() or 0


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
