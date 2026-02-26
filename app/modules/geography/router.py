from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import log_event
from app.core.pagination import PaginatedResponse, paginate_metadata
from app.database import get_db
from app.dependencies import require_perm
from app.modules.geography import service
from app.modules.geography.schemas import (
    CampusCreate,
    CampusOut,
    CampusUpdate,
    CityCreate,
    CityOut,
    CityUpdate,
    CountryCreate,
    CountryOut,
    CountryUpdate,
    UniversityCreate,
    UniversityOut,
    UniversityUpdate,
)
from app.modules.users.models import User

router = APIRouter(prefix="/geography", tags=["Geography"])


# ── Countries ────────────────────────────────────────────────────────────────

@router.get("/countries", response_model=PaginatedResponse[CountryOut])
async def api_list_countries(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=500),
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


@router.post("/countries", response_model=CountryOut, status_code=201)
async def api_create_country(
    data: CountryCreate,
    current_user: User = Depends(require_perm("geography", "read")),
    db: AsyncSession = Depends(get_db),
):
    country = await service.create_country(db, data)
    await log_event(db, "geography.country_created", current_user.id, "geography", str(country.id), {})
    await db.commit()
    return country


@router.patch("/countries/{country_id}", response_model=CountryOut)
async def api_update_country(
    country_id: int,
    data: CountryUpdate,
    current_user: User = Depends(require_perm("geography", "read")),
    db: AsyncSession = Depends(get_db),
):
    country = await service.update_country(db, country_id, data)
    await log_event(db, "geography.country_updated", current_user.id, "geography", str(country.id), {})
    await db.commit()
    return country


# ── Cities ───────────────────────────────────────────────────────────────────

@router.get("/cities", response_model=PaginatedResponse[CityOut])
async def api_list_cities(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=500),
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


@router.post("/cities", response_model=CityOut, status_code=201)
async def api_create_city(
    data: CityCreate,
    current_user: User = Depends(require_perm("geography", "read")),
    db: AsyncSession = Depends(get_db),
):
    city = await service.create_city(db, data)
    await log_event(db, "geography.city_created", current_user.id, "geography", str(city.id), {})
    await db.commit()
    return city


@router.patch("/cities/{city_id}", response_model=CityOut)
async def api_update_city(
    city_id: int,
    data: CityUpdate,
    current_user: User = Depends(require_perm("geography", "read")),
    db: AsyncSession = Depends(get_db),
):
    city = await service.update_city(db, city_id, data)
    await log_event(db, "geography.city_updated", current_user.id, "geography", str(city.id), {})
    await db.commit()
    return city


# ── Universities ─────────────────────────────────────────────────────────────

@router.get("/universities", response_model=PaginatedResponse[UniversityOut])
async def api_list_universities(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=500),
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


@router.post("/universities", response_model=UniversityOut, status_code=201)
async def api_create_university(
    data: UniversityCreate,
    current_user: User = Depends(require_perm("geography", "read")),
    db: AsyncSession = Depends(get_db),
):
    university = await service.create_university(db, data)
    await log_event(db, "geography.university_created", current_user.id, "geography", str(university.id), {})
    await db.commit()
    return university


@router.patch("/universities/{university_id}", response_model=UniversityOut)
async def api_update_university(
    university_id: int,
    data: UniversityUpdate,
    current_user: User = Depends(require_perm("geography", "read")),
    db: AsyncSession = Depends(get_db),
):
    university = await service.update_university(db, university_id, data)
    await log_event(db, "geography.university_updated", current_user.id, "geography", str(university.id), {})
    await db.commit()
    return university


# ── Campuses ─────────────────────────────────────────────────────────────────

@router.get("/campuses", response_model=PaginatedResponse[CampusOut])
async def api_list_campuses(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=500),
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


@router.post("/campuses", response_model=CampusOut, status_code=201)
async def api_create_campus(
    data: CampusCreate,
    current_user: User = Depends(require_perm("geography", "read")),
    db: AsyncSession = Depends(get_db),
):
    campus = await service.create_campus(db, data)
    await log_event(db, "geography.campus_created", current_user.id, "geography", str(campus.id), {})
    await db.commit()
    return campus


@router.patch("/campuses/{campus_id}", response_model=CampusOut)
async def api_update_campus(
    campus_id: int,
    data: CampusUpdate,
    current_user: User = Depends(require_perm("geography", "read")),
    db: AsyncSession = Depends(get_db),
):
    campus = await service.update_campus(db, campus_id, data)
    await log_event(db, "geography.campus_updated", current_user.id, "geography", str(campus.id), {})
    await db.commit()
    return campus
