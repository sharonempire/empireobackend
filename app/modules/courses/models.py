import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Text, DateTime, Numeric, BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from app.database import Base


class Course(Base):
    __tablename__ = "ref_courses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    program_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    university: Mapped[str | None] = mapped_column(String(500), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    city: Mapped[str | None] = mapped_column(String(255), nullable=True)
    campus: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tuition_fee: Mapped[str | None] = mapped_column(String(255), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(10), nullable=True)
    duration: Mapped[str | None] = mapped_column(String(100), nullable=True)
    program_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    field_of_study: Mapped[str | None] = mapped_column(String(255), nullable=True)
    commission: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    keywords: Mapped[list | None] = mapped_column(ARRAY(String), nullable=True)
    approval_status: Mapped[str] = mapped_column(String(30), default="not_approved")
    intakes: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    program_level_normalized: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    legacy_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, unique=True)
