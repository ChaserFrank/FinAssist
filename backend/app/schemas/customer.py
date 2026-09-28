"""Customer API schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    reference: str
    name: str
    phone: str
    email: str
    created_at: datetime


class CustomerVerificationResponse(BaseModel):
    customer_reference: str
    transaction_reference: str
    verified: bool