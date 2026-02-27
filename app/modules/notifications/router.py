from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import log_event
from app.core.pagination import PaginatedResponse, paginate_metadata
from app.database import get_db
from app.dependencies import get_current_user, require_perm
from app.modules.notifications import service
from app.modules.notifications.schemas import NotificationOut, NotificationSend, PushNotificationRequest
from app.modules.users.models import User

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/", response_model=PaginatedResponse[NotificationOut])
async def api_list_notifications(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=500),
    is_read: bool | None = None,
    user_id: UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Allow filtering by user_id (admin use), otherwise default to current user
    target_user_id = user_id if user_id else current_user.id
    items, total = await service.list_notifications(db, target_user_id, page, size, is_read)
    return {**paginate_metadata(total, page, size), "items": items}


@router.post("/read-all", response_model=None)
async def api_read_all(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    count = await service.mark_all_read(db, current_user.id)
    await log_event(db, "notification.read_all", current_user.id, "notification", "bulk", {"count": count})
    await db.commit()
    return {"detail": "All notifications marked as read", "count": count}


async def _mark_read(notification_id, current_user, db):
    notification = await service.mark_one_read(db, notification_id, current_user.id)
    await log_event(db, "notification.read", current_user.id, "notification", str(notification_id), {})
    await db.commit()
    return notification


@router.patch("/{notification_id}/read", response_model=NotificationOut)
async def api_read_one(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _mark_read(notification_id, current_user, db)


@router.put("/{notification_id}/read", response_model=NotificationOut)
async def api_read_one_put(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """PUT alias for PATCH notification read."""
    return await _mark_read(notification_id, current_user, db)


@router.delete("/{notification_id}", status_code=204)
async def api_delete_notification(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a notification."""
    await service.delete_notification(db, notification_id, current_user.id)
    await log_event(db, "notification.deleted", current_user.id, "notification", str(notification_id), {})
    await db.commit()


@router.post("/send", response_model=NotificationOut, status_code=201)
async def api_send_notification(
    data: NotificationSend,
    current_user: User = Depends(require_perm("notifications", "create")),
    db: AsyncSession = Depends(get_db),
):
    """Send an in-app notification + FCM push to a user.

    Creates an eb_notifications record and sends FCM push
    to all of the user's registered devices.
    """
    # Create in-app notification
    notification = await service.create_notification(
        db=db,
        user_id=data.recipient_id,
        title=data.title,
        message=data.body,
        notification_type="push",
        data=data.data,
    )

    # Send FCM push notification
    push_results = []
    try:
        from app.core.fcm_service import send_push_to_user
        push_results = await send_push_to_user(db, str(data.recipient_id), data.title, data.body)
    except Exception as e:
        import logging
        logging.getLogger("empireo.notifications").warning("FCM push failed: %s", e)

    await log_event(db, "notification.sent", current_user.id, "notification", str(notification.id), {
        "recipient_id": str(data.recipient_id),
        "title": data.title,
        "push_results_count": len(push_results),
    })
    await db.commit()
    return notification


@router.post("/push")
async def api_push_notification(
    data: PushNotificationRequest,
    current_user: User = Depends(get_current_user),
):
    """Direct FCM push by token (replaces Supabase Edge Function).

    Sends push notification directly to a device via FCM token.
    No in-app notification record is created.
    """
    from app.core.fcm_service import send_push_notification

    result = await send_push_notification(
        fcm_token=data.fcm_token,
        title=data.title,
        body=data.body,
        data=data.data,
    )
    return result
