from sqlalchemy import BigInteger, Column, DateTime
from sqlalchemy.dialects.postgresql import JSONB

from app.database import Base


class SavedJob(Base):
    __tablename__ = "saved_jobs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=True)
    job_id = Column(BigInteger, nullable=True)
    job_details = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)
