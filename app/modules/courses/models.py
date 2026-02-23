from sqlalchemy import BigInteger, Boolean, Column, DateTime, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, TSVECTOR

from app.database import Base


class Course(Base):
    __tablename__ = "courses"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True))
    program_name = Column(Text, nullable=True)
    university = Column(Text, nullable=True)
    country = Column(Text, nullable=True)
    city = Column(Text, nullable=True)
    campus = Column(Text, nullable=True)
    application_fee = Column(Text, nullable=True)
    tuition_fee = Column(Text, nullable=True)
    deposit_amount = Column(Text, nullable=True)
    currency = Column(Text, nullable=True)
    duration = Column(Text, nullable=True)
    language = Column(Text, nullable=True)
    study_type = Column(Text, nullable=True)
    program_level = Column(Text, nullable=True)
    english_proficiency = Column(Text, nullable=True)
    minimum_percentage = Column(Text, nullable=True)
    age_limit = Column(Text, nullable=True)
    academic_gap = Column(Text, nullable=True)
    max_backlogs = Column(Text, nullable=True)
    work_experience_requirement = Column(Text, nullable=True)
    required_subjects = Column(JSONB, nullable=True)
    intakes = Column(JSONB, nullable=True)
    links = Column(JSONB, nullable=True)
    media_links = Column(JSONB, nullable=True)
    course_description = Column(String, nullable=True)
    special_requirements = Column(String, nullable=True)
    field_of_study = Column(Text, nullable=True)
    embedding = Column(Text, nullable=True)  # VECTOR type - read as text
    commission = Column(JSONB, nullable=True)
    search_text = Column(Text, nullable=True)
    search_vector = Column(TSVECTOR, nullable=True)
    domain = Column(Text, nullable=True)
    keywords = Column(ARRAY(Text), nullable=True)
    application_status = Column(Text, nullable=True, server_default="not_applied")
    approval_status = Column(Text, nullable=False, server_default="not_approved")
    approved_detail = Column(JSONB, nullable=True)
    insertion_details = Column(JSONB, nullable=True)
    # Normalized / AI-computed fields
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
    fos_processing = Column(Boolean, nullable=True, server_default="false")
    fos_processing_at = Column(DateTime(timezone=True), nullable=True)
    fos_needs_recompute = Column(Boolean, nullable=True, server_default="true")
    field_of_study_raw_backup = Column(Text, nullable=True)
    english_proficiency_normalized_v2 = Column(JSONB, nullable=True)
    english_proficiency_v2_processed = Column(Boolean, nullable=False, server_default="false")
    required_subjects_normalized = Column(JSONB, nullable=True)
    required_subjects_ai_processed = Column(Boolean, nullable=False, server_default="false")
    required_subjects_ai_processed_at = Column(DateTime(timezone=True), nullable=True)


class UniversityCourse(Base):
    """Duplicate courses table used by Flutter apps."""
    __tablename__ = "university_courses"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True))
    program_name = Column(Text, nullable=True)
    university = Column(Text, nullable=True)
    country = Column(Text, nullable=True)
    city = Column(Text, nullable=True)
    campus = Column(Text, nullable=True)
    application_fee = Column(Text, nullable=True)
    tuition_fee = Column(Text, nullable=True)
    deposit_amount = Column(Text, nullable=True)
    currency = Column(Text, nullable=True)
    duration = Column(Text, nullable=True)
    language = Column(Text, nullable=True)
    study_type = Column(Text, nullable=True)
    program_level = Column(Text, nullable=True)
    english_proficiency = Column(Text, nullable=True)
    minimum_percentage = Column(Text, nullable=True)
    age_limit = Column(Text, nullable=True)
    academic_gap = Column(Text, nullable=True)
    max_backlogs = Column(Text, nullable=True)
    work_experience_requirement = Column(Text, nullable=True)
    required_subjects = Column(JSONB, nullable=True)
    intakes = Column(JSONB, nullable=True)
    links = Column(JSONB, nullable=True)
    media_links = Column(JSONB, nullable=True)
    course_description = Column(String, nullable=True)
    special_requirements = Column(String, nullable=True)
    field_of_study = Column(Text, nullable=True)
    embedding = Column(Text, nullable=True)
    commission = Column(JSONB, nullable=True)
    search_text = Column(Text, nullable=True)
    search_vector = Column(TSVECTOR, nullable=True)
    domain = Column(Text, nullable=True)
    keywords = Column(ARRAY(Text), nullable=True)
    application_status = Column(Text, nullable=True, server_default="not_applied")
    approval_status = Column(Text, nullable=False, server_default="not_approved")
    approved_detail = Column(JSONB, nullable=True)
    insertion_details = Column(JSONB, nullable=True)
    source_key = Column(Text, nullable=True)
    university_image = Column(Text, nullable=True)
    tuition_fee_international_amount = Column(Numeric, nullable=True)
    tuition_fee_international_currency = Column(Text, nullable=True)
    tuition_fee_international_basis = Column(Text, nullable=True)
    tuition_fee_international_raw = Column(Text, nullable=True)


class CourseApprovalRequest(Base):
    __tablename__ = "course_approval_requests"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True))
    status = Column(Text, nullable=True)
    payload = Column(JSONB, nullable=True)
    submitted_by = Column(String, nullable=True)
    submitted_designation = Column(Text, nullable=True)
    approved_by = Column(Text, nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approved_course_id = Column(Text, nullable=True)


class SavedCourse(Base):
    __tablename__ = "saved_courses"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True))
    user_id = Column(BigInteger, nullable=True)
    course_id = Column(BigInteger, nullable=True)
    course_details = Column(JSONB, nullable=True)


class AppliedCourse(Base):
    __tablename__ = "applied_courses"

    id = Column(Text, primary_key=True)
    user_id = Column(Text, nullable=False)
    course_id = Column(Text, nullable=False)
    course_details = Column(JSONB, nullable=False)
    status = Column(Text, nullable=False, server_default="applied")
    applied_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
