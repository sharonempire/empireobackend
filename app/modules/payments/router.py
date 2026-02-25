from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import PaginatedResponse, paginate_metadata
from app.database import get_db
from app.dependencies import require_perm
from app.modules.payments import service
from app.modules.payments.schemas import PaymentOut
from app.modules.users.models import User

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.get("/", response_model=PaginatedResponse[PaymentOut])
async def api_list_payments(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    current_user: User = Depends(require_perm("payments", "read")),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_payments(db, page, size, status)
    return {**paginate_metadata(total, page, size), "items": items}


@router.get("/{payment_id}", response_model=PaymentOut)
async def api_get_payment(
    payment_id: int,
    current_user: User = Depends(require_perm("payments", "read")),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_payment(db, payment_id)
