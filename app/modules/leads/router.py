from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.database import get_db
from app.dependencies import get_current_user
from app.modules.leads.service import LeadService
from app.modules.leads.schemas import LeadOut, LeadCreate, LeadUpdate, LeadInfoUpdate, LeadInfoOut
from app.modules.users.models import User
from app.core.pagination import PaginatedResponse

router = APIRouter()


@router.get("", response_model=PaginatedResponse[LeadOut])
async def list_leads(
    page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100),
    status: str | None = None, assigned_to: UUID | None = None,
    lead_tab: str | None = None, heat_status: str | None = None,
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user),
):
    svc = LeadService(db)
    items, total = await svc.list_leads(page, size, status, assigned_to, lead_tab, heat_status)
    return PaginatedResponse(items=items, total=total, page=page, size=size, pages=(total + size - 1) // size)


@router.get("/{lead_id}", response_model=LeadOut)
async def get_lead(lead_id: UUID, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    return await LeadService(db).get_by_id(lead_id)


@router.post("", response_model=LeadOut, status_code=201)
async def create_lead(data: LeadCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await LeadService(db).create_lead(data, actor_id=user.id)


@router.patch("/{lead_id}", response_model=LeadOut)
async def update_lead(lead_id: UUID, data: LeadUpdate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await LeadService(db).update_lead(lead_id, data, actor_id=user.id)


@router.put("/{lead_id}/info", response_model=LeadInfoOut)
async def update_lead_info(lead_id: UUID, data: LeadInfoUpdate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await LeadService(db).update_lead_info(lead_id, data, actor_id=user.id)


@router.post("/{lead_id}/assign/{assignee_id}", response_model=LeadOut)
async def assign_lead(lead_id: UUID, assignee_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await LeadService(db).assign_lead(lead_id, assignee_id, actor_id=user.id)
