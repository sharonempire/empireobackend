from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    status: Optional[str] = None
    payment_method: Optional[str] = None
    transaction_id: Optional[str] = None
    payment_details: Optional[Any] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    platform: Optional[str] = None
