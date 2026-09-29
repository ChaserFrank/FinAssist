"""Local, in-process implementation of ``WorkflowPort`` (no IBM dependency).

Each action is a thin dispatch to the application service that owns the
corresponding business rule; this adapter contains *no* rules of its own
(``AI interprets. Orchestration coordinates. Backend authorizes.``).
Results are plain dicts so a future ``WatsonOrchestrateAdapter`` returns the
identical shape. See docs/decisions/003-local-first-integration.md.
"""

from collections.abc import Callable
from typing import Any

from sqlalchemy.orm import Session

from app.application.customer_service import CustomerService
from app.application.dispute_service import DisputeService
from app.application.support_service import SupportService
from app.application.transaction_service import TransactionService
from app.core.exceptions import AppError, ErrorCode


class LocalWorkflowAdapter:
    """``WorkflowPort`` that calls application services directly."""

    def __init__(self, session: Session) -> None:
        self._customers = CustomerService(session)
        self._transactions = TransactionService(session)
        self._disputes = DisputeService(session)
        self._support = SupportService(session)
        self._actions: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
            "verify_customer": self._verify_customer,
            "get_transaction": self._get_transaction,
            "create_dispute": self._create_dispute,
            "create_support_case": self._create_support_case,
            "get_case_status": self._get_case_status,
        }

    def execute(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        handler = self._actions.get(action)
        if handler is None:
            raise AppError(ErrorCode.WORKFLOW_FAILED, f"Unknown workflow action '{action}'.")
        try:
            return handler(payload)
        except KeyError as exc:
            raise AppError(
                ErrorCode.WORKFLOW_FAILED,
                f"Workflow action '{action}' is missing required input {exc}.",
            ) from exc

    # -- actions ---------------------------------------------------------

    def _verify_customer(self, payload: dict[str, Any]) -> dict[str, Any]:
        customer = self._customers.get_customer(payload["customer_reference"])
        return {"customer_reference": customer.reference}

    def _get_transaction(self, payload: dict[str, Any]) -> dict[str, Any]:
        txn = self._transactions.get_transaction_for_customer(
            payload["customer_reference"], payload["transaction_reference"]
        )
        return {
            "transaction_reference": txn.reference,
            "status": txn.status.value,
            "amount": str(txn.amount),
            "currency": txn.currency,
        }

    def _create_dispute(self, payload: dict[str, Any]) -> dict[str, Any]:
        dispute = self._disputes.create_dispute(
            customer_reference=payload["customer_reference"],
            transaction_reference=payload["transaction_reference"],
            reason=payload["reason"],
        )
        return {
            "dispute_reference": dispute.reference,
            "case_reference": dispute.support_case.reference,
            "status": dispute.status.value,
            "transaction_reference": dispute.transaction.reference,
        }

    def _create_support_case(self, payload: dict[str, Any]) -> dict[str, Any]:
        case = self._support.create_case(
            customer_reference=payload["customer_reference"],
            category=payload["category"],
            description=payload["description"],
            transaction_reference=payload.get("transaction_reference"),
        )
        return {"case_reference": case.reference, "status": case.status.value}

    def _get_case_status(self, payload: dict[str, Any]) -> dict[str, Any]:
        case = self._support.get_case_for_customer(
            payload["customer_reference"], payload["case_reference"]
        )
        return {
            "case_reference": case.reference,
            "status": case.status.value,
            "category": case.category,
        }
