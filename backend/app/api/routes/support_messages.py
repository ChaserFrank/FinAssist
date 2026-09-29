"""Support message route -- the entry point the frontend chat form calls.

HTTP layer only. Interpretation, orchestration and business rules all live
behind ``SupportMessageService``.

Business outcomes ("that transaction isn't eligible for a dispute") are
returned as HTTP 200 with an ``outcome`` field: the message was understood and
handled. Genuine client/infrastructure problems use the standard error
envelope instead (404 CUSTOMER_NOT_FOUND, 422 VALIDATION_ERROR,
503 AI_UNAVAILABLE, ...).
"""

from fastapi import APIRouter, Depends

from app.api.dependencies import get_message_service
from app.application.message_service import SupportMessageService
from app.schemas.support import (
    SupportMessageRequest,
    SupportMessageResponse,
    TransactionSummary,
)

router = APIRouter(prefix="/support/messages", tags=["support_messages"])


@router.post("", response_model=SupportMessageResponse)
def post_support_message(
    body: SupportMessageRequest,
    service: SupportMessageService = Depends(get_message_service),
) -> SupportMessageResponse:
    """Interpret a customer's free-text message and act on it."""
    result = service.handle(body.customer_reference.strip(), body.message.strip())
    txn = result.transaction
    return SupportMessageResponse(
        outcome=result.outcome,
        intent=result.intent,
        reply=result.reply,
        transaction=(
            TransactionSummary(
                reference=txn["transaction_reference"],
                status=txn["status"],
                amount=txn["amount"],
                currency=txn["currency"],
            )
            if txn
            else None
        ),
        case_reference=result.case_reference,
        dispute_reference=result.dispute_reference,
        amount_mismatch=result.amount_mismatch,
    )
