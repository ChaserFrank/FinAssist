"""Workflow orchestration port.

Defines the contract used to coordinate a sequence of backend operations
(e.g. get_transaction -> validate -> create_case) independent of whether
the coordination happens locally or through Watson Orchestrate.

Orchestration coordinates; it does not decide. Business rules live in the
application/domain layers, never inside a workflow adapter.
"""

from typing import Any, Protocol


class WorkflowPort(Protocol):
    """Contract for executing a named workflow step against the backend."""

    def execute(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Execute `action` (e.g. "get_transaction") with `payload`.

        Returns the backend's result. Implementations must not embed
        business rules — they only route the call to the appropriate
        backend capability.
        """
        ...
