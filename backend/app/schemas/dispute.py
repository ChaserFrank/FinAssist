"""Dispute API schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DisputeCreate(BaseModel):
    customer_reference: str
    transaction_reference: str
    reason: str


class DisputeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    reference: str
    support_case_reference: str
    transaction_reference: str
    reason: str
    status: str
    created_at: datetime