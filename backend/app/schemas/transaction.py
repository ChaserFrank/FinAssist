"""Transaction API schemas.

Pydantic models for the transaction resource.  Monetary amounts are
returned as strings to preserve exact decimal representation across
language boundaries (avoids IEEE-754 float precision loss).
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.domain.transaction.enums import TransactionStatus


class TransactionResponse(BaseModel):
    """Response shape for ``GET /api/v1/transactions/{reference}``."""

    model_config = ConfigDict(from_attributes=True)

    reference: str
    customer_reference: str
    amount: Decimal
    currency: str
    status: TransactionStatus
    payment_method: str
    created_at: datetime
