"""Transaction routes.

HTTP layer only — no business logic, no direct database access.
All work is delegated to TransactionService.
"""

from fastapi import APIRouter, Depends

from app.api.dependencies import get_transaction_service
from app.application.transaction_service import TransactionService
from app.schemas.transaction import TransactionResponse

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("/{reference}", response_model=TransactionResponse)
def get_transaction(
    reference: str,
    service: TransactionService = Depends(get_transaction_service),
) -> TransactionResponse:
    """Retrieve a transaction by its human-friendly reference.

    Raises HTTP 404 (TRANSACTION_NOT_FOUND) if the reference does not exist.
    """
    txn = service.get_transaction(reference)
    return TransactionResponse(
        reference=txn.reference,
        customer_reference=txn.customer.reference,
        amount=txn.amount,
        currency=txn.currency,
        status=txn.status,
        payment_method=txn.payment_method,
        created_at=txn.created_at,
    )
