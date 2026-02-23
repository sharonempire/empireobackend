from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.pagination import PaginatedResponse, paginate_metadata
from app.database import get_db
from app.dependencies import get_current_user
from app.modules.geography.models import Campus, City, Country, University
from app.modules.geography.schemas import CampusOut, CityOut, CountryOut, UniversityOut
from app.modules.users.models import User

router = APIRouter(prefix="/geography", tags=["Geography"])


# ── Countries ────────────────────────────────────────────────────────────────

@router.get("/countries", response_model=PaginatedResponse[CountryOut])
async def api_list_countries(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Country)
    count_stmt = select(func.count()).select_from(Country)

    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.offset((page - 1) * size).limit(size).order_by(Country.name)
    result = await db.execute(stmt)
    return {**paginate_metadata(total, page, size), "items": result.scalars().all()}


@router.get("/countries/{country_id}", response_model=CountryOut)
async def api_get_country(
    country_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Country).where(Country.id == country_id))
    country = result.scalar_one_or_none()
    if not country:
        raise NotFoundError("Country not found")
    return country


# ── Cities ───────────────────────────────────────────────────────────────────

@router.get("/cities", response_model=PaginatedResponse[CityOut])
async def api_list_cities(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    country_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(City)
    count_stmt = select(func.count()).select_from(City)

    if country_id is not None:
        stmt = stmt.where(City.country_id == country_id)
        count_stmt = count_stmt.where(City.country_id == country_id)

    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.offset((page - 1) * size).limit(size).order_by(City.name)
    result = await db.execute(stmt)
    return {**paginate_metadata(total, page, size), "items": result.scalars().all()}


@router.get("/cities/{city_id}", response_model=CityOut)
async def api_get_city(
    city_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(City).where(City.id == city_id))
    city = result.scalar_one_or_none()
    if not city:
        raise NotFoundError("City not found")
    return city


# ── Universities ─────────────────────────────────────────────────────────────

@router.get("/universities", response_model=PaginatedResponse[UniversityOut])
async def api_list_universities(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    city_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(University)
    count_stmt = select(func.count()).select_from(University)

    if city_id is not None:
        stmt = stmt.where(University.city_id == city_id)
        count_stmt = count_stmt.where(University.city_id == city_id)

    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.offset((page - 1) * size).limit(size).order_by(University.name)
    result = await db.execute(stmt)
    return {**paginate_metadata(total, page, size), "items": result.scalars().all()}


@router.get("/universities/{university_id}", response_model=UniversityOut)
async def api_get_university(
    university_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(University).where(University.id == university_id))
    university = result.scalar_one_or_none()
    if not university:
        raise NotFoundError("University not found")
    return university


# ── Campuses ─────────────────────────────────────────────────────────────────

@router.get("/campuses", response_model=PaginatedResponse[CampusOut])
async def api_list_campuses(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    university_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Campus)
    count_stmt = select(func.count()).select_from(Campus)

    if university_id is not None:
        stmt = stmt.where(Campus.university_id == university_id)
        count_stmt = count_stmt.where(Campus.university_id == university_id)

    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.offset((page - 1) * size).limit(size).order_by(Campus.name)
    result = await db.execute(stmt)
    return {**paginate_metadata(total, page, size), "items": result.scalars().all()}


@router.get("/campuses/{campus_id}", response_model=CampusOut)
async def api_get_campus(
    campus_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Campus).where(Campus.id == campus_id))
    campus = result.scalar_one_or_none()
    if not campus:
        raise NotFoundError("Campus not found")
    return campus
