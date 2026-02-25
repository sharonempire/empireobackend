from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import PaginatedResponse, paginate_metadata
from app.database import get_db
from app.dependencies import require_perm
from app.modules.profiles import service
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
    items, total = await service.list_profiles(db, page, size, user_type, designation)
    return {**paginate_metadata(total, page, size), "items": items}


@router.get("/counselors")
async def api_list_counselors(
    current_user: User = Depends(require_perm("profiles", "read")),
    db: AsyncSession = Depends(get_db),
):
    """List counselors with today's attendance status."""
    return await service.list_counselors_with_attendance(db)


@router.get("/{profile_id}", response_model=ProfileOut)
async def api_get_profile(
    profile_id: UUID,
    current_user: User = Depends(require_perm("profiles", "read")),
    db: AsyncSession = Depends(get_db),
):
    """Get a profile (also serves as mentor endpoint)."""
    return await service.get_profile(db, profile_id)


@router.get("/{profile_id}/fcm-token")
async def api_get_profile_fcm_token(
    profile_id: UUID,
    current_user: User = Depends(require_perm("profiles", "read")),
    db: AsyncSession = Depends(get_db),
):
    """Get just the FCM token for a profile (for push notifications)."""
    token = await service.get_profile_fcm_token(db, profile_id)
    return {"profile_id": str(profile_id), "fcm_token": token}
