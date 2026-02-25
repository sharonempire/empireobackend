"""IG Sessions service layer."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.ig_sessions.models import ConversationSession, DMTemplate


async def list_sessions(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    status: str | None = None,
    ig_user_id: str | None = None,
) -> tuple[list[ConversationSession], int]:
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
    return result.scalars().all(), total


async def get_session(db: AsyncSession, session_id: UUID) -> ConversationSession:
    result = await db.execute(
        select(ConversationSession).where(ConversationSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise NotFoundError("Conversation session not found")
    return session


async def list_templates(db: AsyncSession) -> list[DMTemplate]:
    result = await db.execute(
        select(DMTemplate).order_by(DMTemplate.created_at.desc())
    )
    return result.scalars().all()
