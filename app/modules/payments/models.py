from sqlalchemy import BigInteger, Column, DateTime, Numeric, Text
from sqlalchemy.dialects.postgresql import JSONB

from app.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    amount = Column(Numeric, nullable=True)
    currency = Column(Text, nullable=True)
    status = Column(Text, nullable=True)
    payment_method = Column(Text, nullable=True)
    transaction_id = Column(Text, nullable=True)
    payment_details = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Missing column from audit
    platform = Column(Text, nullable=True)  # Payment platform

