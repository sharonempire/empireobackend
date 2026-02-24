from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.pagination import PaginatedResponse, paginate_metadata
from app.database import get_db
from app.dependencies import require_perm
from app.modules.payments.models import Payment
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
    stmt = select(Payment)
    count_stmt = select(func.count()).select_from(Payment)

    if status:
        stmt = stmt.where(Payment.status == status)
        count_stmt = count_stmt.where(Payment.status == status)

    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.offset((page - 1) * size).limit(size).order_by(Payment.id.desc())
    result = await db.execute(stmt)
    return {**paginate_metadata(total, page, size), "items": result.scalars().all()}


@router.get("/{payment_id}", response_model=PaymentOut)
async def api_get_payment(
    payment_id: int,
    current_user: User = Depends(require_perm("payments", "read")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if not payment:
        raise NotFoundError("Payment not found")
    return payment
