from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PaymentOut(BaseModel):
    """Full payment record response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: str
    order_id: str
    payment_id: str | None = None
    amount: int  # paise
    currency: str = "INR"
    receipt: str
    status: str
    user_email: str | None = None
    description: str | None = None
    platform: str | None = None
    error_message: str | None = None
    refund_id: str | None = None
    refund_amount: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def amount_inr(self) -> float:
        return self.amount / 100.0


class PaymentDetailOut(PaymentOut):
    """Full payment with Razorpay response data (admin view)."""
    razorpay_order_response: Any | None = None
    razorpay_payment_response: Any | None = None
    signature: str | None = None


# ── Request Schemas ──────────────────────────────────────────────────


class CreateOrderRequest(BaseModel):
    """Create a Razorpay order. Amount in paise (INR × 100).

    Example: amount=6000 means ₹60.00
    """
    user_id: str
    amount: int = Field(..., gt=0, description="Amount in paise (INR × 100)")
    currency: str = "INR"
    description: str | None = None
    user_email: str | None = None
    platform: str | None = Field(None, pattern="^(android|ios|web)$")


class VerifyPaymentRequest(BaseModel):
    """Verify a Razorpay payment after checkout completion.

    The client sends back the payment details from Razorpay SDK callback.
    We verify the signature using HMAC SHA256 to prevent tampering.
    """
    order_id: str
    payment_id: str
    signature: str


class RecordIOSPaymentRequest(BaseModel):
    """Record an iOS In-App Purchase payment.

    Apple IAP transactions are verified client-side via StoreKit 2.
    We record the transaction for bookkeeping.
    """
    user_id: str
    amount: int = Field(..., gt=0)
    currency: str = "INR"
    apple_transaction_id: str
    product_id: str
    description: str | None = None
    user_email: str | None = None


class RefundRequest(BaseModel):
    """Initiate a refund for a completed Razorpay payment."""
    amount: int | None = Field(None, gt=0, description="Partial refund amount in paise. Omit for full refund.")
    reason: str | None = None
