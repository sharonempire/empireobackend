from sqlalchemy import BigInteger, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from app.database import Base


class Course(Base):
    __tablename__ = "courses"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String, nullable=True)
    university = Column(String, nullable=True)
    country = Column(String, nullable=True)
    program_level = Column(String, nullable=True)
    duration = Column(String, nullable=True)
    tuition_fee = Column(String, nullable=True)
    currency = Column(String, nullable=True)
    intake = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    requirements = Column(Text, nullable=True)
    url = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)
