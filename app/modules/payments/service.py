"""Payments service layer."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.payments.models import Payment


async def list_payments(
    db: AsyncSession, page: int = 1, size: int = 20, status: str | None = None
) -> tuple[list[Payment], int]:
    stmt = select(Payment)
    count_stmt = select(func.count()).select_from(Payment)

    if status:
        stmt = stmt.where(Payment.status == status)
        count_stmt = count_stmt.where(Payment.status == status)

    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.offset((page - 1) * size).limit(size).order_by(Payment.id.desc())
    result = await db.execute(stmt)
    return result.scalars().all(), total


async def get_payment(db: AsyncSession, payment_id: int) -> Payment:
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if not payment:
        raise NotFoundError("Payment not found")
    return payment
