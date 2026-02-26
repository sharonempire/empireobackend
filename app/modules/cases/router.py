from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import log_event
from app.core.pagination import PaginatedResponse, paginate_metadata
from app.database import get_db
from app.dependencies import get_current_user, require_perm
from app.modules.cases.schemas import CaseCreate, CaseOut, CaseUpdate
from app.modules.cases.service import create_case, get_case, list_cases, update_case
from app.modules.users.models import User

router = APIRouter(prefix="/cases", tags=["Cases"])


@router.get("/", response_model=PaginatedResponse[CaseOut])
async def api_list_cases(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=500),
    is_active: bool | None = None,
    counselor_id: UUID | None = None,
    stage: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cases, total = await list_cases(db, page, size, is_active, counselor_id, stage)
    return {**paginate_metadata(total, page, size), "items": cases}


@router.get("/{case_id}", response_model=CaseOut)
async def api_get_case(
    case_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_case(db, case_id)


@router.post("/", response_model=CaseOut, status_code=201)
async def api_create_case(
    data: CaseCreate,
    current_user: User = Depends(require_perm("cases", "create")),
    db: AsyncSession = Depends(get_db),
):
    case = await create_case(db, data)
    await log_event(db, "case.created", current_user.id, "case", case.id, {"student_id": str(case.student_id)})
    await db.commit()
    return case


@router.patch("/{case_id}", response_model=CaseOut)
async def api_update_case(
    case_id: UUID,
    data: CaseUpdate,
    current_user: User = Depends(require_perm("cases", "update")),
    db: AsyncSession = Depends(get_db),
):
    case, old_stage = await update_case(db, case_id, data)
    if old_stage:
        await log_event(
            db, "case.stage_changed", current_user.id, "case", case.id,
            {"old_stage": old_stage, "new_stage": case.current_stage},
        )
    else:
        await log_event(db, "case.updated", current_user.id, "case", case.id, data.model_dump(exclude_unset=True))
    await db.commit()
    return case
