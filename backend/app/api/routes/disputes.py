"""Dispute routes.

HTTP layer only — no business logic, no direct database access.
All work is delegated to DisputeService.

POST /disputes creates both a SupportCase and a Dispute atomically;
the response includes both references so callers can track either entity.
"""

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_dispute_service
from app.application.dispute_service import DisputeService
from app.schemas.dispute import CreateDisputeRequest, DisputeResponse

router = APIRouter(prefix="/disputes", tags=["disputes"])


@router.post("", response_model=DisputeResponse, status_code=status.HTTP_201_CREATED)
def create_dispute(
    body: CreateDisputeRequest,
    service: DisputeService = Depends(get_dispute_service),
) -> DisputeResponse:
    """Raise a formal dispute against a transaction.

    Atomically creates a SupportCase and a Dispute.  The response contains
    both references.

    Possible error responses:
    - 404 TRANSACTION_NOT_FOUND
    - 404 CUSTOMER_NOT_FOUND
    - 400 CUSTOMER_TRANSACTION_MISMATCH
    - 422 INVALID_TRANSACTION_STATE  (PENDING or REVERSED transaction)
    - 409 DISPUTE_NOT_ELIGIBLE       (active or prior dispute exists)
    """
    dispute = service.create_dispute(
        customer_reference=body.customer_reference,
        transaction_reference=body.transaction_reference,
        reason=body.reason,
    )

    return DisputeResponse(
        reference=dispute.reference,
        support_case_reference=dispute.support_case.reference,
        transaction_reference=dispute.transaction.reference,
        status=dispute.status,
        reason=dispute.reason,
        created_at=dispute.created_at,
    )


@router.get("/{reference}", response_model=DisputeResponse)
def get_dispute(
    reference: str,
    service: DisputeService = Depends(get_dispute_service),
) -> DisputeResponse:
    """Retrieve a dispute by its reference (e.g. DSP-1042).

    Raises HTTP 404 (DISPUTE_NOT_FOUND) if not found.
    """
    dispute = service.get_dispute(reference)
    return DisputeResponse(
        reference=dispute.reference,
        support_case_reference=dispute.support_case.reference,
        transaction_reference=dispute.transaction.reference,
        status=dispute.status,
        reason=dispute.reason,
        created_at=dispute.created_at,
    )
