"""FastAPI application entrypoint.

This module is intentionally thin: it wires up application metadata and
routers only. No database access or business logic belongs here — see
`app/api/routes/` for endpoints and `app/application/` for use cases.
"""

from fastapi import FastAPI

from app.api.routes import health
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "AI-powered payment support and resolution agent. "
        "AI interprets. Orchestration coordinates. Backend authorizes. "
        "Database persists."
    ),
    version="0.1.0",
)

# --- Routers ---
app.include_router(health.router)

# Future routers (added once their respective domains are implemented):
# app.include_router(transactions.router, prefix="/api/v1")
# app.include_router(customers.router, prefix="/api/v1")
# app.include_router(support_cases.router, prefix="/api/v1")
# app.include_router(disputes.router, prefix="/api/v1")
