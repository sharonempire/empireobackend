"""Payment model — matches the live `payments` table exactly.

DB schema (from Supabase):
  id              bigint PK auto-increment
  user_id         text NOT NULL           -- leadslist.id (string)
  order_id        text NOT NULL UNIQUE    -- Razorpay order_xxx or ios_rcpt_xxx
  payment_id      text                    -- Razorpay pay_xxx or apple_xxx
  signature       text                    -- Razorpay HMAC SHA256 or Apple transaction ID
  amount          integer NOT NULL        -- Amount in paise (INR × 100)
  currency        text NOT NULL DEFAULT 'INR'
  receipt         text NOT NULL UNIQUE    -- rcpt_xxx format
  status          text NOT NULL DEFAULT 'pending'  -- pending/completed/failed/refunded
  user_email      text
  description     text
  razorpay_order_response   jsonb         -- Full Razorpay order creation response
  razorpay_payment_response jsonb         -- Full Razorpay payment capture response
  error_message   text
  refund_id       text                    -- Razorpay rfnd_xxx
  refund_amount   integer                 -- Refund amount in paise
  created_at      timestamptz NOT NULL DEFAULT now()
  updated_at      timestamptz
  platform        text                    -- 'android', 'ios', 'web'

Indexes: payments_pkey, payments_order_id_key (UNIQUE), payments_receipt_key (UNIQUE)
No triggers.
"""

from sqlalchemy import BigInteger, Column, DateTime, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB

from app.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(Text, nullable=False)
    order_id = Column(Text, nullable=False, unique=True)
    payment_id = Column(Text, nullable=True)
    signature = Column(Text, nullable=True)
    amount = Column(Integer, nullable=False)  # Amount in paise (INR × 100)
    currency = Column(Text, nullable=False, default="INR")
    receipt = Column(Text, nullable=False, unique=True)
    status = Column(Text, nullable=False, default="pending")
    user_email = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    razorpay_order_response = Column(JSONB, nullable=True)
    razorpay_payment_response = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)
    refund_id = Column(Text, nullable=True)
    refund_amount = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=True)
    platform = Column(Text, nullable=True)
