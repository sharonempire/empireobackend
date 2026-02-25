from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import PaginatedResponse, paginate_metadata
from app.database import get_db
from app.dependencies import require_perm
from app.modules.intakes import service
from app.modules.intakes.schemas import IntakeOut
from app.modules.users.models import User

router = APIRouter(prefix="/intakes", tags=["Intakes"])


@router.get("/", response_model=PaginatedResponse[IntakeOut])
async def api_list_intakes(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_perm("intakes", "read")),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_intakes(db, page, size)
    return {**paginate_metadata(total, page, size), "items": items}


@router.get("/{intake_id}", response_model=IntakeOut)
async def api_get_intake(
    intake_id: int,
    current_user: User = Depends(require_perm("intakes", "read")),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_intake(db, intake_id)
