# Orchestration (Watson Orchestrate)

## Status

Not yet implemented. This document records the intended contract and
boundary.

## Role

Watson Orchestrate coordinates workflow steps and tool calls. **It does
not own business rules.** The backend decides; the orchestrator routes.

## Backend-exposed capabilities

The orchestrator will call backend capabilities such as:

```text
get_transaction
get_customer
check_dispute_eligibility
create_support_case
create_dispute
get_case_status
```

Each capability corresponds to a real backend application operation
(e.g. `GET /api/v1/transactions/{reference}` → `TransactionService` →
`TransactionRepository` → PostgreSQL). The orchestrator is never given
direct database access — only an API capability. This is a deliberate
security boundary.

## Adapter boundary

```text
application code
      │
      ▼
WorkflowPort (Protocol, backend/app/infrastructure/orchestration/workflow_port.py)
      │
      ├── LocalWorkflowAdapter        — local development, calls application services directly
      └── WatsonOrchestrateAdapter    — delegates to IBM Watson Orchestrate
```

Locally, `LocalWorkflowAdapter` can execute a sequence like
`get_transaction → validate → create_case` in-process, without any IBM
dependency. See `decisions/003-local-first-integration.md`.

## Configuration

```text
ORCHESTRATE_URL
ORCHESTRATE_API_KEY
```

Empty locally. No network calls are made until these are populated and
`WatsonOrchestrateAdapter` is implemented.
