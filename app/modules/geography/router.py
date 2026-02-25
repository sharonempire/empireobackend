from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import PaginatedResponse, paginate_metadata
from app.database import get_db
from app.dependencies import require_perm
from app.modules.geography import service
from app.modules.geography.schemas import CampusOut, CityOut, CountryOut, UniversityOut
from app.modules.users.models import User

router = APIRouter(prefix="/geography", tags=["Geography"])


# ── Countries ────────────────────────────────────────────────────────────────

@router.get("/countries", response_model=PaginatedResponse[CountryOut])
async def api_list_countries(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_perm("geography", "read")),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_countries(db, page, size)
    return {**paginate_metadata(total, page, size), "items": items}


@router.get("/countries/{country_id}", response_model=CountryOut)
async def api_get_country(
    country_id: int,
    current_user: User = Depends(require_perm("geography", "read")),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_country(db, country_id)


# ── Cities ───────────────────────────────────────────────────────────────────

@router.get("/cities", response_model=PaginatedResponse[CityOut])
async def api_list_cities(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    country_id: int | None = None,
    current_user: User = Depends(require_perm("geography", "read")),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_cities(db, page, size, country_id)
    return {**paginate_metadata(total, page, size), "items": items}


@router.get("/cities/{city_id}", response_model=CityOut)
async def api_get_city(
    city_id: int,
    current_user: User = Depends(require_perm("geography", "read")),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_city(db, city_id)


# ── Universities ─────────────────────────────────────────────────────────────

@router.get("/universities", response_model=PaginatedResponse[UniversityOut])
async def api_list_universities(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    city_id: int | None = None,
    current_user: User = Depends(require_perm("geography", "read")),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_universities(db, page, size, city_id)
    return {**paginate_metadata(total, page, size), "items": items}


@router.get("/universities/{university_id}", response_model=UniversityOut)
async def api_get_university(
    university_id: int,
    current_user: User = Depends(require_perm("geography", "read")),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_university(db, university_id)


# ── Campuses ─────────────────────────────────────────────────────────────────

@router.get("/campuses", response_model=PaginatedResponse[CampusOut])
async def api_list_campuses(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    university_id: int | None = None,
    current_user: User = Depends(require_perm("geography", "read")),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_campuses(db, page, size, university_id)
    return {**paginate_metadata(total, page, size), "items": items}


@router.get("/campuses/{campus_id}", response_model=CampusOut)
async def api_get_campus(
    campus_id: int,
    current_user: User = Depends(require_perm("geography", "read")),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_campus(db, campus_id)
