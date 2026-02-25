from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CommissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    commission_name: str | None = None
    commission_amount: int | None = None
    created_at: datetime | None = None


class CommissionCreate(BaseModel):
    commission_name: str
    commission_amount: int | None = None


class FreelancerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str | None = None
    phone_number: int | None = None
    email: str | None = None
    address: str | None = None
    description: str | None = None
    creator_id: UUID | None = None
    commission_percentage: int | None = None


class FreelancerCreate(BaseModel):
    name: str
    phone_number: int | None = None
    email: str | None = None
    address: str | None = None
    description: str | None = None
    commission_percentage: int | None = None


class FreelancerUpdate(BaseModel):
    name: str | None = None
    phone_number: int | None = None
    email: str | None = None
    address: str | None = None
    description: str | None = None
    commission_percentage: int | None = None


class FreelanceManagerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    phone_number: int
    username: str
    commission_tier_id: int | None = None
    email: str | None = None
    address: str | None = None
    description: str | None = None
    commission_tier_name: str | None = None
    profile_id: UUID | None = None


class FreelanceManagerCreate(BaseModel):
    name: str
    phone_number: int
    username: str
    commission_tier_id: int | None = None
    email: str | None = None
    address: str | None = None
    description: str | None = None
    commission_tier_name: str | None = None
    profile_id: UUID | None = None


class FreelanceManagerUpdate(BaseModel):
    name: str | None = None
    phone_number: int | None = None
    username: str | None = None
    commission_tier_id: int | None = None
    email: str | None = None
    address: str | None = None
    description: str | None = None
    commission_tier_name: str | None = None
    profile_id: UUID | None = None


class AgentEndpointOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    agent_key: str
    ext_norm: str | None = None
    profile_id: UUID | None = None
