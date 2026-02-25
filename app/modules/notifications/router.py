from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import log_event
from app.core.pagination import PaginatedResponse, paginate_metadata
from app.database import get_db
from app.dependencies import require_perm
from app.modules.notifications import service
from app.modules.notifications.schemas import NotificationOut
from app.modules.users.models import User

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/", response_model=PaginatedResponse[NotificationOut])
async def api_list_notifications(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    is_read: bool | None = None,
    current_user: User = Depends(require_perm("notifications", "read")),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_notifications(db, current_user.id, page, size, is_read)
    return {**paginate_metadata(total, page, size), "items": items}


@router.post("/read-all", response_model=None)
async def api_read_all(
    current_user: User = Depends(require_perm("notifications", "read")),
    db: AsyncSession = Depends(get_db),
):
    count = await service.mark_all_read(db, current_user.id)
    await log_event(db, "notification.read_all", current_user.id, "notification", "bulk", {"count": count})
    await db.commit()
    return {"detail": "All notifications marked as read", "count": count}


@router.patch("/{notification_id}/read", response_model=NotificationOut)
async def api_read_one(
    notification_id: UUID,
    current_user: User = Depends(require_perm("notifications", "read")),
    db: AsyncSession = Depends(get_db),
):
    notification = await service.mark_one_read(db, notification_id, current_user.id)
    await log_event(db, "notification.read", current_user.id, "notification", str(notification_id), {})
    await db.commit()
    return notification
