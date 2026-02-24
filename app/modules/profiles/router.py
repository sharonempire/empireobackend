from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.pagination import PaginatedResponse, paginate_metadata
from app.database import get_db
from app.dependencies import require_perm
from app.modules.profiles.models import Profile
from app.modules.profiles.schemas import ProfileOut
from app.modules.users.models import User

router = APIRouter(prefix="/profiles", tags=["Profiles"])


@router.get("/", response_model=PaginatedResponse[ProfileOut])
async def api_list_profiles(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user_type: str | None = None,
    designation: str | None = None,
    current_user: User = Depends(require_perm("profiles", "read")),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Profile)
    count_stmt = select(func.count()).select_from(Profile)

    if user_type:
        stmt = stmt.where(Profile.user_type == user_type)
        count_stmt = count_stmt.where(Profile.user_type == user_type)
    if designation:
        stmt = stmt.where(Profile.designation == designation)
        count_stmt = count_stmt.where(Profile.designation == designation)

    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.offset((page - 1) * size).limit(size).order_by(Profile.diplay_name)
    result = await db.execute(stmt)
    return {**paginate_metadata(total, page, size), "items": result.scalars().all()}


@router.get("/{profile_id}", response_model=ProfileOut)
async def api_get_profile(
    profile_id: UUID,
    current_user: User = Depends(require_perm("profiles", "read")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Profile).where(Profile.id == profile_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise NotFoundError("Profile not found")
    return profile
