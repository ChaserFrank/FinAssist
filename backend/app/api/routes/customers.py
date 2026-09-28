"""Customer API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.application.customer_service import get_customer
from app.application.transaction_service import verify_transaction_customer
from app.core.exceptions import NotFoundError
from app.schemas.customer import CustomerResponse, CustomerVerificationResponse

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get(
    "/{reference}",
    response_model=CustomerResponse,
)
def lookup_customer(
    reference: str,
    db: Session = Depends(get_db),  # noqa: B008
) -> CustomerResponse:
    try:
        return get_customer(db, reference)
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "/{customer_reference}/transactions/{transaction_reference}/verify",
    response_model=CustomerVerificationResponse,
)
def verify_customer_transaction(
    customer_reference: str,
    transaction_reference: str,
    db: Session = Depends(get_db),  # noqa: B008
) -> CustomerVerificationResponse:
    try:
        verified = verify_transaction_customer(
            db,
            transaction_reference,
            customer_reference,
        )
        return CustomerVerificationResponse(
            customer_reference=customer_reference.upper(),
            transaction_reference=transaction_reference.upper(),
            verified=verified,
        )
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc