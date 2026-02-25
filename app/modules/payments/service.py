"""Payments service layer — Razorpay + iOS IAP.

Handles the full payment lifecycle:
  1. create_order     — Create Razorpay order + DB record (replaces Edge Function)
  2. verify_payment   — Verify signature + mark as completed (CRITICAL security)
  3. record_ios_payment — Record Apple IAP transaction
  4. process_webhook  — Handle Razorpay webhook events
  5. initiate_refund  — Refund via Razorpay API
  6. list/get/stats   — Read operations

Security:
  - Signature verification via HMAC SHA256 prevents fake payments
  - Webhook verification ensures events come from Razorpay
  - Idempotent: duplicate order_id/receipt are rejected by UNIQUE constraints
  - Amount is always server-authoritative (never trust client amount)
"""

import logging
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.core.razorpay_service import (
    create_order as razorpay_create_order,
    create_refund as razorpay_create_refund,
    fetch_payment as razorpay_fetch_payment,
    generate_receipt,
    verify_payment_signature,
)
from app.modules.payments.models import Payment

logger = logging.getLogger("empireo.payments")


# ── Read Operations ──────────────────────────────────────────────────


async def list_payments(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    status: str | None = None,
    user_id: str | None = None,
    platform: str | None = None,
) -> tuple[list[Payment], int]:
    stmt = select(Payment)
    count_stmt = select(func.count()).select_from(Payment)

    if status:
        stmt = stmt.where(Payment.status == status)
        count_stmt = count_stmt.where(Payment.status == status)
    if user_id:
        stmt = stmt.where(Payment.user_id == user_id)
        count_stmt = count_stmt.where(Payment.user_id == user_id)
    if platform:
        stmt = stmt.where(Payment.platform == platform)
        count_stmt = count_stmt.where(Payment.platform == platform)

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


async def get_payment_by_order_id(db: AsyncSession, order_id: str) -> Payment | None:
    result = await db.execute(select(Payment).where(Payment.order_id == order_id))
    return result.scalar_one_or_none()


# ── Create Razorpay Order ────────────────────────────────────────────


async def create_order(
    db: AsyncSession,
    user_id: str,
    amount: int,
    currency: str = "INR",
    description: str | None = None,
    user_email: str | None = None,
    platform: str | None = None,
) -> Payment:
    """Create a Razorpay order and store the payment record.

    This replaces the `razorpay-create-order` Edge Function.

    Steps:
    1. Generate a unique receipt
    2. Call Razorpay API to create the order (server-side, keys never exposed)
    3. Store the order + full Razorpay response in DB
    4. Return the payment record (client uses order_id for Razorpay checkout)
    """
    receipt = generate_receipt()

    # Call Razorpay API
    razorpay_order = await razorpay_create_order(amount, currency, receipt)

    order_id = razorpay_order["id"]

    # Check for duplicate (idempotency)
    existing = await get_payment_by_order_id(db, order_id)
    if existing:
        raise ConflictError(f"Order {order_id} already exists")

    # Store in DB
    payment = Payment(
        user_id=user_id,
        order_id=order_id,
        amount=amount,
        currency=currency,
        receipt=receipt,
        status="pending",
        user_email=user_email,
        description=description,
        platform=platform,
        razorpay_order_response=razorpay_order,
        created_at=datetime.now(timezone.utc),
    )
    db.add(payment)
    await db.flush()
    await db.refresh(payment)

    logger.info(
        "Payment order created: id=%d order_id=%s user=%s amount=%d",
        payment.id, order_id, user_id, amount,
    )
    return payment


# ── Verify Payment (CRITICAL SECURITY) ──────────────────────────────


async def verify_payment(
    db: AsyncSession,
    order_id: str,
    payment_id: str,
    signature: str,
) -> Payment:
    """Verify a Razorpay payment after checkout and mark as completed.

    This is the MOST CRITICAL security function:
    1. Look up the order in our DB
    2. Verify the signature using HMAC SHA256 (prevents fake payments)
    3. Optionally fetch payment details from Razorpay for reconciliation
    4. Mark as completed

    If signature verification fails, the payment is marked as FAILED.
    """
    # Find the pending order
    payment = await get_payment_by_order_id(db, order_id)
    if not payment:
        raise NotFoundError(f"Order {order_id} not found")

    if payment.status == "completed":
        logger.info("Payment %s already completed, returning existing", order_id)
        return payment

    if payment.status not in ("pending", "failed"):
        raise BadRequestError(f"Payment in unexpected status: {payment.status}")

    # CRITICAL: Verify the Razorpay signature
    if not verify_payment_signature(order_id, payment_id, signature):
        logger.warning(
            "PAYMENT SIGNATURE VERIFICATION FAILED: order=%s payment=%s user=%s",
            order_id, payment_id, payment.user_id,
        )
        payment.status = "failed"
        payment.error_message = "Signature verification failed — possible tampering"
        payment.payment_id = payment_id
        payment.signature = signature
        payment.updated_at = datetime.now(timezone.utc)
        await db.flush()
        raise BadRequestError("Payment signature verification failed")

    # Signature valid — fetch payment details from Razorpay for reconciliation
    razorpay_payment = None
    try:
        razorpay_payment = await razorpay_fetch_payment(payment_id)
    except Exception as e:
        logger.warning("Failed to fetch Razorpay payment details: %s", e)

    # Verify amount matches (server-authoritative)
    if razorpay_payment:
        rp_amount = razorpay_payment.get("amount")
        if rp_amount is not None and rp_amount != payment.amount:
            logger.warning(
                "AMOUNT MISMATCH: order=%s expected=%d razorpay=%d",
                order_id, payment.amount, rp_amount,
            )
            payment.status = "failed"
            payment.error_message = f"Amount mismatch: expected {payment.amount}, got {rp_amount}"
            payment.payment_id = payment_id
            payment.signature = signature
            payment.razorpay_payment_response = razorpay_payment
            payment.updated_at = datetime.now(timezone.utc)
            await db.flush()
            raise BadRequestError("Payment amount mismatch")

    # All checks passed — mark as completed
    payment.payment_id = payment_id
    payment.signature = signature
    payment.status = "completed"
    payment.razorpay_payment_response = razorpay_payment
    payment.updated_at = datetime.now(timezone.utc)
    await db.flush()

    logger.info(
        "Payment verified and completed: order=%s payment=%s amount=%d user=%s",
        order_id, payment_id, payment.amount, payment.user_id,
    )
    return payment


# ── Record iOS IAP ───────────────────────────────────────────────────


async def record_ios_payment(
    db: AsyncSession,
    user_id: str,
    amount: int,
    currency: str,
    apple_transaction_id: str,
    product_id: str,
    description: str | None = None,
    user_email: str | None = None,
) -> Payment:
    """Record an iOS In-App Purchase for bookkeeping.

    Apple IAP transactions are verified client-side via StoreKit 2.
    We just store the record.
    """
    receipt = f"ios_rcpt_{generate_receipt().split('_', 1)[1]}"
    order_id = receipt  # iOS uses receipt as order_id

    # Check for duplicate Apple transaction
    existing = await db.execute(
        select(Payment).where(Payment.payment_id == f"apple_{apple_transaction_id}")
    )
    if existing.scalar_one_or_none():
        raise ConflictError(f"Apple transaction {apple_transaction_id} already recorded")

    payment = Payment(
        user_id=user_id,
        order_id=order_id,
        payment_id=f"apple_{apple_transaction_id}",
        signature=apple_transaction_id,
        amount=amount,
        currency=currency,
        receipt=receipt,
        status="completed",
        user_email=user_email,
        description=description,
        platform="ios",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(payment)
    await db.flush()
    await db.refresh(payment)

    logger.info(
        "iOS payment recorded: id=%d apple_txn=%s user=%s amount=%d",
        payment.id, apple_transaction_id, user_id, amount,
    )
    return payment


# ── Razorpay Webhook ─────────────────────────────────────────────────


async def process_webhook(
    db: AsyncSession,
    event_type: str,
    payload: dict,
) -> dict:
    """Process a verified Razorpay webhook event.

    Handles:
    - payment.captured  → Mark as completed
    - payment.failed    → Mark as failed
    - refund.created    → Record refund
    """
    result = {"event": event_type, "status": "processed"}

    if event_type == "payment.captured":
        payment_entity = payload.get("payment", {}).get("entity", {})
        rp_order_id = payment_entity.get("order_id")
        rp_payment_id = payment_entity.get("id")

        if rp_order_id:
            payment = await get_payment_by_order_id(db, rp_order_id)
            if payment and payment.status == "pending":
                payment.payment_id = rp_payment_id
                payment.status = "completed"
                payment.razorpay_payment_response = payment_entity
                payment.updated_at = datetime.now(timezone.utc)
                await db.flush()
                result["payment_id"] = payment.id
                logger.info("Webhook: payment.captured for order %s", rp_order_id)

    elif event_type == "payment.failed":
        payment_entity = payload.get("payment", {}).get("entity", {})
        rp_order_id = payment_entity.get("order_id")

        if rp_order_id:
            payment = await get_payment_by_order_id(db, rp_order_id)
            if payment and payment.status == "pending":
                payment.status = "failed"
                payment.error_message = payment_entity.get("error_description", "Payment failed")
                payment.razorpay_payment_response = payment_entity
                payment.updated_at = datetime.now(timezone.utc)
                await db.flush()
                result["payment_id"] = payment.id
                logger.info("Webhook: payment.failed for order %s", rp_order_id)

    elif event_type == "refund.created":
        refund_entity = payload.get("refund", {}).get("entity", {})
        rp_payment_id = refund_entity.get("payment_id")

        if rp_payment_id:
            pay_result = await db.execute(
                select(Payment).where(Payment.payment_id == rp_payment_id)
            )
            payment = pay_result.scalar_one_or_none()
            if payment:
                payment.refund_id = refund_entity.get("id")
                payment.refund_amount = refund_entity.get("amount")
                payment.status = "refunded"
                payment.updated_at = datetime.now(timezone.utc)
                await db.flush()
                result["payment_id"] = payment.id
                logger.info("Webhook: refund.created for payment %s", rp_payment_id)

    return result


# ── Refund ───────────────────────────────────────────────────────────


async def initiate_refund(
    db: AsyncSession,
    payment_id_db: int,
    amount: int | None = None,
    reason: str | None = None,
) -> Payment:
    """Initiate a refund for a completed payment via Razorpay API."""
    payment = await get_payment(db, payment_id_db)

    if payment.status != "completed":
        raise BadRequestError(f"Cannot refund payment in status: {payment.status}")

    if not payment.payment_id or not payment.payment_id.startswith("pay_"):
        raise BadRequestError("Cannot refund non-Razorpay payment via API")

    if payment.refund_id:
        raise ConflictError("Payment already has a refund")

    # Call Razorpay refund API
    refund = await razorpay_create_refund(payment.payment_id, amount, reason)

    payment.refund_id = refund.get("id")
    payment.refund_amount = refund.get("amount", amount or payment.amount)
    payment.status = "refunded"
    payment.updated_at = datetime.now(timezone.utc)
    await db.flush()

    logger.info(
        "Refund initiated: payment=%d refund=%s amount=%s",
        payment_id_db, payment.refund_id, payment.refund_amount,
    )
    return payment


# ── Stats ────────────────────────────────────────────────────────────


async def get_payment_stats(db: AsyncSession) -> dict:
    """Payment statistics: total revenue, counts by status/platform."""
    # By status
    status_q = await db.execute(
        select(Payment.status, func.count(), func.coalesce(func.sum(Payment.amount), 0))
        .group_by(Payment.status)
    )
    by_status = {}
    total_revenue_paise = 0
    for status, count, total_amount in status_q.all():
        by_status[status] = {"count": count, "total_paise": int(total_amount)}
        if status == "completed":
            total_revenue_paise = int(total_amount)

    # By platform
    platform_q = await db.execute(
        select(Payment.platform, func.count(), func.coalesce(func.sum(Payment.amount), 0))
        .where(Payment.status == "completed")
        .group_by(Payment.platform)
    )
    by_platform = {}
    for platform, count, total_amount in platform_q.all():
        by_platform[platform or "unknown"] = {"count": count, "total_paise": int(total_amount)}

    return {
        "total_revenue_paise": total_revenue_paise,
        "total_revenue_inr": round(total_revenue_paise / 100.0, 2),
        "by_status": by_status,
        "by_platform": by_platform,
    }
