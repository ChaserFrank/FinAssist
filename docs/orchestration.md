# Orchestration

## Status

**Implemented (local).** `LocalWorkflowAdapter`
(`backend/app/infrastructure/orchestration/local_workflow_adapter.py`) plays
the role Watson Orchestrate will eventually play: it coordinates calls to
backend capabilities, in-process, with **no business rules of its own**.
`WatsonOrchestrateAdapter` remains a documented placeholder until IBM
TechZone access is available (ADR-003).

## Backend capabilities

`WorkflowPort.execute(action, payload)` is the only surface an orchestrator
(local or IBM) uses. Every action returns a plain, JSON-serialisable `dict`
and raises `app.core.exceptions.AppError` with a documented `ErrorCode` on
failure — the same contract a remote orchestrator would see over HTTP.

| Action | Payload | Backed by |
|---|---|---|
| `verify_customer` | `{customer_reference}` | `CustomerService.get_customer` |
| `get_transaction` | `{customer_reference, transaction_reference}` | `TransactionService.get_transaction_for_customer` |
| `create_dispute` | `{customer_reference, transaction_reference, reason}` | `DisputeService.create_dispute` |
| `create_support_case` | `{customer_reference, category, description, [transaction_reference]}` | `SupportService.create_case` |
| `get_case_status` | `{customer_reference, case_reference}` | `SupportService.get_case_for_customer` |

The orchestrator is never given a database connection — only these five
named capabilities, each of which independently re-validates ownership. This
is the security boundary from `docs/architecture.md`: "the orchestrator never
gets `postgresql://...`; it gets an API capability."

## Who calls it today

`SupportMessageService` (`backend/app/application/message_service.py`) is the
orchestrator's only current caller: `POST /api/v1/support/messages` ->
`MockAIService.analyze()` -> one or two `WorkflowPort.execute()` calls ->
a reply built from the result. `SupportMessageService` contains no business
rules either — eligibility, ownership, and state checks all live inside the
services `LocalWorkflowAdapter` dispatches to.

## Configuration

```text
ORCHESTRATE_URL
ORCHESTRATE_API_KEY
```

Empty locally (no default). No network call is made until
`WatsonOrchestrateAdapter` is implemented and these are populated.
