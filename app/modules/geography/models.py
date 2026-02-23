from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Text, VARCHAR
from sqlalchemy.dialects.postgresql import JSONB

from app.database import Base


class Country(Base):
    __tablename__ = "countries"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=True)
    language = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True))
    description = Column(VARCHAR, nullable=True)
    cities = Column(JSONB, nullable=True)
    images = Column(JSONB, nullable=True)
    currency = Column(Text, nullable=True)
    top_attractions = Column(JSONB, nullable=True)
    portion = Column(JSONB, nullable=True)
    commission = Column(JSONB, nullable=True)
    displayimage = Column(Text, nullable=True)


class City(Base):
    __tablename__ = "cities"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=True)
    country_id = Column(BigInteger, ForeignKey("countries.id"), nullable=True)
    language = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True))
    description = Column(VARCHAR, nullable=True)
    universities = Column(JSONB, nullable=True)
    images = Column(JSONB, nullable=True)
    population = Column(Text, nullable=True)
    top_attractions = Column(JSONB, nullable=True)
    portion = Column(JSONB, nullable=True)
    commission = Column(Text, nullable=True)


class University(Base):
    __tablename__ = "universities"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=True)
    city_id = Column(BigInteger, ForeignKey("cities.id"), nullable=True)
    established_year = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True))
    description = Column(VARCHAR, nullable=True)
    campuses = Column(JSONB, nullable=True)
    images = Column(JSONB, nullable=True)
    website = Column(Text, nullable=True)
    accreditation = Column(Text, nullable=True)
    ranking = Column(Text, nullable=True)
    portion = Column(JSONB, nullable=True)
    commission = Column(Text, nullable=True)


class Campus(Base):
    __tablename__ = "campuses"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=True)
    university_id = Column(BigInteger, ForeignKey("universities.id"), nullable=True)
    created_at = Column(DateTime(timezone=True))
    address = Column(Text, nullable=True)
    city = Column(Text, nullable=True)
    country = Column(Text, nullable=True)
    description = Column(VARCHAR, nullable=True)
    courses = Column(JSONB, nullable=True)
    images = Column(JSONB, nullable=True)
    contact_info = Column(JSONB, nullable=True)
    facilities = Column(JSONB, nullable=True)
    portion = Column(JSONB, nullable=True)
    commission = Column(Text, nullable=True)
