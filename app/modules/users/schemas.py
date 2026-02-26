from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, computed_field


class UserOut(BaseModel):
    id: UUID
    email: str
    phone: str | None = None
    full_name: str
    department: str | None = None
    is_active: bool
    profile_picture: str | None = None
    caller_id: str | None = None
    location: str | None = None
    countries: list | dict | None = None
    last_login_at: datetime | None = None
    legacy_supabase_id: UUID | None = None
    created_at: datetime
    updated_at: datetime
    roles: list[str] = []

    model_config = {"from_attributes": True}

    @computed_field
    @property
    def profile_id(self) -> UUID | None:
        """The legacy profiles table ID — used by the Flutter frontend."""
        return self.legacy_supabase_id


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    phone: str | None = None
    department: str | None = None
    caller_id: str | None = None
    location: str | None = None
    countries: list | dict | None = None
    role_ids: list[UUID] = []


class UserUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    department: str | None = None
    is_active: bool | None = None
    profile_picture: str | None = None
    caller_id: str | None = None
    location: str | None = None
    countries: list | dict | None = None
    role_ids: list[UUID] | None = None
