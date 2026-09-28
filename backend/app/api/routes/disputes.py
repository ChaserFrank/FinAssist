"""Dispute API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.application.dispute_service import create_dispute
from app.core.exceptions import NotFoundError
from app.schemas.dispute import DisputeCreate, DisputeResponse

router = APIRouter(prefix="/disputes", tags=["disputes"])


@router.post(
    "",
    response_model=DisputeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_dispute_case(
    payload: DisputeCreate,
    db: Session = Depends(get_db),  # noqa: B008
) -> DisputeResponse:
    try:
        return create_dispute(
            db,
            customer_reference=payload.customer_reference,
            transaction_reference=payload.transaction_reference,
            reason=payload.reason,
        )
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc