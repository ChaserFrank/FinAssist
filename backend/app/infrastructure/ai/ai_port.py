"""AI service port.

Defines the contract the application layer uses to interpret a customer's
natural-language message, independent of which provider implements it.
Local development uses ``MockAIService``; ``WatsonXAIService`` slots in later
with no application-layer change (docs/decisions/003-local-first-integration.md).

Untrusted-input principle (docs/decisions/002-ai-backend-boundary.md)
--------------------------------------------------------------------
Whatever a model returns is *untrusted input*. It is parsed into
``AIInterpretation``, which enforces the allowed intents and the shape of
every reference. Anything that fails validation is discarded and treated as
``Intent.UNKNOWN`` -- the system never acts on malformed AI output. Even a
well-formed interpretation is only a hint: the backend re-reads every entity
from the database and never trusts an AI-extracted amount or ownership.
"""

import logging
import re
from decimal import Decimal
from enum import StrEnum
from typing import Any, Protocol

from pydantic import BaseModel, Field, ValidationError, field_validator

logger = logging.getLogger(__name__)

_TXN_REFERENCE = re.compile(r"^TXN-\d{4,9}$")
_CASE_REFERENCE = re.compile(r"^CASE-\d{4,9}$")


class Intent(StrEnum):
    """The closed set of intents the system understands (see docs/ai.md)."""

    TRANSACTION_STATUS = "transaction_status"
    PAYMENT_FAILED = "payment_failed"
    PAYMENT_DISPUTE = "payment_dispute"
    SUPPORT_CASE_STATUS = "support_case_status"
    UNKNOWN = "unknown"


class AIInterpretation(BaseModel):
    """Validated structured interpretation of one customer message."""

    intent: Intent = Intent.UNKNOWN
    transaction_reference: str | None = None
    case_reference: str | None = None
    amount: Decimal | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    requires_transaction_lookup: bool = False

    @field_validator("transaction_reference")
    @classmethod
    def _check_txn_reference(cls, value: str | None) -> str | None:
        if value is not None and not _TXN_REFERENCE.match(value):
            raise ValueError("malformed transaction reference")
        return value

    @field_validator("case_reference")
    @classmethod
    def _check_case_reference(cls, value: str | None) -> str | None:
        if value is not None and not _CASE_REFERENCE.match(value):
            raise ValueError("malformed case reference")
        return value


UNKNOWN_INTERPRETATION = AIInterpretation()


def parse_ai_output(raw: Any) -> AIInterpretation:
    """Validate raw model output; fall back to ``unknown`` if it is invalid.

    This is the single choke point every real provider adapter must pass its
    output through. It never raises: invalid output is logged (without the
    payload, which could echo customer text) and neutralised.
    """
    try:
        return AIInterpretation.model_validate(raw)
    except ValidationError:
        logger.warning("Discarded malformed AI output; treating intent as unknown")
        return UNKNOWN_INTERPRETATION


class AIService(Protocol):
    """Contract for turning a customer message into a validated interpretation."""

    def analyze(self, message: str) -> AIInterpretation:
        """Interpret ``message``. ``Intent.UNKNOWN`` is a valid, expected answer."""
        ...
