from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import log_event
from app.core.pagination import PaginatedResponse, paginate_metadata
from app.database import get_db
from app.dependencies import get_current_user, require_perm
from app.modules.profiles import service
from app.modules.profiles.schemas import ProfileBatchRequest, ProfileCreate, ProfileOut, ProfileSummaryOut, ProfileUpdate
from app.modules.users.models import User

router = APIRouter(prefix="/profiles", tags=["Profiles"])


@router.get("/", response_model=PaginatedResponse[ProfileOut])
async def api_list_profiles(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=500),
    user_type: str | None = None,
    designation: str | None = None,
    email: str | None = Query(None, description="Filter by exact email"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_profiles(db, page, size, user_type, designation, email)
    return {**paginate_metadata(total, page, size), "items": items}


@router.get("/exists")
async def api_profile_exists(
    email: str = Query(..., description="Email to check"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Check if a profile exists by email."""
    exists = await service.profile_exists_by_email(db, email)
    return {"exists": exists, "email": email}


@router.post("/", response_model=ProfileOut, status_code=201)
async def api_create_profile(
    data: ProfileCreate,
    current_user: User = Depends(require_perm("profiles", "create")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new profile (used by addEmployee)."""
    profile = await service.create_profile(db, data)
    await log_event(db, "profile.created", current_user.id, "profile", str(profile.id),
                    {"diplay_name": profile.diplay_name, "email": profile.email})
    await db.commit()
    return profile


@router.post("/batch", response_model=list[ProfileSummaryOut])
async def api_batch_profiles(
    data: ProfileBatchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Batch fetch profile summaries by IDs (max 100)."""
    if len(data.profile_ids) > 100:
        from app.core.exceptions import BadRequestError
        raise BadRequestError("Maximum 100 profile IDs per batch request")
    return await service.batch_get_profiles(db, data.profile_ids)


@router.get("/counselors")
async def api_list_counselors(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List counselors with today's attendance status."""
    return await service.list_counselors_with_attendance(db)


@router.get("/{profile_id}", response_model=ProfileOut)
async def api_get_profile(
    profile_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a profile (also serves as mentor endpoint)."""
    return await service.get_profile(db, profile_id)


@router.patch("/{profile_id}", response_model=ProfileOut)
async def api_update_profile(
    profile_id: UUID,
    data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a profile (FCM token, display name, etc.)."""
    profile = await service.update_profile(db, profile_id, data)
    await log_event(db, "profile.updated", current_user.id, "profile", str(profile_id),
                    data.model_dump(exclude_unset=True))
    await db.commit()
    return profile


@router.put("/{profile_id}", response_model=ProfileOut)
async def api_update_profile_put(
    profile_id: UUID,
    data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """PUT alias for PATCH profile update."""
    profile = await service.update_profile(db, profile_id, data)
    await log_event(db, "profile.updated", current_user.id, "profile", str(profile_id),
                    data.model_dump(exclude_unset=True))
    await db.commit()
    return profile


@router.get("/{profile_id}/fcm-token")
async def api_get_profile_fcm_token(
    profile_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get just the FCM token for a profile (for push notifications)."""
    token = await service.get_profile_fcm_token(db, profile_id)
    return {"profile_id": str(profile_id), "fcm_token": token}
