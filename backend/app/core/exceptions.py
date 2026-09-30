"""Application error handling.

Defines the AppError exception and the FastAPI exception handler that
converts it into the documented error envelope:

    { "error": { "code": "...", "message": "..." } }

Usage (inside a service or route):

    raise AppError(ErrorCode.TRANSACTION_NOT_FOUND, "TXN-99999 not found.")

The handler is registered in ``app.main``.
"""

import logging
from enum import StrEnum
from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class ErrorCode(StrEnum):
    """Predictable, documented error codes for the FinAssist API."""

    TRANSACTION_NOT_FOUND = "TRANSACTION_NOT_FOUND"
    CUSTOMER_NOT_FOUND = "CUSTOMER_NOT_FOUND"
    CUSTOMER_TRANSACTION_MISMATCH = "CUSTOMER_TRANSACTION_MISMATCH"
    INVALID_TRANSACTION_STATE = "INVALID_TRANSACTION_STATE"
    DISPUTE_NOT_ELIGIBLE = "DISPUTE_NOT_ELIGIBLE"
    SUPPORT_CASE_NOT_FOUND = "SUPPORT_CASE_NOT_FOUND"
    DISPUTE_NOT_FOUND = "DISPUTE_NOT_FOUND"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AI_UNAVAILABLE = "AI_UNAVAILABLE"
    WORKFLOW_FAILED = "WORKFLOW_FAILED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


# Canonical HTTP status codes for each error code.
_HTTP_STATUS: dict[ErrorCode, int] = {
    ErrorCode.TRANSACTION_NOT_FOUND: 404,
    ErrorCode.CUSTOMER_NOT_FOUND: 404,
    ErrorCode.CUSTOMER_TRANSACTION_MISMATCH: 400,
    ErrorCode.INVALID_TRANSACTION_STATE: 422,
    ErrorCode.DISPUTE_NOT_ELIGIBLE: 409,
    ErrorCode.SUPPORT_CASE_NOT_FOUND: 404,
    ErrorCode.DISPUTE_NOT_FOUND: 404,
    ErrorCode.VALIDATION_ERROR: 422,
    ErrorCode.AI_UNAVAILABLE: 503,
    ErrorCode.WORKFLOW_FAILED: 502,
    ErrorCode.INTERNAL_ERROR: 500,
}


class AppError(Exception):
    """Domain exception raised by application services.

    Routes and services raise this; the ``app_error_handler`` converts it
    to the standard error envelope before the response reaches the client.

    Args:
        code:    ``ErrorCode`` enum value identifying the problem type.
        message: Human-readable explanation suitable for an API consumer.
    """

    def __init__(self, code: ErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code: int = _HTTP_STATUS.get(code, 500)


def _error_body(code: ErrorCode, message: str) -> dict[str, Any]:
    return {"error": {"code": str(code), "message": message}}


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """FastAPI exception handler for ``AppError``.

    Registered in ``app.main`` via::

        app.add_exception_handler(AppError, app_error_handler)
    """
    if exc.status_code >= 500:
        logger.error("AppError %s on %s %s", exc.code, request.method, request.url.path)
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_body(exc.code, exc.message),
    )


async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Map FastAPI/Pydantic request validation failures onto the same error
    envelope as every other error, so clients handle exactly one shape.

    Only the field location and the validation message are returned -- never
    the submitted values, which may contain personal data.
    """
    problems = "; ".join(
        f"{'.'.join(str(part) for part in err['loc'] if part != 'body')}: {err['msg']}"
        for err in exc.errors()
    )
    return JSONResponse(
        status_code=_HTTP_STATUS[ErrorCode.VALIDATION_ERROR],
        content=_error_body(ErrorCode.VALIDATION_ERROR, f"Invalid request. {problems}"),
    )


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler for unexpected exceptions.

    Prevents raw tracebacks reaching the client, but the failure is *always*
    logged with its traceback so it can be diagnosed. Only method and path are
    logged (not the query string or body, which may hold personal data).
    """
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content=_error_body(
            ErrorCode.INTERNAL_ERROR,
            "An unexpected error occurred. Please try again later.",
        ),
    )
