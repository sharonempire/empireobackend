"""Razorpay payment gateway integration.

Replaces the `razorpay-create-order` Supabase Edge Function with a proper
backend service that:
  1. Creates orders via Razorpay API (server-side, credentials never exposed)
  2. Verifies payment signatures using HMAC SHA256 (prevents tampering)
  3. Fetches payment details from Razorpay for reconciliation
  4. Processes refunds

Security improvements over the Edge Function:
  - API keys stored in environment variables, not hardcoded
  - Signature verification on the backend (not trusting client)
  - Webhook verification with Razorpay webhook secret
  - Idempotent order creation via receipt uniqueness
"""

import hashlib
import hmac
import logging
import time
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger("empireo.razorpay")

RAZORPAY_API_BASE = "https://api.razorpay.com/v1"


def _get_auth() -> tuple[str, str]:
    """Get Razorpay API credentials. Raises if not configured."""
    key_id = settings.RAZORPAY_KEY_ID
    key_secret = settings.RAZORPAY_KEY_SECRET
    if not key_id or not key_secret:
        raise RuntimeError("Razorpay credentials not configured (RAZORPAY_KEY_ID / RAZORPAY_KEY_SECRET)")
    return key_id, key_secret


def generate_receipt() -> str:
    """Generate a unique receipt ID matching the format used by the Flutter app."""
    import random
    timestamp = time.strftime("%Y%m%d%H%M%S")
    suffix = random.randint(1000, 9999)
    return f"rcpt_{timestamp}{suffix}"


def verify_payment_signature(order_id: str, payment_id: str, signature: str) -> bool:
    """Verify Razorpay payment signature using HMAC SHA256.

    Razorpay signs: "{order_id}|{payment_id}" with the key_secret.
    The client receives this signature and sends it back.
    We re-compute and compare to detect tampering.

    This is CRITICAL for payment security — without this, anyone could
    claim they paid by sending a fake payment_id.
    """
    _, key_secret = _get_auth()
    message = f"{order_id}|{payment_id}"
    expected = hmac.new(
        key_secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def verify_webhook_signature(body: bytes, signature: str) -> bool:
    """Verify Razorpay webhook signature.

    Razorpay signs the raw request body with the webhook secret.
    """
    webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET
    if not webhook_secret:
        logger.warning("RAZORPAY_WEBHOOK_SECRET not configured, skipping webhook verification")
        return False
    expected = hmac.new(
        webhook_secret.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


async def create_order(
    amount: int,
    currency: str = "INR",
    receipt: str | None = None,
) -> dict[str, Any]:
    """Create a Razorpay order via their API.

    Args:
        amount: Amount in paise (e.g., 6000 = ₹60.00)
        currency: Currency code (default INR)
        receipt: Unique receipt ID (auto-generated if not provided)

    Returns:
        Full Razorpay order response dict including order.id
    """
    key_id, key_secret = _get_auth()

    if receipt is None:
        receipt = generate_receipt()

    payload = {
        "amount": amount,
        "currency": currency,
        "receipt": receipt,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{RAZORPAY_API_BASE}/orders",
            json=payload,
            auth=(key_id, key_secret),
        )

    if resp.status_code != 200:
        error_body = resp.text
        logger.error("Razorpay order creation failed (%d): %s", resp.status_code, error_body[:500])
        raise RuntimeError(f"Razorpay order creation failed: {error_body[:500]}")

    order = resp.json()
    logger.info("Razorpay order created: %s (amount=%d %s)", order["id"], amount, currency)
    return order


async def fetch_payment(payment_id: str) -> dict[str, Any]:
    """Fetch payment details from Razorpay for reconciliation."""
    key_id, key_secret = _get_auth()

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{RAZORPAY_API_BASE}/payments/{payment_id}",
            auth=(key_id, key_secret),
        )

    if resp.status_code != 200:
        logger.error("Razorpay payment fetch failed (%d): %s", resp.status_code, resp.text[:500])
        raise RuntimeError(f"Failed to fetch payment {payment_id}")

    return resp.json()


async def create_refund(
    payment_id: str,
    amount: int | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    """Create a refund for a Razorpay payment.

    Args:
        payment_id: The Razorpay payment ID (pay_xxx)
        amount: Partial refund amount in paise. None = full refund.
        reason: Optional reason for the refund.

    Returns:
        Razorpay refund response dict.
    """
    key_id, key_secret = _get_auth()

    payload: dict[str, Any] = {}
    if amount is not None:
        payload["amount"] = amount
    if reason:
        payload["notes"] = {"reason": reason}

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{RAZORPAY_API_BASE}/payments/{payment_id}/refund",
            json=payload,
            auth=(key_id, key_secret),
        )

    if resp.status_code != 200:
        error_body = resp.text
        logger.error("Razorpay refund failed (%d): %s", resp.status_code, error_body[:500])
        raise RuntimeError(f"Razorpay refund failed: {error_body[:500]}")

    refund = resp.json()
    logger.info("Razorpay refund created: %s for payment %s", refund.get("id"), payment_id)
    return refund
