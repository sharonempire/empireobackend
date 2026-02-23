import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "eb_users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(20), nullable=True)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    department = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    profile_picture = Column(Text, nullable=True)
    caller_id = Column(String(50), nullable=True)
    location = Column(String(100), nullable=True)
    countries = Column(JSONB, nullable=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    legacy_supabase_id = Column(UUID(as_uuid=True), unique=True, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    user_roles = relationship("UserRole", back_populates="user", lazy="selectin")

    @property
    def roles(self) -> list[str]:
        return [ur.role.name for ur in self.user_roles if ur.role]


class Role(Base):
    __tablename__ = "eb_roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    role_permissions = relationship("RolePermission", back_populates="role", lazy="selectin")


class Permission(Base):
    __tablename__ = "eb_permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resource = Column(String(50), nullable=False)
    action = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)


class UserRole(Base):
    __tablename__ = "eb_user_roles"

    user_id = Column(UUID(as_uuid=True), ForeignKey("eb_users.id"), primary_key=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey("eb_roles.id"), primary_key=True)

    user = relationship("User", back_populates="user_roles")
    role = relationship("Role")


class RolePermission(Base):
    __tablename__ = "eb_role_permissions"

    role_id = Column(UUID(as_uuid=True), ForeignKey("eb_roles.id"), primary_key=True)
    permission_id = Column(UUID(as_uuid=True), ForeignKey("eb_permissions.id"), primary_key=True)

    role = relationship("Role", back_populates="role_permissions")
    permission = relationship("Permission")
