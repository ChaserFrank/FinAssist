"""AI service port.

Defines the contract the application layer uses to interpret natural
language messages, independent of which AI provider implements it. This
lets local development proceed against `MockAIService` while
`WatsonXAIService` is wired up later without touching application code.

Note: AI output must be treated as untrusted input by callers — the
backend, not the model, is authoritative.
"""

from typing import Any, Protocol


class AIService(Protocol):
    """Contract for interpreting a customer message into structured intent."""

    def analyze(self, message: str) -> dict[str, Any]:
        """Return a structured interpretation of `message`.

        The expected shape (once implemented) includes at least an
        `intent` field, with `unknown` as a valid, expected value — the
        AI must be allowed to say it doesn't understand a message rather
        than being forced into one of the known workflows.
        """
        ...
