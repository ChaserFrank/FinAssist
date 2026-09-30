"""Shared FastAPI dependencies (DI providers).

Each dependency function yields or returns the object needed by a route.
Routes declare them via ``Depends()``.  The session dependency follows
the standard FastAPI pattern: one session per request, closed on teardown.

Services are constructed per-request; they are cheap to build and
stateless beyond the injected session.
"""

from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.application.customer_service import CustomerService
from app.application.dispute_service import DisputeService
from app.application.message_service import SupportMessageService
from app.application.support_service import SupportService
from app.application.transaction_service import TransactionService
from app.infrastructure.ai.mock_ai_service import MockAIService
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.orchestration.local_workflow_adapter import LocalWorkflowAdapter

# ---------------------------------------------------------------------------
# Database session
# ---------------------------------------------------------------------------

def get_db() -> Generator[Session, None, None]:
    """Yield a database session for the lifetime of a single request.

    Services own commit/rollback for writes (ADR-006); this dependency only
    guarantees the session is always closed.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Application services
# ---------------------------------------------------------------------------

def get_customer_service(db: Session = Depends(get_db)) -> CustomerService:
    return CustomerService(db)


def get_transaction_service(db: Session = Depends(get_db)) -> TransactionService:
    return TransactionService(db)


def get_support_service(db: Session = Depends(get_db)) -> SupportService:
    return SupportService(db)


def get_dispute_service(db: Session = Depends(get_db)) -> DisputeService:
    return DisputeService(db)


def get_message_service(db: Session = Depends(get_db)) -> SupportMessageService:
    """Wire the message flow with the local (offline) AI and workflow adapters.

    Swap in ``WatsonXAIService`` / ``WatsonOrchestrateAdapter`` here once the
    IBM TechZone environment is available (ADR-003); nothing else changes.
    """
    return SupportMessageService(ai=MockAIService(), workflow=LocalWorkflowAdapter(db))
