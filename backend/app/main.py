"""FastAPI application entrypoint.

This module is intentionally thin: it wires up application metadata,
routers, exception handlers, and middleware only.  No database access
or business logic belongs here — see ``app/api/routes/`` for endpoints
and ``app/application/`` for use cases.
"""

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    customers,
    disputes,
    health,
    support_cases,
    support_messages,
    transactions,
)
from app.config import get_settings
from app.core.exceptions import (
    AppError,
    app_error_handler,
    unhandled_error_handler,
    validation_error_handler,
)
from app.core.logging import configure_logging

settings = get_settings()
configure_logging(settings.LOG_LEVEL)

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "AI-powered payment support and resolution agent. "
        "AI interprets. Orchestration coordinates. Backend authorizes. "
        "Database persists."
    ),
    version="0.1.0",
)

# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------
app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]
app.add_exception_handler(
    RequestValidationError, validation_error_handler  # type: ignore[arg-type]
)
app.add_exception_handler(Exception, unhandled_error_handler)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
# CORS: origins come from configuration (CORS_ORIGINS), defaulting to the Vite
# dev server. Set it explicitly for any other deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(health.router)
app.include_router(transactions.router, prefix="/api/v1")
app.include_router(customers.router, prefix="/api/v1")
app.include_router(support_cases.router, prefix="/api/v1")
app.include_router(support_messages.router, prefix="/api/v1")
app.include_router(disputes.router, prefix="/api/v1")
