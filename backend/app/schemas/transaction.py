"""Transaction API schemas."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    reference: str
    customer_id: str
    amount: Decimal
    currency: str
    status: str
    payment_method: str
    description: str
    created_at: datetime
