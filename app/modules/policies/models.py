import uuid

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class Policy(Base):
    __tablename__ = "eb_policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    category = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    department = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    version = Column(Integer, default=1)
    embedding = Column(Text, nullable=True)  # VECTOR type - stored as text
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
