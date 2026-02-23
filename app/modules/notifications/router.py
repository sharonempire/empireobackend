from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.pagination import PaginatedResponse, paginate
from app.database import get_db
from app.dependencies import get_current_user
from app.modules.notifications.models import Notification
from app.modules.notifications.schemas import NotificationOut
from app.modules.users.models import User

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/", response_model=PaginatedResponse[NotificationOut])
async def api_list_notifications(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    is_read: bool | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Notification).where(Notification.user_id == current_user.id)
    count_stmt = select(func.count()).select_from(Notification).where(Notification.user_id == current_user.id)

    if is_read is not None:
        stmt = stmt.where(Notification.is_read == is_read)
        count_stmt = count_stmt.where(Notification.is_read == is_read)

    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.offset((page - 1) * size).limit(size).order_by(Notification.created_at.desc())
    result = await db.execute(stmt)
    return {**paginate(total, page, size), "items": result.scalars().all()}


@router.post("/read-all")
async def api_read_all(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        update(Notification)
        .where(Notification.user_id == current_user.id, Notification.is_read == False)
        .values(is_read=True, read_at=datetime.now(timezone.utc))
    )
    await db.commit()
    return {"detail": "All notifications marked as read"}


@router.patch("/{notification_id}/read", response_model=NotificationOut)
async def api_read_one(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Notification).where(Notification.id == notification_id, Notification.user_id == current_user.id)
    )
    notification = result.scalar_one_or_none()
    if not notification:
        raise NotFoundError("Notification not found")
    notification.is_read = True
    notification.read_at = datetime.now(timezone.utc)
    await db.commit()
    return notification
