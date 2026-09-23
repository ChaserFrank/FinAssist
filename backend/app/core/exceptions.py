"""Application error-code vocabulary.

This module establishes the taxonomy of predictable error codes the API
will return, ahead of implementing the business logic that raises them.
Establishing the vocabulary first keeps error handling consistent once
routes, services, and the frontend all depend on it.

Deliberately not wired into any exception-handling middleware yet — no
route currently raises any of these. See docs/api.md for the response
envelope these codes are intended to populate:

    {
      "error": {
        "code": "TRANSACTION_NOT_FOUND",
        "message": "The requested transaction could not be found."
      }
    }
"""

from enum import StrEnum


class ErrorCode(StrEnum):
    """Predictable, documented error codes for the FinAssist API."""

    TRANSACTION_NOT_FOUND = "TRANSACTION_NOT_FOUND"
    CUSTOMER_NOT_FOUND = "CUSTOMER_NOT_FOUND"
    CUSTOMER_TRANSACTION_MISMATCH = "CUSTOMER_TRANSACTION_MISMATCH"
    INVALID_TRANSACTION_STATE = "INVALID_TRANSACTION_STATE"
    DISPUTE_NOT_ELIGIBLE = "DISPUTE_NOT_ELIGIBLE"
    SUPPORT_CASE_NOT_FOUND = "SUPPORT_CASE_NOT_FOUND"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AI_UNAVAILABLE = "AI_UNAVAILABLE"
    WORKFLOW_FAILED = "WORKFLOW_FAILED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
