from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, NotFoundError
from app.modules.cases.models import VALID_STAGES, Case
from app.modules.cases.schemas import CaseCreate, CaseUpdate


async def list_cases(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    is_active: bool | None = None,
    counselor_id: UUID | None = None,
    stage: str | None = None,
) -> tuple[list[Case], int]:
    stmt = select(Case)
    count_stmt = select(func.count()).select_from(Case)

    if is_active is not None:
        stmt = stmt.where(Case.is_active == is_active)
        count_stmt = count_stmt.where(Case.is_active == is_active)
    if counselor_id:
        stmt = stmt.where(Case.assigned_counselor_id == counselor_id)
        count_stmt = count_stmt.where(Case.assigned_counselor_id == counselor_id)
    if stage:
        stmt = stmt.where(Case.current_stage == stage)
        count_stmt = count_stmt.where(Case.current_stage == stage)

    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.offset((page - 1) * size).limit(size).order_by(Case.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all(), total


async def get_case(db: AsyncSession, case_id: UUID) -> Case:
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise NotFoundError("Case not found")
    return case


async def create_case(db: AsyncSession, data: CaseCreate) -> Case:
    if data.current_stage not in VALID_STAGES:
        raise BadRequestError(f"Invalid stage: {data.current_stage}")
    case = Case(**data.model_dump())
    db.add(case)
    await db.flush()
    return case


async def update_case(db: AsyncSession, case_id: UUID, data: CaseUpdate) -> tuple[Case, str | None]:
    case = await get_case(db, case_id)
    update_data = data.model_dump(exclude_unset=True)
    old_stage = case.current_stage

    if "current_stage" in update_data and update_data["current_stage"] not in VALID_STAGES:
        raise BadRequestError(f"Invalid stage: {update_data['current_stage']}")

    for key, value in update_data.items():
        setattr(case, key, value)

    if "is_active" in update_data and not update_data["is_active"]:
        case.closed_at = datetime.now(timezone.utc)

    await db.flush()

    stage_changed = "current_stage" in update_data and update_data["current_stage"] != old_stage
    return case, old_stage if stage_changed else None
