"""Support case routes.

HTTP layer only — no business logic, no direct database access.
All work is delegated to SupportService.
"""

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_support_service
from app.application.support_service import SupportService
from app.schemas.support import CreateSupportCaseRequest, SupportCaseResponse

router = APIRouter(prefix="/support/cases", tags=["support_cases"])


@router.post("", response_model=SupportCaseResponse, status_code=status.HTTP_201_CREATED)
def create_support_case(
    body: CreateSupportCaseRequest,
    service: SupportService = Depends(get_support_service),
) -> SupportCaseResponse:
    """Open a new support case.

    The ``transaction_reference`` is optional.  If provided, the transaction
    must belong to the given customer.

    Raises HTTP 404 (CUSTOMER_NOT_FOUND | TRANSACTION_NOT_FOUND) or
    HTTP 400 (CUSTOMER_TRANSACTION_MISMATCH) on validation failure.
    """
    case = service.create_case(
        customer_reference=body.customer_reference,
        category=body.category,
        description=body.description,
        transaction_reference=body.transaction_reference,
    )

    return SupportCaseResponse(
        reference=case.reference,
        customer_reference=case.customer.reference,
        transaction_reference=(
            case.transaction.reference if case.transaction else None
        ),
        category=case.category,
        description=case.description,
        status=case.status,
        created_at=case.created_at,
    )


@router.get("/{reference}", response_model=SupportCaseResponse)
def get_support_case(
    reference: str,
    service: SupportService = Depends(get_support_service),
) -> SupportCaseResponse:
    """Retrieve a support case by its reference.

    Raises HTTP 404 (SUPPORT_CASE_NOT_FOUND) if not found.
    """
    case = service.get_case(reference)
    return SupportCaseResponse(
        reference=case.reference,
        customer_reference=case.customer.reference,
        transaction_reference=(
            case.transaction.reference if case.transaction else None
        ),
        category=case.category,
        description=case.description,
        status=case.status,
        created_at=case.created_at,
    )
