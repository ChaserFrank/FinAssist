"""Support case API schemas.

Pydantic models for the support case resource.

``transaction_reference`` is optional on creation — a customer can open
a support case about a general issue before a specific transaction is
identified.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.application.message_service import MessageOutcome
from app.domain.support.enums import SupportCaseStatus
from app.domain.transaction.enums import TransactionStatus
from app.infrastructure.ai.ai_port import Intent


class CreateSupportCaseRequest(BaseModel):
    """Request body for ``POST /api/v1/support/cases``."""

    customer_reference: str = Field(..., examples=["CUS-10021"])
    transaction_reference: str | None = Field(None, examples=["TXN-84721"])
    category: str = Field(..., max_length=64, examples=["payment_dispute"])
    description: str = Field(..., min_length=1, examples=["Payment failed but I was charged."])


class SupportCaseResponse(BaseModel):
    """Response shape for support case endpoints."""

    model_config = ConfigDict(from_attributes=True)

    reference: str
    customer_reference: str
    transaction_reference: str | None
    category: str
    description: str
    status: SupportCaseStatus
    created_at: datetime


class SupportMessageRequest(BaseModel):
    """Request body for ``POST /api/v1/support/messages``.

    ``customer_reference`` identifies who is asking. There is no authentication
    yet, so this is a *claimed* identity (see docs/security.md): the backend
    still refuses to reveal or act on anything that does not belong to that
    customer, but it cannot prove the caller *is* that customer.
    """

    customer_reference: str = Field(..., min_length=1, max_length=32, examples=["CUS-10021"])
    message: str = Field(
        ..., min_length=1, max_length=2000,
        examples=["I was charged KSh 800 for TXN-84722 but the payment failed"],
    )


class TransactionSummary(BaseModel):
    """Backend-verified transaction facts included in a message response."""

    reference: str
    status: TransactionStatus
    amount: Decimal
    currency: str


class SupportMessageResponse(BaseModel):
    """Response for ``POST /api/v1/support/messages``.

    ``outcome`` is a stable value the UI can switch on; ``reply`` is text
    generated from backend data (never from AI output).
    """

    outcome: MessageOutcome
    intent: Intent
    reply: str
    transaction: TransactionSummary | None = None
    case_reference: str | None = None
    dispute_reference: str | None = None
    amount_mismatch: bool = False
