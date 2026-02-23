from sqlalchemy import BigInteger, Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB

from app.database import Base


class SavedCourse(Base):
    __tablename__ = "saved_courses"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=True)
    course_id = Column(BigInteger, nullable=True)
    course_details = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)


class SavedJob(Base):
    __tablename__ = "saved_jobs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=True)
    job_id = Column(BigInteger, nullable=True)
    job_details = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)

