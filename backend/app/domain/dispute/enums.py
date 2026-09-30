"""Dispute status enum."""

from enum import StrEnum


class DisputeStatus(StrEnum):
    """Allowed dispute states."""

    OPEN = "OPEN"
    UNDER_REVIEW = "UNDER_REVIEW"
    RESOLVED = "RESOLVED"
    REJECTED = "REJECTED"
