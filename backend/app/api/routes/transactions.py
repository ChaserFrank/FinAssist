"""Transaction API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.application.transaction_service import get_transaction
from app.core.exceptions import NotFoundError
from app.schemas.transaction import TransactionResponse

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get(
    "/{reference}",
    response_model=TransactionResponse,
)
def lookup_transaction(
    reference: str,
    db: Session = Depends(get_db),  # noqa: B008
) -> TransactionResponse:
    try:
        return get_transaction(db, reference)
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc