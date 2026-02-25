"""Leads service layer (read-only legacy)."""

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.leads.models import Lead, LeadInfo


async def list_leads(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    search: str | None = None,
    status: str | None = None,
    heat_status: str | None = None,
    lead_tab: str | None = None,
    assigned_to: str | None = None,
) -> tuple[list[Lead], int]:
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
    return result.scalars().all(), total


async def get_lead(db: AsyncSession, lead_id: int) -> Lead:
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise NotFoundError("Lead not found")
    return lead


async def get_lead_info(db: AsyncSession, lead_id: int) -> LeadInfo | None:
    result = await db.execute(select(LeadInfo).where(LeadInfo.id == lead_id))
    return result.scalar_one_or_none()
