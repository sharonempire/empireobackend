from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Numeric, Text, VARCHAR
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class Commission(Base):
    __tablename__ = "commission"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    commission_name = Column(VARCHAR, nullable=True)
    commission_amount = Column(BigInteger, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)


class Freelancer(Base):
    __tablename__ = "freelancers"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(VARCHAR, nullable=True)
    phone_number = Column(BigInteger, nullable=True)
    email = Column(VARCHAR, nullable=True)
    address = Column(VARCHAR, nullable=True)
    description = Column(VARCHAR, nullable=True)
    creator_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=True)
    commission_percentage = Column(BigInteger, nullable=True)


class FreelanceManager(Base):
    __tablename__ = "freelance_managers"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(VARCHAR, nullable=False)
    phone_number = Column(BigInteger, nullable=False, unique=True)
    username = Column(VARCHAR, nullable=False)
    commission_tier_id = Column(BigInteger, nullable=True)
    email = Column(VARCHAR, nullable=True)
    address = Column(VARCHAR, nullable=True)
    description = Column(VARCHAR, nullable=True)
    commission_tier_name = Column(VARCHAR, nullable=True)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=True)


class AgentEndpoint(Base):
    __tablename__ = "agent_endpoints"

    agent_key = Column(Text, primary_key=True)
    ext_norm = Column(Text, nullable=True, unique=True)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=True)

