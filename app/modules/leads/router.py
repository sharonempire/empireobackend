from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.pagination import PaginatedResponse, paginate
from app.database import get_db
from app.dependencies import get_current_user
from app.modules.leads.models import Lead, LeadInfo
from app.modules.leads.schemas import LeadDetailOut, LeadOut
from app.modules.users.models import User

router = APIRouter(prefix="/leads", tags=["Leads"])


@router.get("/", response_model=PaginatedResponse[LeadOut])
async def api_list_leads(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Lead)
    count_stmt = select(func.count()).select_from(Lead)

    if search:
        pattern = f"%{search}%"
        condition = or_(Lead.name.ilike(pattern), Lead.email.ilike(pattern), Lead.phone.ilike(pattern))
        stmt = stmt.where(condition)
        count_stmt = count_stmt.where(condition)

    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.offset((page - 1) * size).limit(size).order_by(Lead.id.desc())
    result = await db.execute(stmt)
    return {**paginate(total, page, size), "items": result.scalars().all()}


@router.get("/{lead_id}", response_model=LeadDetailOut)
async def api_get_lead(
    lead_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise NotFoundError("Lead not found")

    info_result = await db.execute(select(LeadInfo).where(LeadInfo.lead_id == lead_id))
    lead_info = info_result.scalar_one_or_none()

    return LeadDetailOut(
        id=lead.id,
        name=lead.name,
        email=lead.email,
        phone=lead.phone,
        source=lead.source,
        status=lead.status,
        created_at=lead.created_at,
        updated_at=lead.updated_at,
        info=lead_info.info if lead_info else None,
    )
