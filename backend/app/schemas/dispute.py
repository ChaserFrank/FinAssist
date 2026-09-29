"""Dispute API schemas.

Pydantic models for the dispute resource.

Creating a dispute atomically produces both a ``SupportCase`` and a
``Dispute``.  The response exposes both references so callers can
track either entity without a second request.

Matches the contract documented in ``docs/api.md``.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.dispute.enums import DisputeStatus


class CreateDisputeRequest(BaseModel):
    """Request body for ``POST /api/v1/disputes``.

    ``POST /api/v1/disputes``::

        {
          "customer_reference": "CUS-10021",
          "transaction_reference": "TXN-84721",
          "reason": "Payment failed but account was charged"
        }
    """

    customer_reference: str = Field(..., examples=["CUS-10021"])
    transaction_reference: str = Field(..., examples=["TXN-84721"])
    reason: str = Field(..., min_length=1, examples=["Payment failed but account was charged"])


class DisputeResponse(BaseModel):
    """Response shape for dispute endpoints.

    ``POST /api/v1/disputes`` returns HTTP 201 with this body::

        {
          "reference": "DSP-1042",
          "support_case_reference": "CASE-1042",
          "status": "OPEN",
          "transaction_reference": "TXN-84721"
        }
    """

    model_config = ConfigDict(from_attributes=True)

    reference: str
    support_case_reference: str
    transaction_reference: str
    status: DisputeStatus
    reason: str
    created_at: datetime
