from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import PaginatedResponse, paginate_metadata
from app.database import get_db
from app.dependencies import require_perm
from app.modules.leads import service
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
    current_user: User = Depends(require_perm("leads", "read")),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_leads(db, page, size, search, status, heat_status, lead_tab, assigned_to)
    return {**paginate_metadata(total, page, size), "items": items}


@router.get("/{lead_id}", response_model=LeadDetailOut)
async def api_get_lead(
    lead_id: int,
    current_user: User = Depends(require_perm("leads", "read")),
    db: AsyncSession = Depends(get_db),
):
    lead = await service.get_lead(db, lead_id)
    lead_info = await service.get_lead_info(db, lead_id)

    lead_data = LeadOut.model_validate(lead).model_dump()
    lead_data["lead_info"] = LeadInfoOut.model_validate(lead_info) if lead_info else None
    return LeadDetailOut(**lead_data)
