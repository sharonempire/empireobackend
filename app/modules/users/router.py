from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.database import get_db
from app.dependencies import get_current_user
from app.modules.users.service import UserService
from app.modules.users.schemas import UserOut, UserCreate, UserUpdate, AssignRoleRequest
from app.core.pagination import PaginatedResponse

router = APIRouter()


@router.get("", response_model=PaginatedResponse[UserOut])
async def list_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    department: str | None = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    svc = UserService(db)
    users, total = await svc.list_users(page, size, department)
    return PaginatedResponse(
        items=users, total=total, page=page, size=size, pages=(total + size - 1) // size
    )


@router.get("/me", response_model=UserOut)
async def get_me(current_user=Depends(get_current_user)):
    return current_user


@router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: UUID, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    return await UserService(db).get_by_id(user_id)


@router.post("", response_model=UserOut, status_code=201)
async def create_user(data: UserCreate, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    return await UserService(db).create_user(data)


@router.patch("/{user_id}", response_model=UserOut)
async def update_user(user_id: UUID, data: UserUpdate, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    return await UserService(db).update_user(user_id, data)


@router.put("/{user_id}/roles", response_model=UserOut)
async def assign_roles(user_id: UUID, data: AssignRoleRequest, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    return await UserService(db).assign_roles(user_id, data.role_names)
