from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime
from typing import Optional, List


class PermissionOut(BaseModel):
    id: UUID
    resource: str
    action: str
    model_config = {"from_attributes": True}


class RoleOut(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    permissions: List[PermissionOut] = []
    model_config = {"from_attributes": True}


class UserOut(BaseModel):
    id: UUID
    email: str
    phone: Optional[str] = None
    full_name: str
    department: Optional[str] = None
    is_active: bool
    location: Optional[str] = None
    roles: List[RoleOut] = []
    created_at: datetime
    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    email: EmailStr
    phone: Optional[str] = None
    full_name: str
    password: str
    department: Optional[str] = None
    role_names: List[str] = ["counselor"]


class UserUpdate(BaseModel):
    phone: Optional[str] = None
    full_name: Optional[str] = None
    department: Optional[str] = None
    is_active: Optional[bool] = None
    location: Optional[str] = None


class AssignRoleRequest(BaseModel):
    role_names: List[str]
