from sqlalchemy import BigInteger, Boolean, Column, DateTime, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, TSVECTOR
from pgvector.sqlalchemy import Vector

from app.core.enums import ApplicationStatusEnum
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
    
    # Missing columns from audit
    domain = Column(Text, nullable=True)
    keywords = Column(ARRAY(Text), nullable=True)
    application_status = Column(ApplicationStatusEnum, nullable=True)
    approval_status = Column(Text, nullable=True, server_default="not_approved")
    approved_detail = Column(JSONB, nullable=True)
    insertion_details = Column(JSONB, nullable=True)
    program_level_normalized = Column(Text, nullable=True)
    age_limit_num = Column(Integer, nullable=True)
    academic_gap_num = Column(Integer, nullable=True)
    max_backlogs_num = Column(Integer, nullable=True)
    min_pct_num = Column(Numeric, nullable=True)
    domain_tags = Column(ARRAY(Text), nullable=True, server_default="{}")
    study_type_raw = Column(Text, nullable=True)
    field_of_study_raw = Column(Text, nullable=True)
    intakes_raw = Column(JSONB, nullable=True)
    field_of_study_ai = Column(Text, nullable=True)
    fos_processing = Column(Boolean, nullable=True, server_default="false")  # PostgreSQL boolean default
    fos_processing_at = Column(DateTime(timezone=True), nullable=True)
    fos_needs_recompute = Column(Boolean, nullable=True, server_default="true")  # PostgreSQL boolean default
    field_of_study_raw_backup = Column(Text, nullable=True)
    english_proficiency_normalized_v2 = Column(JSONB, nullable=True)
    english_proficiency_v2_processed = Column(Boolean, nullable=True, server_default="false")  # PostgreSQL boolean default
    required_subjects_normalized = Column(JSONB, nullable=True)
    required_subjects_ai_processed = Column(Boolean, nullable=True)
    required_subjects_ai_processed_at = Column(DateTime(timezone=True), nullable=True)
    search_text = Column(Text, nullable=True)
    search_vector = Column(TSVECTOR, nullable=True)
    embedding = Column(Vector, nullable=True)  # pgvector embedding
    commission = Column(JSONB, nullable=True)
