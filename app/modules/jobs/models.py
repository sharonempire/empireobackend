from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB

from app.core.enums import ApplicationStatusEnum
from app.database import Base


class JobProfile(Base):
    __tablename__ = "job_profiles"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    company_name = Column(Text, nullable=True)
    email_address = Column(Text, nullable=True, unique=True)
    profile_id = Column(Text, nullable=True)  # UUID as text
    status = Column(Text, nullable=True)
    company_website = Column(Text, nullable=True)
    company_address = Column(Text, nullable=True)


class Job(Base):
    __tablename__ = "jobs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), nullable=True)
    job_information = Column(JSONB, nullable=True)
    location_salary_details = Column(JSONB, nullable=True)
    job_details = Column(JSONB, nullable=True)
    required_qualification = Column(JSONB, nullable=True)
    status = Column(Text, nullable=True)
    job_profile_id = Column(BigInteger, ForeignKey("job_profiles.id"), nullable=True)
    application_status = Column(ApplicationStatusEnum, nullable=True)


class JobCountry(Base):
    __tablename__ = "jobs_countries"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    country = Column(Text, nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), nullable=True)


class AppliedJob(Base):
    __tablename__ = "applied_jobs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    job_id = Column(BigInteger, nullable=True)
    user_id = Column(BigInteger, nullable=True)
    status = Column(Text, nullable=True)
    applied_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)
    
    # Missing columns from audit
    candidate_name = Column(Text, nullable=True)
    job_title = Column(Text, nullable=True)

