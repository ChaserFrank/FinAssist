"""Support case status enum."""

from enum import StrEnum


class SupportCaseStatus(StrEnum):
    """Allowed support case states."""

    OPEN = "OPEN"
    IN_REVIEW = "IN_REVIEW"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
