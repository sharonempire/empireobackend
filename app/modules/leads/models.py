from sqlalchemy import BigInteger, Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from app.database import Base


class Lead(Base):
    __tablename__ = "leadslist"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    source = Column(String, nullable=True)
    status = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)


class LeadInfo(Base):
    __tablename__ = "lead_info"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    lead_id = Column(BigInteger, nullable=True)
    info = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)
