"""Deterministic, keyword-based stand-in for watsonx.ai (local development).

It does the same *job* as the real model -- text in, validated structured
intent out -- without any intelligence, network call or credentials, so the
whole system can be built and tested offline. Swapping in ``WatsonXAIService``
requires no change to application code.
"""

import re
from decimal import Decimal, InvalidOperation

from app.infrastructure.ai.ai_port import AIInterpretation, Intent, parse_ai_output

_TXN = re.compile(r"\bTXN-\d{4,9}\b", re.IGNORECASE)
_CASE = re.compile(r"\bCASE-\d{4,9}\b", re.IGNORECASE)
_NUM = r"([0-9][0-9,]*(?:\.[0-9]{1,2})?)"
_CUR = r"(?:ksh|kshs|kes)\.?"
_AMOUNT_PREFIX = re.compile(rf"\b{_CUR}\s*{_NUM}", re.IGNORECASE)
_AMOUNT_SUFFIX = re.compile(rf"\b{_NUM}\s*(?:{_CUR}|shillings)\b", re.IGNORECASE)

_DEDUCTED = (
    "deducted", "charged", "debited", "took my money", "money was taken",
    "refund", "dispute",
)
_FAILED = (
    "fail", "didn't go through", "did not go through", "didnt go through",
    "unsuccessful", "declined", "hasn't gone through", "has not gone through",
)
_STATUS = ("status", "check", "what happened", "where is", "pending", "reversed", "reverse")


def _extract_amount(message: str) -> Decimal | None:
    match = _AMOUNT_PREFIX.search(message) or _AMOUNT_SUFFIX.search(message)
    if match is None:
        return None
    try:
        return Decimal(match.group(1).replace(",", ""))
    except InvalidOperation:
        return None


class MockAIService:
    """Keyword-based ``AIService`` implementation."""

    def analyze(self, message: str) -> AIInterpretation:
        text = message.lower()

        txn = _TXN.search(message)
        case = _CASE.search(message)
        amount = _extract_amount(message)

        deducted = any(word in text for word in _DEDUCTED)
        failed = any(word in text for word in _FAILED)
        status_words = any(word in text for word in _STATUS)

        if case is not None or ("case" in text and status_words):
            intent = Intent.SUPPORT_CASE_STATUS
        elif deducted:
            intent = Intent.PAYMENT_DISPUTE
        elif failed:
            intent = Intent.PAYMENT_FAILED
        elif status_words:
            intent = Intent.TRANSACTION_STATUS
        else:
            intent = Intent.UNKNOWN

        needs_txn = intent in (
            Intent.PAYMENT_DISPUTE, Intent.PAYMENT_FAILED, Intent.TRANSACTION_STATUS
        )
        if intent is Intent.UNKNOWN:
            confidence = 0.0
        elif (needs_txn and txn) or (intent is Intent.SUPPORT_CASE_STATUS and case):
            confidence = 0.9
        else:
            confidence = 0.6

        # Go through the same validation gate a real provider's output must.
        return parse_ai_output(
            {
                "intent": intent,
                "transaction_reference": txn.group(0).upper() if txn else None,
                "case_reference": case.group(0).upper() if case else None,
                "amount": amount,
                "currency": "KES" if amount is not None else None,
                "confidence": confidence,
                "requires_transaction_lookup": needs_txn,
            }
        )
