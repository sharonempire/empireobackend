"""Notifications service layer."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.notifications.models import Notification


async def list_notifications(
    db: AsyncSession,
    user_id: UUID,
    page: int = 1,
    size: int = 20,
    is_read: bool | None = None,
) -> tuple[list[Notification], int]:
    stmt = select(Notification).where(Notification.user_id == user_id)
    count_stmt = select(func.count()).select_from(Notification).where(Notification.user_id == user_id)

    if is_read is not None:
        stmt = stmt.where(Notification.is_read == is_read)
        count_stmt = count_stmt.where(Notification.is_read == is_read)

    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.offset((page - 1) * size).limit(size).order_by(Notification.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all(), total


async def mark_all_read(db: AsyncSession, user_id: UUID) -> int:
    result = await db.execute(
        update(Notification)
        .where(Notification.user_id == user_id, Notification.is_read == False)  # noqa: E712
        .values(is_read=True, read_at=datetime.now(timezone.utc))
    )
    await db.flush()
    return result.rowcount


async def mark_one_read(db: AsyncSession, notification_id: UUID, user_id: UUID) -> Notification:
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id, Notification.user_id == user_id
        )
    )
    notification = result.scalar_one_or_none()
    if not notification:
        raise NotFoundError("Notification not found")
    notification.is_read = True
    notification.read_at = datetime.now(timezone.utc)
    await db.flush()
    return notification


async def create_notification(
    db: AsyncSession,
    user_id: UUID,
    title: str,
    message: str | None = None,
    notification_type: str = "general",
    entity_type: str | None = None,
    entity_id: UUID | None = None,
    data: dict | None = None,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
        entity_type=entity_type,
        entity_id=entity_id,
        data=data,
    )
    db.add(notification)
    await db.flush()
    return notification
