from uuid import UUID

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginResponse(TokenResponse):
    """Extended login response with user info for the frontend."""
    user_id: UUID
    profile_id: UUID | None = None
    email: str
    full_name: str
    roles: list[str] = []


class RefreshRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class BootstrapRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = "admin"


class AdminResetPasswordRequest(BaseModel):
    email: EmailStr
    new_password: str
