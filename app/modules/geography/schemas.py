from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class CountryOut(BaseModel):
    id: int
    name: str | None = None
    language: str | None = None
    created_at: datetime | None = None
    description: str | None = None
    cities: Any | None = None
    images: Any | None = None
    currency: str | None = None
    top_attractions: Any | None = None
    portion: Any | None = None
    commission: Any | None = None
    displayimage: str | None = None

    model_config = ConfigDict(from_attributes=True)


class CityOut(BaseModel):
    id: int
    name: str | None = None
    country_id: int | None = None
    language: str | None = None
    created_at: datetime | None = None
    description: str | None = None
    universities: Any | None = None
    images: Any | None = None
    population: str | None = None
    top_attractions: Any | None = None
    portion: Any | None = None
    commission: str | None = None

    model_config = ConfigDict(from_attributes=True)


class UniversityOut(BaseModel):
    id: int
    name: str | None = None
    city_id: int | None = None
    established_year: str | None = None
    created_at: datetime | None = None
    description: str | None = None
    campuses: Any | None = None
    images: Any | None = None
    website: str | None = None
    accreditation: str | None = None
    ranking: str | None = None
    portion: Any | None = None
    commission: str | None = None

    model_config = ConfigDict(from_attributes=True)


class CampusOut(BaseModel):
    id: int
    name: str | None = None
    university_id: int | None = None
    created_at: datetime | None = None
    address: str | None = None
    city: str | None = None
    country: str | None = None
    description: str | None = None
    courses: Any | None = None
    images: Any | None = None
    contact_info: Any | None = None
    facilities: Any | None = None
    portion: Any | None = None
    commission: str | None = None

    model_config = ConfigDict(from_attributes=True)
