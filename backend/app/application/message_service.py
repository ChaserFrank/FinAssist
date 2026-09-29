"""Customer message handling: AI interprets -> workflow coordinates -> backend decides.

This is the "Orchestrator" box of the architecture. It owns *no business
rules*: eligibility, ownership and state checks all happen inside the
application services reached through ``WorkflowPort``. Its jobs are to
(1) obtain a validated interpretation, (2) call the right backend capability,
and (3) turn the authoritative result into a reply.

Replies are templated from backend data only. Nothing the AI said is ever
echoed to the customer, and an AI-extracted amount is only *compared* against
the real one (the database is authoritative).
"""

import logging
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import Any

from app.core.exceptions import AppError, ErrorCode
from app.infrastructure.ai.ai_port import AIInterpretation, AIService, Intent
from app.infrastructure.orchestration.workflow_port import WorkflowPort

logger = logging.getLogger(__name__)

_DISPUTE_DECLINED_CODES = frozenset(
    {ErrorCode.DISPUTE_NOT_ELIGIBLE, ErrorCode.INVALID_TRANSACTION_STATE}
)

_STATUS_SENTENCES = {
    "SUCCESS": "completed successfully",
    "FAILED": "failed",
    "PENDING": "is still pending",
    "REVERSED": "was reversed and the funds returned",
}


class MessageOutcome(StrEnum):
    """What handling a message led to (stable values the frontend can switch on)."""

    NEEDS_INFO = "needs_info"
    NOT_FOUND = "not_found"
    STATUS_REPORTED = "status_reported"
    CASE_STATUS = "case_status"
    DISPUTE_CREATED = "dispute_created"
    DISPUTE_DECLINED = "dispute_declined"


@dataclass
class MessageResult:
    outcome: MessageOutcome
    intent: Intent
    reply: str
    transaction: dict[str, Any] | None = None
    case_reference: str | None = None
    dispute_reference: str | None = None
    amount_mismatch: bool = False
    extras: dict[str, Any] = field(default_factory=dict)


def _money(currency: str, amount: str) -> str:
    try:
        return f"{currency} {Decimal(amount):,.2f}"
    except InvalidOperation:  # defensive: amount always comes from our own DB
        return f"{currency} {amount}"


class SupportMessageService:
    """Handles one free-text customer message end to end."""

    def __init__(self, ai: AIService, workflow: WorkflowPort) -> None:
        self._ai = ai
        self._workflow = workflow

    def handle(self, customer_reference: str, message: str) -> MessageResult:
        # Fail fast, with a real 404, if the claimed customer does not exist.
        self._workflow.execute("verify_customer", {"customer_reference": customer_reference})

        interpretation = self._interpret(message)
        intent = interpretation.intent

        if intent is Intent.UNKNOWN:
            return MessageResult(
                MessageOutcome.NEEDS_INFO,
                intent,
                "I'm not sure I understood that. Could you tell me what happened and "
                "include your transaction reference (for example TXN-84721)?",
            )

        if intent is Intent.SUPPORT_CASE_STATUS:
            return self._case_status(customer_reference, interpretation)

        if interpretation.transaction_reference is None:
            return MessageResult(
                MessageOutcome.NEEDS_INFO,
                intent,
                "I can help with that. Please include your transaction reference "
                "(for example TXN-84721) - you'll find it in your payment confirmation.",
            )

        try:
            txn = self._workflow.execute(
                "get_transaction",
                {
                    "customer_reference": customer_reference,
                    "transaction_reference": interpretation.transaction_reference,
                },
            )
        except AppError as exc:
            if exc.code is ErrorCode.TRANSACTION_NOT_FOUND:
                return MessageResult(
                    MessageOutcome.NOT_FOUND,
                    intent,
                    f"I couldn't find transaction {interpretation.transaction_reference} "
                    "on your account. Please double-check the reference.",
                )
            raise

        mismatch = self._amount_mismatch(interpretation, txn)

        if intent is Intent.PAYMENT_DISPUTE:
            return self._dispute(customer_reference, message, intent, txn, mismatch)

        return self._status(intent, txn, mismatch)

    # -- steps -----------------------------------------------------------

    def _interpret(self, message: str) -> AIInterpretation:
        try:
            return self._ai.analyze(message)
        except AppError:
            raise
        except Exception as exc:
            logger.exception("AI interpretation failed")
            raise AppError(
                ErrorCode.AI_UNAVAILABLE,
                "The assistant is temporarily unavailable. Please try again shortly.",
            ) from exc

    @staticmethod
    def _amount_mismatch(interpretation: AIInterpretation, txn: dict[str, Any]) -> bool:
        """True if the customer's stated amount differs from the real one."""
        if interpretation.amount is None:
            return False
        return interpretation.amount != Decimal(txn["amount"])

    def _status(self, intent: Intent, txn: dict[str, Any], mismatch: bool) -> MessageResult:
        status = txn["status"]
        reply = (
            f"Your {_money(txn['currency'], txn['amount'])} payment "
            f"({txn['transaction_reference']}) {_STATUS_SENTENCES.get(status, status.lower())}."
        )
        if intent is Intent.PAYMENT_FAILED and status == "FAILED":
            reply += (
                " If money was taken from your account, tell me and I'll open a "
                "dispute for you."
            )
        if mismatch:
            reply += " Note: the amount you mentioned differs from our records."
        return MessageResult(
            MessageOutcome.STATUS_REPORTED, intent, reply, transaction=txn,
            amount_mismatch=mismatch,
        )

    def _dispute(
        self,
        customer_reference: str,
        message: str,
        intent: Intent,
        txn: dict[str, Any],
        mismatch: bool,
    ) -> MessageResult:
        try:
            result = self._workflow.execute(
                "create_dispute",
                {
                    "customer_reference": customer_reference,
                    "transaction_reference": txn["transaction_reference"],
                    "reason": message,
                },
            )
        except AppError as exc:
            if exc.code in _DISPUTE_DECLINED_CODES:
                return MessageResult(
                    MessageOutcome.DISPUTE_DECLINED, intent, exc.message,
                    transaction=txn, amount_mismatch=mismatch,
                )
            raise

        status = txn["status"]
        reply = (
            f"Your {_money(txn['currency'], txn['amount'])} payment "
            f"({txn['transaction_reference']}) {_STATUS_SENTENCES.get(status, status.lower())}. "
            f"I've opened support case {result['case_reference']} and dispute "
            f"{result['dispute_reference']} so our team can investigate."
        )
        if mismatch:
            reply += " Note: the amount you mentioned differs from our records."
        return MessageResult(
            MessageOutcome.DISPUTE_CREATED, intent, reply, transaction=txn,
            case_reference=result["case_reference"],
            dispute_reference=result["dispute_reference"],
            amount_mismatch=mismatch,
        )

    def _case_status(
        self, customer_reference: str, interpretation: AIInterpretation
    ) -> MessageResult:
        if interpretation.case_reference is None:
            return MessageResult(
                MessageOutcome.NEEDS_INFO,
                interpretation.intent,
                "Which support case would you like an update on? "
                "Please include the case reference (for example CASE-1001).",
            )
        try:
            case = self._workflow.execute(
                "get_case_status",
                {
                    "customer_reference": customer_reference,
                    "case_reference": interpretation.case_reference,
                },
            )
        except AppError as exc:
            if exc.code is ErrorCode.SUPPORT_CASE_NOT_FOUND:
                return MessageResult(
                    MessageOutcome.NOT_FOUND,
                    interpretation.intent,
                    f"I couldn't find case {interpretation.case_reference} on your account. "
                    "Please double-check the reference.",
                )
            raise
        return MessageResult(
            MessageOutcome.CASE_STATUS,
            interpretation.intent,
            f"Case {case['case_reference']} is currently "
            f"{case['status'].replace('_', ' ').lower()}.",
            case_reference=case["case_reference"],
        )
