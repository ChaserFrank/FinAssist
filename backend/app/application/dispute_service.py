"""Dispute use cases (application layer).

This is the most important business-logic module in FinAssist.

create_dispute implements the full eligibility pipeline:
  1. Look up transaction           → TRANSACTION_NOT_FOUND
  2. Look up customer              → CUSTOMER_NOT_FOUND
  3. Verify customer owns txn      → CUSTOMER_TRANSACTION_MISMATCH
  4. Check transaction state       → INVALID_TRANSACTION_STATE
     - PENDING:  in-flight, cannot dispute until settlement
     - REVERSED: funds returned, nothing to dispute
     - SUCCESS / FAILED: eligible
  5. Check for active open dispute → DISPUTE_NOT_ELIGIBLE
     - Status OPEN or UNDER_REVIEW on same transaction → reject
     - Status RESOLVED or REJECTED on same transaction → reject (cannot redispute)
  6. Create SupportCase            → atomically in same DB transaction
  7. Create Dispute                → same DB transaction

The database-level partial unique index on disputes(transaction_id) is a
second, independent safety net against concurrent duplicate disputes.

Transaction boundary (ADR-006): this service owns commit/rollback. Repositories
only ``add``/``flush``; routes never touch the session. A support case and its
dispute are therefore committed together or not at all.

The eligibility matrix (which transaction states may be disputed) is
documented in ADR-005.

Per ADR-002: AI output is untrusted input.  This service receives already-
validated, backend-authoritative data — it never accepts AI-extracted values
without the caller having independently retrieved the real entities first.
"""

import logging

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import AppError, ErrorCode
from app.domain.dispute.enums import DisputeStatus
from app.domain.dispute.models import Dispute
from app.domain.transaction.enums import TransactionStatus
from app.infrastructure.database.reference_generator import (
    next_dispute_reference,
    next_support_case_reference,
)
from app.infrastructure.repositories.customer_repo import CustomerRepository
from app.infrastructure.repositories.dispute_repo import DisputeRepository
from app.infrastructure.repositories.support_case_repo import SupportCaseRepository
from app.infrastructure.repositories.transaction_repo import TransactionRepository

logger = logging.getLogger(__name__)

# Fragments that identify our "one active dispute per transaction" unique index
# in a driver's error text: Postgres names the index; SQLite names the column.
_ACTIVE_DISPUTE_INDEX_MARKERS = (
    "uq_disputes_open_per_transaction",
    "disputes.transaction_id",
)


def _is_active_dispute_violation(exc: IntegrityError) -> bool:
    """True only if ``exc`` is the duplicate-active-dispute unique violation.

    Any *other* integrity error (FK violation, reference collision, CHECK
    failure) is a genuine bug or data problem and must not be reported to the
    customer as "not eligible".
    """
    text = str(exc.orig)
    return any(marker in text for marker in _ACTIVE_DISPUTE_INDEX_MARKERS)


# Statuses that mean a transaction has settled and is therefore eligible for
# dispute (see ADR-005).
_DISPUTABLE_STATUSES = frozenset({TransactionStatus.SUCCESS, TransactionStatus.FAILED})

# Statuses of a prior dispute that permanently close the dispute window.
_TERMINAL_DISPUTE_STATUSES = frozenset({DisputeStatus.RESOLVED, DisputeStatus.REJECTED})


class DisputeService:
    """Application-layer use cases for the Dispute domain."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._customer_repo = CustomerRepository(session)
        self._txn_repo = TransactionRepository(session)
        self._case_repo = SupportCaseRepository(session)
        self._dispute_repo = DisputeRepository(session)

    def create_dispute(
        self,
        customer_reference: str,
        transaction_reference: str,
        reason: str,
    ) -> Dispute:
        """Open a formal dispute against a transaction.

        Atomically creates both a SupportCase (the customer service record)
        and a Dispute (the financial challenge) in a single database
        transaction, committed here.  If any step fails, both are rolled back.

        Eligibility matrix (rationale: docs/decisions/005-dispute-eligibility-matrix.md):

        - TransactionStatus.SUCCESS  → eligible
        - TransactionStatus.FAILED   → eligible (core scenario: charged
                                       despite payment failure)
        - TransactionStatus.PENDING  → ineligible (INVALID_TRANSACTION_STATE)
        - TransactionStatus.REVERSED → ineligible (INVALID_TRANSACTION_STATE)

        Args:
            customer_reference:    ``CUS-xxxxx`` of the disputing customer.
            transaction_reference: ``TXN-xxxxx`` of the disputed transaction.
            reason:                Free-text reason supplied by the customer.

        Returns:
            The newly created ``Dispute``.

        Raises:
            AppError(TRANSACTION_NOT_FOUND):         transaction missing.
            AppError(CUSTOMER_NOT_FOUND):            customer missing.
            AppError(CUSTOMER_TRANSACTION_MISMATCH): txn not owned by customer.
            AppError(INVALID_TRANSACTION_STATE):     txn in PENDING or REVERSED.
            AppError(DISPUTE_NOT_ELIGIBLE):          active/prior dispute exists.
        """
        try:
            dispute = self._create_dispute_inner(
                customer_reference, transaction_reference, reason
            )
            self._session.commit()
            return dispute
        except IntegrityError as exc:
            self._session.rollback()
            if _is_active_dispute_violation(exc):
                # The partial unique index caught a concurrent duplicate that
                # slipped past the application-level check.
                raise AppError(
                    ErrorCode.DISPUTE_NOT_ELIGIBLE,
                    f"An active dispute already exists for transaction "
                    f"'{transaction_reference}'. Cannot open a second dispute "
                    "while one is in progress.",
                ) from exc
            logger.exception("Unexpected integrity error creating dispute")
            raise
        except Exception:
            # Business-rule rejections (AppError) and unexpected failures alike:
            # leave nothing half-written and the session reusable.
            self._session.rollback()
            raise

    def _create_dispute_inner(
        self,
        customer_reference: str,
        transaction_reference: str,
        reason: str,
    ) -> Dispute:
        # Step 1: Resolve transaction
        txn = self._txn_repo.get_by_reference(transaction_reference)
        if txn is None:
            raise AppError(
                ErrorCode.TRANSACTION_NOT_FOUND,
                f"No transaction found with reference '{transaction_reference}'.",
            )

        # Step 2: Resolve customer
        customer = self._customer_repo.get_by_reference(customer_reference)
        if customer is None:
            raise AppError(
                ErrorCode.CUSTOMER_NOT_FOUND,
                f"No customer found with reference '{customer_reference}'.",
            )

        # Step 3: Ownership check — AI may have hallucinated the pairing
        if txn.customer_id != customer.id:
            raise AppError(
                ErrorCode.CUSTOMER_TRANSACTION_MISMATCH,
                f"Transaction '{transaction_reference}' does not belong to "
                f"customer '{customer_reference}'.",
            )

        # Step 4: Transaction state eligibility
        if txn.status not in _DISPUTABLE_STATUSES:
            if txn.status == TransactionStatus.PENDING:
                detail = (
                    f"Transaction '{transaction_reference}' is still pending. "
                    "Disputes can only be raised once a transaction has settled."
                )
            else:  # REVERSED
                detail = (
                    f"Transaction '{transaction_reference}' has already been reversed. "
                    "Funds have been returned — there is nothing to dispute."
                )
            raise AppError(ErrorCode.INVALID_TRANSACTION_STATE, detail)

        # Step 5: Duplicate dispute check (application layer)
        # The partial unique index on disputes is the database-layer fallback.
        existing = self._dispute_repo.find_active_by_transaction_id(txn.id)
        if existing is not None:
            raise AppError(
                ErrorCode.DISPUTE_NOT_ELIGIBLE,
                f"An active dispute ('{existing.reference}') already exists for "
                f"transaction '{transaction_reference}'. "
                "Cannot open a second dispute while one is in progress.",
            )

        # Also reject if the transaction was previously disputed and that dispute
        # reached a terminal state (RESOLVED or REJECTED) — cannot redispute.
        prior_terminal = self._session.scalars(
            select(Dispute).where(
                Dispute.transaction_id == txn.id,
                Dispute.status.in_(_TERMINAL_DISPUTE_STATUSES),
            )
        ).first()
        if prior_terminal is not None:
            raise AppError(
                ErrorCode.DISPUTE_NOT_ELIGIBLE,
                f"Transaction '{transaction_reference}' was previously disputed "
                f"('{prior_terminal.reference}', status: {prior_terminal.status}). "
                "Transactions cannot be redisputed once a dispute has been resolved or rejected.",
            )

        # Steps 6 & 7: Atomic creation within the caller's transaction
        case_ref = next_support_case_reference(self._session)
        case = self._case_repo.create(
            reference=case_ref,
            customer_id=customer.id,
            transaction_id=txn.id,
            category="payment_dispute",
            description=reason,
        )

        dispute_ref = next_dispute_reference(self._session)
        dispute = self._dispute_repo.create(
            reference=dispute_ref,
            support_case_id=case.id,
            transaction_id=txn.id,
            reason=reason,
        )

        return dispute

    def get_dispute(self, reference: str) -> Dispute:
        """Return the dispute identified by ``reference``.

        Raises:
            AppError(DISPUTE_NOT_FOUND): if not found.
        """
        dispute = self._dispute_repo.get_by_reference(reference)
        if dispute is None:
            raise AppError(
                ErrorCode.DISPUTE_NOT_FOUND,
                f"No dispute found with reference '{reference}'.",
            )
        return dispute
