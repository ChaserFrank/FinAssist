"""Support case API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.application.support_service import (
    create_support_case,
    get_support_case,
    investigate_support_case,
)
from app.core.exceptions import NotFoundError
from app.schemas.support import SupportCaseCreate, SupportCaseResponse

router = APIRouter(prefix="/support", tags=["support"])


@router.post(
    "/cases",
    response_model=SupportCaseResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_case(
    payload: SupportCaseCreate,
    db: Session = Depends(get_db),
) -> SupportCaseResponse:
    if not payload.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Support message cannot be empty.",
        )

    try:
        return create_support_case(
            db,
            payload.transaction_reference,
            payload.message.strip(),
        )
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "/cases/{reference}",
    response_model=SupportCaseResponse,
)
def lookup_case(
    reference: str,
    db: Session = Depends(get_db),
) -> SupportCaseResponse:
    try:
        return get_support_case(db, reference)
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post(
    "/cases/{reference}/investigate",
    response_model=SupportCaseResponse,
)
def investigate_case(
    reference: str,
    db: Session = Depends(get_db),
) -> SupportCaseResponse:
    try:
        return investigate_support_case(db, reference)
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
