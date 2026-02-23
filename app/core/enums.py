"""PostgreSQL enum types for the database schema."""
from enum import Enum as PyEnum

from sqlalchemy.dialects.postgresql import ENUM


class LeadTab(PyEnum):
    """Lead tab type enum."""
    STUDENT = "student"
    JOB = "job"


class ModuleType(PyEnum):
    """Module type enum."""
    NOTIFICATION = "notification"
    CHAT = "chat"
    APPLICATION = "application"


class ApplicationStatus(PyEnum):
    """Application status enum."""
    APPLIED = "applied"
    NOT_APPLIED = "not_applied"
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


# SQLAlchemy PostgreSQL Enum types for use in models
# These reference existing PostgreSQL enums in the database
LeadTabEnum = ENUM(LeadTab, name="leadtab", create_type=False)
ModuleTypeEnum = ENUM(ModuleType, name="module_type", create_type=False)
ApplicationStatusEnum = ENUM(ApplicationStatus, name="application_status", create_type=False)

