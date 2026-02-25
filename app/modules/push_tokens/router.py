from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import log_event
from app.core.pagination import PaginatedResponse, paginate_metadata
from app.database import get_db
from app.dependencies import require_perm
from app.modules.push_tokens import service
from app.modules.push_tokens.schemas import (
    UserFCMTokenCreate,
    UserFCMTokenOut,
    UserPushTokenCreate,
    UserPushTokenOut,
)
from app.modules.users.models import User

router = APIRouter(prefix="/push-tokens", tags=["Push Tokens"])


@router.get("/", response_model=PaginatedResponse[UserPushTokenOut])
async def api_list_push_tokens(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user_id: UUID | None = None,
    current_user: User = Depends(require_perm("push_tokens", "read")),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_push_tokens(db, page, size, user_id)
    return {**paginate_metadata(total, page, size), "items": items}


@router.post("/", response_model=UserPushTokenOut, status_code=201)
async def api_create_push_token(
    data: UserPushTokenCreate,
    current_user: User = Depends(require_perm("push_tokens", "create")),
    db: AsyncSession = Depends(get_db),
):
    token = await service.create_push_token(db, data)
    await log_event(db, "push_token.created", current_user.id, "push_token", str(token.id), {
        "user_id": str(data.user_id),
    })
    await db.commit()
    return token


@router.delete("/{token_id}", status_code=204)
async def api_delete_push_token(
    token_id: UUID,
    current_user: User = Depends(require_perm("push_tokens", "delete")),
    db: AsyncSession = Depends(get_db),
):
    await service.delete_push_token(db, token_id)
    await log_event(db, "push_token.deleted", current_user.id, "push_token", str(token_id), {})
    await db.commit()


@router.get("/fcm", response_model=PaginatedResponse[UserFCMTokenOut])
async def api_list_fcm_tokens(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user_id: UUID | None = None,
    current_user: User = Depends(require_perm("push_tokens", "read")),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_fcm_tokens(db, page, size, user_id)
    return {**paginate_metadata(total, page, size), "items": items}


@router.post("/fcm", response_model=UserFCMTokenOut, status_code=201)
async def api_create_fcm_token(
    data: UserFCMTokenCreate,
    current_user: User = Depends(require_perm("push_tokens", "create")),
    db: AsyncSession = Depends(get_db),
):
    token = await service.create_fcm_token(db, data)
    await log_event(db, "fcm_token.created", current_user.id, "fcm_token", str(token.id), {
        "user_id": str(data.user_id),
    })
    await db.commit()
    return token


# ── Push Notification Sending ────────────────────────────────────────
# Mirrors Supabase Edge Function `Notification` (v18)


@router.post("/send")
async def api_send_push(
    user_id: UUID,
    title: str,
    body: str,
    current_user: User = Depends(require_perm("push_tokens", "create")),
    db: AsyncSession = Depends(get_db),
):
    """Send FCM push notification to all devices of a user.

    Mirrors the Supabase Edge Function `Notification` which sends
    FCM pushes via Google Auth HTTP v1 API.
    """
    from app.core.fcm_service import send_push_to_user

    results = await send_push_to_user(db, str(user_id), title, body)
    await log_event(db, "push_notification.sent", current_user.id, "push_token", str(user_id), {
        "title": title, "results_count": len(results),
    })
    await db.commit()
    return {"user_id": str(user_id), "results": results}
