from fastapi import APIRouter, Depends, Query
from sqlalchemy import cast, func, or_, select, String
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.pagination import PaginatedResponse, paginate_metadata
from app.database import get_db
from app.dependencies import get_current_user
from app.modules.leads.models import Lead, LeadInfo
from app.modules.leads.schemas import LeadDetailOut, LeadInfoOut, LeadOut
from app.modules.users.models import User

router = APIRouter(prefix="/leads", tags=["Leads"])


@router.get("/", response_model=PaginatedResponse[LeadOut])
async def api_list_leads(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    status: str | None = None,
    heat_status: str | None = None,
    lead_tab: str | None = None,
    assigned_to: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Lead)
    count_stmt = select(func.count()).select_from(Lead)

    if search:
        pattern = f"%{search}%"
        condition = or_(
            Lead.name.ilike(pattern),
            Lead.email.ilike(pattern),
            Lead.phone_norm.ilike(pattern),
        )
        stmt = stmt.where(condition)
        count_stmt = count_stmt.where(condition)

    if status:
        stmt = stmt.where(Lead.status == status)
        count_stmt = count_stmt.where(Lead.status == status)
    if heat_status:
        stmt = stmt.where(Lead.heat_status == heat_status)
        count_stmt = count_stmt.where(Lead.heat_status == heat_status)
    if lead_tab:
        stmt = stmt.where(Lead.lead_tab == lead_tab)
        count_stmt = count_stmt.where(Lead.lead_tab == lead_tab)
    if assigned_to:
        stmt = stmt.where(Lead.assigned_to == assigned_to)
        count_stmt = count_stmt.where(Lead.assigned_to == assigned_to)

    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.offset((page - 1) * size).limit(size).order_by(Lead.id.desc())
    result = await db.execute(stmt)
    return {**paginate_metadata(total, page, size), "items": result.scalars().all()}


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

    # LeadInfo PK = leadslist.id
    info_result = await db.execute(select(LeadInfo).where(LeadInfo.id == lead_id))
    lead_info = info_result.scalar_one_or_none()

    # Build response from ORM objects
    lead_data = LeadOut.model_validate(lead).model_dump()
    lead_data["lead_info"] = LeadInfoOut.model_validate(lead_info) if lead_info else None
    return LeadDetailOut(**lead_data)
