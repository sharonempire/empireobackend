from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.modules.leads.models import Lead, LeadInfo
from app.modules.leads.schemas import LeadCreate, LeadUpdate, LeadInfoUpdate
from app.modules.events.service import EventService
from app.core.exceptions import NotFoundError


class LeadService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.events = EventService(db)

    async def get_by_id(self, lead_id: UUID) -> Lead:
        result = await self.db.execute(
            select(Lead).options(selectinload(Lead.lead_info)).where(Lead.id == lead_id)
        )
        lead = result.scalar_one_or_none()
        if not lead:
            raise NotFoundError("Lead", str(lead_id))
        return lead

    async def list_leads(self, page=1, size=20, status=None, assigned_to=None, lead_tab=None, heat_status=None):
        q = select(Lead).options(selectinload(Lead.lead_info))
        if status:
            q = q.where(Lead.status == status)
        if assigned_to:
            q = q.where(Lead.assigned_to == assigned_to)
        if lead_tab:
            q = q.where(Lead.lead_tab == lead_tab)
        if heat_status:
            q = q.where(Lead.heat_status == heat_status)
        total = (await self.db.execute(select(func.count()).select_from(q.subquery()))).scalar()
        q = q.offset((page - 1) * size).limit(size).order_by(Lead.created_at.desc())
        result = await self.db.execute(q)
        return result.scalars().all(), total

    async def create_lead(self, data: LeadCreate, actor_id: UUID | None = None) -> Lead:
        max_sl = (await self.db.execute(select(func.max(Lead.sl_no)))).scalar() or 0
        lead = Lead(**data.model_dump(exclude_unset=True), sl_no=max_sl + 1)
        self.db.add(lead)
        await self.db.flush()
        info = LeadInfo(lead_id=lead.id)
        self.db.add(info)
        await self.db.flush()
        await self.events.log("lead_created", "user" if actor_id else "system", actor_id, "lead", lead.id,
                              {"name": lead.full_name, "source": lead.source})
        return lead

    async def update_lead(self, lead_id: UUID, data: LeadUpdate, actor_id: UUID | None = None) -> Lead:
        lead = await self.get_by_id(lead_id)
        changes = {}
        for field, value in data.model_dump(exclude_unset=True).items():
            old = getattr(lead, field)
            if old != value:
                changes[field] = {"from": str(old), "to": str(value)}
                setattr(lead, field, value)
        if changes:
            await self.events.log("lead_updated", "user" if actor_id else "system", actor_id, "lead", lead.id,
                                  {"changes": changes})
        await self.db.flush()
        return lead

    async def update_lead_info(self, lead_id: UUID, data: LeadInfoUpdate, actor_id: UUID | None = None) -> LeadInfo:
        lead = await self.get_by_id(lead_id)
        if not lead.lead_info:
            info = LeadInfo(lead_id=lead.id, **data.model_dump(exclude_unset=True))
            self.db.add(info)
        else:
            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(lead.lead_info, field, value)
            info = lead.lead_info
        await self.db.flush()
        return info

    async def assign_lead(self, lead_id: UUID, assignee_id: UUID, actor_id: UUID) -> Lead:
        lead = await self.get_by_id(lead_id)
        old = lead.assigned_to
        lead.assigned_to = assignee_id
        if lead.status == "new":
            lead.status = "contacted"
        lead.fresh = False
        await self.db.flush()
        await self.events.log("lead_assigned", "user", actor_id, "lead", lead.id,
                              {"from": str(old), "to": str(assignee_id)})
        return lead
