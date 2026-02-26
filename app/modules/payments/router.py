"""Payment endpoints — Razorpay order creation, verification, webhooks, refunds.

Security:
  - Order creation: authenticated staff only (require_perm)
  - Payment verification: HMAC SHA256 signature check
  - Webhook: Razorpay webhook signature verification (no JWT needed)
  - Refund: admin/manager permission required
  - Razorpay API keys never exposed to client
"""

import logging

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import log_event
from app.core.pagination import PaginatedResponse, paginate_metadata
from app.database import get_db
from app.dependencies import require_perm
from app.modules.payments import service
from app.modules.payments.schemas import (
    CreateOrderRequest,
    PaymentDetailOut,
    PaymentOut,
    RecordIOSPaymentRequest,
    RefundRequest,
    VerifyPaymentRequest,
)
from app.modules.users.models import User

logger = logging.getLogger("empireo.payments.router")

router = APIRouter(prefix="/payments", tags=["Payments"])

# Separate router for webhook — NO JWT/RBAC (Razorpay can't send JWTs)
# This router is mounted directly in main.py without include_router_with_default
webhook_router = APIRouter(prefix="/payments", tags=["Payments Webhooks"])


# ── List / Get ───────────────────────────────────────────────────────


@router.get("/", response_model=PaginatedResponse[PaymentOut])
async def api_list_payments(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=500),
    status: str | None = None,
    user_id: str | None = None,
    platform: str | None = None,
    current_user: User = Depends(require_perm("payments", "read")),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_payments(db, page, size, status, user_id, platform)
    return {**paginate_metadata(total, page, size), "items": items}


@router.get("/stats")
async def api_payment_stats(
    current_user: User = Depends(require_perm("payments", "read")),
    db: AsyncSession = Depends(get_db),
):
    """Payment statistics: total revenue, counts by status/platform."""
    return await service.get_payment_stats(db)


@router.get("/{payment_id}", response_model=PaymentDetailOut)
async def api_get_payment(
    payment_id: int,
    current_user: User = Depends(require_perm("payments", "read")),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_payment(db, payment_id)


# ── Create Razorpay Order ────────────────────────────────────────────
# Replaces the `razorpay-create-order` Supabase Edge Function


@router.post("/create-order", response_model=PaymentOut, status_code=201)
async def api_create_order(
    data: CreateOrderRequest,
    current_user: User = Depends(require_perm("payments", "create")),
    db: AsyncSession = Depends(get_db),
):
    """Create a Razorpay order.

    Replaces the `razorpay-create-order` Edge Function. Key improvements:
    - Razorpay API keys stored server-side in env vars (not hardcoded)
    - Amount validated server-side
    - Full order response stored for audit trail
    - Proper auth via JWT + RBAC

    Returns the payment record. Client uses `order_id` to open Razorpay checkout.
    """
    payment = await service.create_order(
        db=db,
        user_id=data.user_id,
        amount=data.amount,
        currency=data.currency,
        description=data.description,
        user_email=data.user_email,
        platform=data.platform,
    )
    await log_event(db, "payment.order_created", current_user.id, "payment", str(payment.id), {
        "order_id": payment.order_id,
        "amount": payment.amount,
        "user_id": data.user_id,
    })
    await db.commit()
    return payment


# ── Verify Payment (CRITICAL) ────────────────────────────────────────


@router.post("/verify", response_model=PaymentOut)
async def api_verify_payment(
    data: VerifyPaymentRequest,
    current_user: User = Depends(require_perm("payments", "create")),
    db: AsyncSession = Depends(get_db),
):
    """Verify a Razorpay payment after checkout completion.

    CRITICAL SECURITY: Verifies the HMAC SHA256 signature to confirm the
    payment was actually processed by Razorpay and not tampered with.

    The client sends: order_id, payment_id, signature (from Razorpay SDK callback).
    We verify: HMAC_SHA256(order_id|payment_id, key_secret) == signature.

    Also fetches payment details from Razorpay API and verifies amount matches.
    """
    payment = await service.verify_payment(
        db=db,
        order_id=data.order_id,
        payment_id=data.payment_id,
        signature=data.signature,
    )
    await log_event(db, "payment.verified", current_user.id, "payment", str(payment.id), {
        "order_id": data.order_id,
        "payment_id": data.payment_id,
        "status": payment.status,
    })
    await db.commit()
    return payment


# ── iOS In-App Purchase ──────────────────────────────────────────────


@router.post("/ios", response_model=PaymentOut, status_code=201)
async def api_record_ios_payment(
    data: RecordIOSPaymentRequest,
    current_user: User = Depends(require_perm("payments", "create")),
    db: AsyncSession = Depends(get_db),
):
    """Record an iOS In-App Purchase (StoreKit 2) for bookkeeping.

    Apple IAP is verified client-side. This just stores the transaction.
    """
    payment = await service.record_ios_payment(
        db=db,
        user_id=data.user_id,
        amount=data.amount,
        currency=data.currency,
        apple_transaction_id=data.apple_transaction_id,
        product_id=data.product_id,
        description=data.description,
        user_email=data.user_email,
    )
    await log_event(db, "payment.ios_recorded", current_user.id, "payment", str(payment.id), {
        "apple_transaction_id": data.apple_transaction_id,
        "product_id": data.product_id,
        "amount": data.amount,
    })
    await db.commit()
    return payment


# ── Razorpay Webhook ─────────────────────────────────────────────────


@webhook_router.post("/webhook/razorpay")
async def api_razorpay_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Razorpay webhook handler — receives payment events.

    NO JWT auth required (Razorpay can't send JWTs). Instead, we verify
    the webhook signature using HMAC SHA256 with the webhook secret.

    Handles: payment.captured, payment.failed, refund.created
    """
    from fastapi.responses import JSONResponse as _JSONResponse

    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")

    # SECURITY: Reject requests without a valid signature
    if not signature:
        logger.warning("Razorpay webhook received without signature header")
        return _JSONResponse(status_code=401, content={"status": "missing_signature"})

    from app.core.razorpay_service import verify_webhook_signature

    if not verify_webhook_signature(body, signature):
        logger.warning("Razorpay webhook signature verification FAILED")
        return _JSONResponse(status_code=401, content={"status": "signature_invalid"})

    import json
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return _JSONResponse(status_code=400, content={"status": "invalid_json"})

    event_type = payload.get("event", "")
    event_payload = payload.get("payload", {})

    result = await service.process_webhook(db, event_type, event_payload)
    await db.commit()

    logger.info("Razorpay webhook processed: %s", event_type)
    return result


# ── Refund ───────────────────────────────────────────────────────────


@router.post("/{payment_id}/refund", response_model=PaymentOut)
async def api_refund_payment(
    payment_id: int,
    data: RefundRequest,
    current_user: User = Depends(require_perm("payments", "delete")),
    db: AsyncSession = Depends(get_db),
):
    """Initiate a refund for a completed Razorpay payment.

    Requires 'payments:delete' permission (admin/manager only).
    Calls the Razorpay refund API and records the refund in DB.
    """
    payment = await service.initiate_refund(
        db=db,
        payment_id_db=payment_id,
        amount=data.amount,
        reason=data.reason,
    )
    await log_event(db, "payment.refunded", current_user.id, "payment", str(payment_id), {
        "refund_id": payment.refund_id,
        "refund_amount": payment.refund_amount,
        "reason": data.reason,
    })
    await db.commit()
    return payment
