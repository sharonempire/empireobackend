from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import log_event
from app.core.pagination import PaginatedResponse, paginate
from app.database import get_db
from app.dependencies import get_current_user, require_perm
from app.modules.users.models import User
from app.modules.users.schemas import UserCreate, UserOut, UserUpdate
from app.modules.users.service import create_user, get_user, list_users, update_user

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", response_model=PaginatedResponse[UserOut])
async def api_list_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    department: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    users, total = await list_users(db, page, size, department)
    return {**paginate(total, page, size), "items": users}


@router.get("/me", response_model=UserOut)
async def api_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/{user_id}", response_model=UserOut)
async def api_get_user(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_user(db, user_id)


@router.post("/", response_model=UserOut, status_code=201)
async def api_create_user(
    data: UserCreate,
    current_user: User = Depends(require_perm("users", "create")),
    db: AsyncSession = Depends(get_db),
):
    user = await create_user(db, data)
    await log_event(db, "user.created", current_user.id, "user", user.id, {"email": user.email})
    await db.commit()
    return user


@router.patch("/{user_id}", response_model=UserOut)
async def api_update_user(
    user_id: UUID,
    data: UserUpdate,
    current_user: User = Depends(require_perm("users", "update")),
    db: AsyncSession = Depends(get_db),
):
    user = await update_user(db, user_id, data)
    await log_event(db, "user.updated", current_user.id, "user", user.id, data.model_dump(exclude_unset=True))
    await db.commit()
    return user
