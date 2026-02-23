from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.pagination import PaginatedResponse, paginate_metadata
from app.database import get_db
from app.dependencies import get_current_user
from app.modules.intakes.models import Intake
from app.modules.intakes.schemas import IntakeOut
from app.modules.users.models import User

router = APIRouter(prefix="/intakes", tags=["Intakes"])


@router.get("/", response_model=PaginatedResponse[IntakeOut])
async def api_list_intakes(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Intake)
    count_stmt = select(func.count()).select_from(Intake)

    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.offset((page - 1) * size).limit(size).order_by(Intake.start_date.desc())
    result = await db.execute(stmt)
    return {**paginate_metadata(total, page, size), "items": result.scalars().all()}


@router.get("/{intake_id}", response_model=IntakeOut)
async def api_get_intake(
    intake_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Intake).where(Intake.id == intake_id))
    intake = result.scalar_one_or_none()
    if not intake:
        raise NotFoundError("Intake not found")
    return intake
