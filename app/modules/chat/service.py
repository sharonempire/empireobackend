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
