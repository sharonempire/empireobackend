from sqlalchemy import BigInteger, Column, Date, DateTime, Text
from sqlalchemy.dialects.postgresql import JSONB

from app.database import Base


class Intake(Base):
    __tablename__ = "intakes"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    application_deadline = Column(Date, nullable=True)
    description = Column(Text, nullable=True)
    universities = Column(JSONB, nullable=True)
    courses = Column(JSONB, nullable=True)
    requirements = Column(JSONB, nullable=True)
    fees = Column(JSONB, nullable=True)
    scholarships = Column(JSONB, nullable=True)
    additional_info = Column(JSONB, nullable=True)
    commission = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)

