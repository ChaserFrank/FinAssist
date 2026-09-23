# API

## Status

Only `GET /health` currently exists. Everything below documents the
**agreed contract** for endpoints that will be implemented in later
milestones, so frontend work can proceed against a stable interface.

## Versioning

Business endpoints will live under `/api/v1/`.

## Current endpoint

### `GET /health`

```json
{ "status": "ok" }
```

No auth, no database dependency. Used for liveness checks.

## Planned endpoints (not yet implemented)

```text
GET  /api/v1/transactions/{reference}
GET  /api/v1/customers/{id}
POST /api/v1/support/messages
POST /api/v1/support/cases
GET  /api/v1/support/cases/{reference}
POST /api/v1/disputes
GET  /api/v1/disputes/{reference}
```

### Example: create dispute

**Request**

```json
POST /api/v1/disputes
{
  "customer_reference": "CUS-10021",
  "transaction_reference": "TXN-84721",
  "reason": "Payment failed but account was charged"
}
```

**Response**

```json
{
  "reference": "CASE-1042",
  "status": "OPEN",
  "transaction_reference": "TXN-84721"
}
```

## Error envelope

All error responses will use a consistent shape:

```json
{
  "error": {
    "code": "TRANSACTION_NOT_FOUND",
    "message": "The requested transaction could not be found."
  }
}
```

See `backend/app/core/exceptions.py` for the full `ErrorCode` vocabulary
(`TRANSACTION_NOT_FOUND`, `CUSTOMER_NOT_FOUND`,
`CUSTOMER_TRANSACTION_MISMATCH`, `INVALID_TRANSACTION_STATE`,
`DISPUTE_NOT_ELIGIBLE`, `SUPPORT_CASE_NOT_FOUND`, `VALIDATION_ERROR`,
`AI_UNAVAILABLE`, `WORKFLOW_FAILED`, `INTERNAL_ERROR`). Exception handling
middleware that raises these consistently has not been wired up yet.

## Contract-first collaboration

Per team convention, request/response contracts for a new endpoint should
be agreed here (or in the relevant GitHub issue) **before** implementation
starts, so backend and frontend work can proceed independently.
