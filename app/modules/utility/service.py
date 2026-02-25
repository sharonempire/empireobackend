"""Utility service layer."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.utility.models import ChatbotSession, ShortLink
from app.modules.utility.schemas import ShortLinkCreate


async def list_short_links(
    db: AsyncSession, page: int = 1, size: int = 20
) -> tuple[list[ShortLink], int]:
    count_stmt = select(func.count()).select_from(ShortLink)
    total = (await db.execute(count_stmt)).scalar()
    stmt = select(ShortLink).offset((page - 1) * size).limit(size).order_by(ShortLink.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all(), total


async def get_short_link(db: AsyncSession, code: str) -> ShortLink:
    result = await db.execute(select(ShortLink).where(ShortLink.code == code))
    item = result.scalar_one_or_none()
    if not item:
        raise NotFoundError("Short link not found")
    return item


async def create_short_link(db: AsyncSession, data: ShortLinkCreate) -> ShortLink:
    item = ShortLink(**data.model_dump())
    db.add(item)
    await db.flush()
    return item


async def list_chatbot_sessions(
    db: AsyncSession, page: int = 1, size: int = 20
) -> tuple[list[ChatbotSession], int]:
    count_stmt = select(func.count()).select_from(ChatbotSession)
    total = (await db.execute(count_stmt)).scalar()
    stmt = select(ChatbotSession).offset((page - 1) * size).limit(size).order_by(ChatbotSession.updated_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all(), total
