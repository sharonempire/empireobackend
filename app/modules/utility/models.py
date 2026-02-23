from sqlalchemy import BigInteger, Column, DateTime, Integer, Text
from sqlalchemy.dialects.postgresql import JSON, UUID

from app.database import Base


class ShortLink(Base):
    __tablename__ = "short_links"

    code = Column(Text, primary_key=True)
    target_url = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=True)


class CourseApprovalRequest(Base):
    __tablename__ = "course_approval_requests"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    status = Column(Text, nullable=True)
    payload = Column(JSON, nullable=True)
    submitted_by = Column(Text, nullable=True)
    submitted_designation = Column(Text, nullable=True)
    approved_by = Column(Text, nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approved_course_id = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)


class ChatbotSession(Base):
    __tablename__ = "chatbot_sessions"

    session_id = Column(Text, primary_key=True)
    last_intent = Column(Text, nullable=True)
    last_country = Column(Text, nullable=True)
    last_field = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)


class LeadAssignmentTracker(Base):
    __tablename__ = "lead_assignment_tracker"

    id = Column(Integer, primary_key=True, autoincrement=True)
    last_assigned_employee = Column(UUID(as_uuid=True), nullable=True)

