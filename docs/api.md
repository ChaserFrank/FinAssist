# API

## Status

Implemented: `GET /health` plus the full `/api/v1` surface below, backed by
PostgreSQL, with automated tests at every layer (see `backend/tests/`).
Not yet implemented: authentication (see `docs/security.md`) and the real
watsonx.ai / Watson Orchestrate integrations (`docs/ai.md`,
`docs/orchestration.md` — local mock/adapter implementations stand in for
both today).

## Versioning

All business endpoints live under `/api/v1/`.

## Endpoints

```text
GET  /health
GET  /api/v1/transactions/{reference}
GET  /api/v1/customers/{reference}
POST /api/v1/support/cases
GET  /api/v1/support/cases/{reference}
POST /api/v1/support/messages
POST /api/v1/disputes
GET  /api/v1/disputes/{reference}
```

Every entity is addressed by its human-friendly `reference`
(`CUS-10021`, `TXN-84721`, `CASE-1001`, `DSP-1001`) — see
`docs/database.md`. Internal UUIDs are never exposed.

### `GET /health`

```json
{ "status": "ok" }
```

No auth, no database dependency. Liveness check only.

### `GET /api/v1/transactions/{reference}`

```json
{
  "reference": "TXN-84722",
  "customer_reference": "CUS-10021",
  "amount": "800.00",
  "currency": "KES",
  "status": "FAILED",
  "payment_method": "M-Pesa",
  "created_at": "2026-09-28T06:49:22.862421Z"
}
```

### `GET /api/v1/customers/{reference}`

```json
{
  "reference": "CUS-10021",
  "name": "Bob Omondi",
  "phone": "+254*******21",
  "email": "b**@example.com",
  "created_at": "2026-09-28T06:49:22.862421Z"
}
```

`phone` and `email` are **masked**. There is no authentication yet (see
`docs/security.md`), so the API must not hand full contact details to an
arbitrary caller who merely knows a customer's reference.

### `POST /api/v1/support/cases`

**Request**

```json
{
  "customer_reference": "CUS-10021",
  "transaction_reference": "TXN-84721",
  "category": "payment_dispute",
  "description": "Payment failed but I was charged."
}
```

`transaction_reference` is optional. **Response** (HTTP 201): same shape as
`GET /api/v1/support/cases/{reference}` below.

### `GET /api/v1/support/cases/{reference}`

```json
{
  "reference": "CASE-1001",
  "customer_reference": "CUS-10021",
  "transaction_reference": "TXN-84722",
  "category": "payment_dispute",
  "description": "Charged but payment failed",
  "status": "OPEN",
  "created_at": "2026-09-28T06:49:34.809436Z"
}
```

### `POST /api/v1/support/messages`

The entry point the frontend's chat form calls. Implements
"AI interprets -> orchestration coordinates -> backend authorizes" end to
end (`docs/architecture.md`).

**Request**

```json
{
  "customer_reference": "CUS-10021",
  "message": "I was charged KSh 800 for TXN-84722 but the payment failed"
}
```

`customer_reference` is a **claimed** identity — see `docs/security.md` on
why this is not the same as authentication.

**Response** (always HTTP 200 once the customer reference itself is valid —
see "Outcomes vs. errors" below)

```json
{
  "outcome": "dispute_created",
  "intent": "payment_dispute",
  "reply": "Your KES 800.00 payment (TXN-84722) failed. I've opened support case CASE-1001 and dispute DSP-1001 so our team can investigate.",
  "transaction": { "reference": "TXN-84722", "status": "FAILED", "amount": "800.00", "currency": "KES" },
  "case_reference": "CASE-1001",
  "dispute_reference": "DSP-1001",
  "amount_mismatch": false
}
```

`outcome` is a stable enum the frontend can switch on without parsing
`reply`:

| Outcome | Meaning |
|---|---|
| `needs_info` | Understood the general topic but missing a reference (transaction or case) to act on |
| `not_found` | A transaction/case reference was given but doesn't exist **on this customer's account** (see below) |
| `status_reported` | Returned the transaction's current, backend-verified status |
| `case_status` | Returned a support case's current status |
| `dispute_created` | A support case and dispute were opened |
| `dispute_declined` | Understood the request but the transaction is not eligible (see ADR-005) |

`amount_mismatch: true` means the customer's stated amount didn't match our
records — the reply still uses **our** number, never theirs (untrusted-input
principle, `docs/ai.md`).

**Cross-customer references are reported as `not_found`, not as an
ownership error.** If `CUS-10001` asks about a transaction that belongs to
`CUS-10021`, the response is identical to asking about a transaction that
doesn't exist at all. This is deliberate: it prevents the endpoint being used
to enumerate which references exist for other customers.

### `POST /api/v1/disputes`

**Request**

```json
{
  "customer_reference": "CUS-10021",
  "transaction_reference": "TXN-84721",
  "reason": "Payment failed but account was charged"
}
```

**Response** (HTTP 201)

```json
{
  "reference": "DSP-1042",
  "support_case_reference": "CASE-1042",
  "transaction_reference": "TXN-84721",
  "status": "OPEN",
  "reason": "Payment failed but account was charged",
  "created_at": "2026-09-28T06:49:34.809436Z"
}
```

Creates a `SupportCase` and a `Dispute` atomically (ADR-006). See ADR-005 for
which transaction states are eligible, and ADR-004 for how duplicate/repeat
disputes on the same transaction are prevented.

### `GET /api/v1/disputes/{reference}`

Same shape as the `POST` response above.

## Outcomes vs. errors

Two different failure shapes exist on purpose:

- **Business outcomes** the system understood but couldn't fulfil (transaction
  not eligible for dispute, message needs more information) are HTTP 200 from
  `POST /api/v1/support/messages`, distinguished by `outcome`. The request was
  valid; the answer is "no, and here's why."
- **Genuine errors** (unknown customer, malformed request, a real backend
  failure) use the standard error envelope and an HTTP 4xx/5xx status, from
  every endpoint including `/support/messages`.

## Error envelope

```json
{
  "error": {
    "code": "TRANSACTION_NOT_FOUND",
    "message": "The requested transaction could not be found."
  }
}
```

| Code | HTTP | Meaning |
|---|---|---|
| `TRANSACTION_NOT_FOUND` | 404 | No transaction with that reference |
| `CUSTOMER_NOT_FOUND` | 404 | No customer with that reference |
| `CUSTOMER_TRANSACTION_MISMATCH` | 400 | Transaction exists but belongs to a different customer (direct dispute/case creation only — see the message-endpoint note above for why the message flow reports `not_found` instead) |
| `INVALID_TRANSACTION_STATE` | 422 | Transaction is `PENDING` or `REVERSED` (ADR-005) |
| `DISPUTE_NOT_ELIGIBLE` | 409 | Active or terminally-resolved prior dispute exists (ADR-004) |
| `SUPPORT_CASE_NOT_FOUND` | 404 | No support case with that reference |
| `DISPUTE_NOT_FOUND` | 404 | No dispute with that reference |
| `VALIDATION_ERROR` | 422 | Request body failed validation (includes standard FastAPI/Pydantic errors, mapped onto this same envelope) |
| `AI_UNAVAILABLE` | 503 | The interpretation step failed unexpectedly |
| `WORKFLOW_FAILED` | 502 | An orchestration action was unknown or misconfigured |
| `INTERNAL_ERROR` | 500 | Unhandled server error (always logged with a traceback server-side; never leaks internals to the client) |

Full definitions: `backend/app/core/exceptions.py`.

## Contract-first collaboration

Request/response contracts are agreed here before implementation, so
frontend and backend work can proceed independently — this document was
written and reviewed before `POST /api/v1/support/messages` was built.
