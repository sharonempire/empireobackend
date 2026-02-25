from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

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
    await db.commit()
    return token


@router.delete("/{token_id}", status_code=204)
async def api_delete_push_token(
    token_id: UUID,
    current_user: User = Depends(require_perm("push_tokens", "delete")),
    db: AsyncSession = Depends(get_db),
):
    await service.delete_push_token(db, token_id)
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
    await db.commit()
    return token
