"""Transaction status enum.

Defined ahead of the transaction model because workflow and business-rule
logic depend on a controlled, predictable state model rather than
arbitrary strings.
"""

from enum import StrEnum


class TransactionStatus(StrEnum):
    """Allowed transaction states."""

    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REVERSED = "REVERSED"
