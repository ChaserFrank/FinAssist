# ADR-004: Reference Generation and Dispute Integrity

## Status

Accepted

## Context

Three gaps were identified during the Phase 1 implementation review:

1. **Missing `reference` on `customers` and `disputes`.** The `database.md`
   proposed schema omitted a human-friendly `reference` column on `customers`
   and `disputes`, yet `api.md` used `customer_reference: "CUS-10021"` in
   its request example and `GET /api/v1/disputes/{reference}` in its endpoint
   list. The project convention ("UUID internally, human-friendly reference
   externally") was inconsistently applied across the four core entities.

2. **No concurrency guarantee for reference uniqueness.** Generating references
   with a Python-side counter or `MAX(id)+1` approach creates a race condition
   under concurrent requests where two processes can compute the same next value
   before either commits.

3. **Duplicate open disputes.** An application-level check alone (query then
   insert) has a TOCTOU (time-of-check/time-of-use) race: two concurrent
   requests for the same transaction can both pass the check and both insert,
   creating two open disputes for a single transaction.

## Decisions

### 1. `reference` on all four core entities

All four entities (`Customer`, `Transaction`, `SupportCase`, `Dispute`)
now carry a `reference VARCHAR(32) NOT NULL UNIQUE` column as their
external identifier.

| Entity | Reference format | Example |
|---|---|---|
| Customer | `CUS-{n:05d}` | `CUS-10001` |
| Transaction | `TXN-{n:05d}` | `TXN-84721` |
| SupportCase | `CASE-{n:04d}` | `CASE-1042` |
| Dispute | `DSP-{n:04d}` | `DSP-1042` |

All API endpoints use `{reference}` path parameters, never `{id}`.

### 2. Concurrency-safe reference generation via database sequences

In PostgreSQL (production and integration tests), one native sequence
per entity type is created alongside the domain tables:

```sql
CREATE SEQUENCE customer_ref_seq START 10001;
CREATE SEQUENCE transaction_ref_seq START 80001;
CREATE SEQUENCE support_case_ref_seq START 1001;
CREATE SEQUENCE dispute_ref_seq START 1001;
```

`nextval()` is atomic, non-blocking across transactions, and
unaffected by transaction rollbacks — the next sequence value is
consumed even if the inserting transaction later rolls back. This
is the desired behaviour: we never reuse a reference, even if the
row that used it was never committed.

In the test environment (SQLite, which does not support standalone
sequences), `ReferenceGenerator` falls back to an in-process
counter that is safe within single-process test runs.

A `UNIQUE` constraint on every `reference` column provides a
database-level collision safeguard regardless of how the value was
generated.

### 3. Preventing duplicate open disputes via partial unique index

A partial unique index is placed on the `disputes` table:

```sql
CREATE UNIQUE INDEX uq_disputes_open_per_transaction
    ON disputes (transaction_id)
    WHERE status IN ('OPEN', 'UNDER_REVIEW');
```

This prevents more than one active dispute per transaction at the
database level. Combined with an application-level pre-check in
`DisputeService`, the defence is two-layered:

- The application check (`DisputeService`) provides a fast, friendly
  error message before touching the database in the happy path.
- The index is the true enforcement boundary. Any concurrent request
  that races past the application check will receive a constraint
  violation that is caught and converted to `DISPUTE_NOT_ELIGIBLE`.

Both SQLite (≥ 3.8.0) and PostgreSQL support partial unique indexes,
so the same Alembic migration generates valid DDL in both environments.

### 4. Atomic support case and dispute creation

Creating a dispute always creates a `SupportCase` first (the customer
support tracking record), then a `Dispute` referencing it. Both inserts
must succeed or neither must persist. `DisputeService.create_dispute`
wraps both operations in an explicit `session.begin()` block.
Repositories only call `session.add()` and `session.flush()` — they
never call `session.commit()`. The commit is the service's responsibility.

## Consequences

- All four core entities are consistently addressable by a human-friendly
  reference; internal UUIDs are never surfaced at the API layer.
- Reference generation scales safely to concurrent requests without
  application-level locking.
- It is impossible to create two open disputes for a single transaction
  even under parallel requests.
- The `POST /api/v1/disputes` response returns both `reference`
  (the dispute's own `DSP-xxx`) and `support_case_reference` (`CASE-xxx`),
  giving callers visibility into both related records without a second
  request.
- `GET /api/v1/customers/{id}` in the original `api.md` is superseded
  by `GET /api/v1/customers/{reference}`. This is a pre-implementation
  correction; no live clients are affected.
