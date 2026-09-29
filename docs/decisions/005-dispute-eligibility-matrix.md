# ADR-005: Dispute Eligibility Matrix

## Status

Accepted

## Context

The original architecture proposal named one disputable transaction state
("FAILED — charged despite payment failure") as the core scenario, but did
not specify the other three. Implementing `DisputeService` required a
complete, unambiguous rule: every `TransactionStatus` needed a decision.

## Decision

| Status | Disputable? | Reasoning |
|---|---|---|
| `SUCCESS` | Yes | The payment completed, but the customer may still dispute the charge itself (wrong amount, unauthorized, goods/services not received). This is the ordinary "I want my money back" case. |
| `FAILED` | Yes | The core FinAssist scenario: money left the account but the payment did not go through. |
| `PENDING` | No (`INVALID_TRANSACTION_STATE`) | The outcome isn't known yet. Disputing before settlement is premature — the transaction may still succeed, fail, or reverse on its own. |
| `REVERSED` | No (`INVALID_TRANSACTION_STATE`) | Funds have already been returned. There is nothing left to dispute. |

Additionally, once a transaction has had a dispute reach a terminal state
(`RESOLVED` or `REJECTED`), it cannot be redisputed — see ADR-004 for the
duplicate/redispute rules this pairs with.

## Consequences

- `DisputeService.create_dispute` has one authoritative eligibility check
  (`_DISPUTABLE_STATUSES = {SUCCESS, FAILED}`), unit-tested for all four
  statuses (`tests/unit/test_dispute_eligibility.py`).
- The error message names the specific reason (still pending vs. already
  reversed) rather than a generic "not eligible", which is friendlier for the
  customer and for whoever is debugging a support ticket.
- If a future requirement needs `SUCCESS` transactions to go through a
  different flow than `FAILED` ones (e.g. a merchant-dispute process vs. a
  payment-failure refund), the two statuses can be split into different
  categories without changing this ADR's structure.
