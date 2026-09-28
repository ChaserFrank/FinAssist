from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SupportCaseCreate(BaseModel):
    transaction_reference: str
    message: str


class SupportCaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    reference: str
    transaction_reference: str
    customer_id: str
    message: str
    status: str
    response: str | None
    created_at: datetime
    resolved_at: datetime | None
