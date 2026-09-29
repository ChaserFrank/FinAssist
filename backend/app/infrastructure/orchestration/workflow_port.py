"""Workflow orchestration port.

Defines the contract used to coordinate backend operations independent of
whether coordination happens locally or through Watson Orchestrate.

Orchestration coordinates; it does not decide. Business rules live in the
application/domain layers, never inside a workflow adapter.

Actions (the backend capabilities an orchestrator may invoke; docs/orchestration.md):

    verify_customer      {customer_reference}
    get_transaction      {customer_reference, transaction_reference}
    create_dispute       {customer_reference, transaction_reference, reason}
    create_support_case  {customer_reference, category, description, [transaction_reference]}
    get_case_status      {customer_reference, case_reference}

Every action returns a plain JSON-serialisable ``dict`` (so a remote
orchestrator can return the same shape) and signals failure by raising
``app.core.exceptions.AppError`` with a documented ``ErrorCode``.
"""

from typing import Any, Protocol


class WorkflowPort(Protocol):
    """Contract for executing a named backend capability."""

    def execute(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Execute ``action`` with ``payload`` and return its result."""
        ...
