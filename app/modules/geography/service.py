"""Geography service layer."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.geography.models import Campus, City, Country, University


# ── Countries ──

async def list_countries(
    db: AsyncSession, page: int = 1, size: int = 20
) -> tuple[list[Country], int]:
    count_stmt = select(func.count()).select_from(Country)
    total = (await db.execute(count_stmt)).scalar()
    stmt = select(Country).offset((page - 1) * size).limit(size).order_by(Country.name)
    result = await db.execute(stmt)
    return result.scalars().all(), total


async def get_country(db: AsyncSession, country_id: int) -> Country:
    result = await db.execute(select(Country).where(Country.id == country_id))
    country = result.scalar_one_or_none()
    if not country:
        raise NotFoundError("Country not found")
    return country


# ── Cities ──

async def list_cities(
    db: AsyncSession, page: int = 1, size: int = 20, country_id: int | None = None
) -> tuple[list[City], int]:
    stmt = select(City)
    count_stmt = select(func.count()).select_from(City)
    if country_id is not None:
        stmt = stmt.where(City.country_id == country_id)
        count_stmt = count_stmt.where(City.country_id == country_id)
    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.offset((page - 1) * size).limit(size).order_by(City.name)
    result = await db.execute(stmt)
    return result.scalars().all(), total


async def get_city(db: AsyncSession, city_id: int) -> City:
    result = await db.execute(select(City).where(City.id == city_id))
    city = result.scalar_one_or_none()
    if not city:
        raise NotFoundError("City not found")
    return city


# ── Universities ──

async def list_universities(
    db: AsyncSession, page: int = 1, size: int = 20, city_id: int | None = None
) -> tuple[list[University], int]:
    stmt = select(University)
    count_stmt = select(func.count()).select_from(University)
    if city_id is not None:
        stmt = stmt.where(University.city_id == city_id)
        count_stmt = count_stmt.where(University.city_id == city_id)
    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.offset((page - 1) * size).limit(size).order_by(University.name)
    result = await db.execute(stmt)
    return result.scalars().all(), total


async def get_university(db: AsyncSession, university_id: int) -> University:
    result = await db.execute(select(University).where(University.id == university_id))
    university = result.scalar_one_or_none()
    if not university:
        raise NotFoundError("University not found")
    return university


# ── Campuses ──

async def list_campuses(
    db: AsyncSession, page: int = 1, size: int = 20, university_id: int | None = None
) -> tuple[list[Campus], int]:
    stmt = select(Campus)
    count_stmt = select(func.count()).select_from(Campus)
    if university_id is not None:
        stmt = stmt.where(Campus.university_id == university_id)
        count_stmt = count_stmt.where(Campus.university_id == university_id)
    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.offset((page - 1) * size).limit(size).order_by(Campus.name)
    result = await db.execute(stmt)
    return result.scalars().all(), total


async def get_campus(db: AsyncSession, campus_id: int) -> Campus:
    result = await db.execute(select(Campus).where(Campus.id == campus_id))
    campus = result.scalar_one_or_none()
    if not campus:
        raise NotFoundError("Campus not found")
    return campus
