from sqlalchemy import BigInteger, Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from pgvector.sqlalchemy import Vector

from app.core.enums import LeadTabEnum, ModuleTypeEnum
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
    
    # Missing columns from audit
    sl_no = Column(Integer, nullable=True, unique=True)  # Serial number (identity)
    heat_status = Column(Text, nullable=True)
    info_progress = Column(Text, nullable=True)
    call_summary = Column(Text, nullable=True)
    phone_norm = Column(Text, nullable=True)
    lead_tab = Column(LeadTabEnum, nullable=True)
    date = Column(DateTime(timezone=True), nullable=True)
    changes_history = Column(JSONB, nullable=True)
    lead_type = Column(Text, nullable=True)
    documents_status = Column(Text, nullable=True)
    fresh = Column(Boolean, nullable=True, server_default="true")  # PostgreSQL boolean default
    profile_image = Column(Text, nullable=True)
    is_premium_jobs = Column(Boolean, nullable=True)
    is_premium_courses = Column(Boolean, nullable=True)
    is_resume_downloaded = Column(Boolean, nullable=True)
    country_preference = Column(ARRAY(Text), nullable=True)
    is_registered = Column(Boolean, nullable=True)
    user_id = Column(String, nullable=True)
    fcm_token = Column(Text, nullable=True)
    finder_type = Column(Text, nullable=True)
    current_module = Column(ModuleTypeEnum, nullable=True)
    preferences_completed = Column(Boolean, nullable=True)
    profile_completion = Column(BigInteger, nullable=True)
    ig_handle = Column(Text, nullable=True)


class LeadInfo(Base):
    __tablename__ = "lead_info"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    lead_id = Column(BigInteger, nullable=True)
    info = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)
    
    # Missing columns from audit
    call_info = Column(JSONB, nullable=True)
    changes_history = Column(JSONB, nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)
    documents = Column(JSONB, nullable=True)
    fcm_token = Column(Text, nullable=True)
    user_id = Column(String, nullable=True)
    domain_tags = Column(ARRAY(Text), nullable=True, server_default="{}")
    interest_embedding = Column(Vector, nullable=True)  # pgvector
    profile_text = Column(Text, nullable=True)
    needs_enrichment = Column(Boolean, nullable=True, server_default="true")  # PostgreSQL boolean default
    enrichment_updated_at = Column(DateTime(timezone=True), nullable=True)
