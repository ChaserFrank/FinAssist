# Database

## Status

Implemented. Four tables, two Alembic migrations, enforced at both the
Python (SQLAlchemy `Enum`) and database (`CHECK` constraint) level. See
`backend/app/domain/*/models.py` and `backend/migrations/versions/`.

## Engine

PostgreSQL, accessed via SQLAlchemy 2.x. `backend/app/infrastructure/database/`
holds the engine/session (`session.py`) and declarative base plus shared
column helpers (`base.py`). Schema changes go through Alembic — never a
manual `CREATE TABLE`.

## Tables

```text
customers
---------
id UUID PK
reference       VARCHAR(32) UNIQUE  -- e.g. CUS-10001
name            VARCHAR(255)
phone           VARCHAR(32)
email           VARCHAR(255)
created_at, updated_at

transactions
------------
id UUID PK
reference       VARCHAR(32) UNIQUE  -- e.g. TXN-84721
customer_id FK -> customers.id (RESTRICT)
amount          NUMERIC(12,2)
currency        VARCHAR(3)          -- ISO 4217, e.g. "KES"
status          VARCHAR(16) CHECK IN (PENDING, SUCCESS, FAILED, REVERSED)
payment_method  VARCHAR(64)
created_at, updated_at

support_cases
-------------
id UUID PK
reference       VARCHAR(32) UNIQUE  -- e.g. CASE-1001
customer_id FK -> customers.id (RESTRICT)
transaction_id FK -> transactions.id (SET NULL), nullable
category        VARCHAR(64)
description     TEXT
status          VARCHAR(16) CHECK IN (OPEN, IN_REVIEW, RESOLVED, CLOSED)
created_at, updated_at

disputes
--------
id UUID PK
reference       VARCHAR(32) UNIQUE  -- e.g. DSP-1001
support_case_id FK -> support_cases.id (RESTRICT)
transaction_id  FK -> transactions.id (RESTRICT)
reason          TEXT
status          VARCHAR(16) CHECK IN (OPEN, UNDER_REVIEW, RESOLVED, REJECTED)
created_at, updated_at
```

Deferred until genuinely needed (not part of the MVP): `support_conversations`
/ `support_messages` tables for full chat history. Today, each
`POST /api/v1/support/messages` call is stateless — see `docs/ai.md`.

## Conventions

- **UUID internally, human-friendly reference externally**, on *all four*
  entities. `reference` is what the API and customers see; the UUID never
  leaves the database layer. This corrects the original proposal, whose
  schema sketch put `reference` only on `transactions` and `support_cases`
  while `docs/api.md` already assumed one on `customers` and `disputes` too.
- **Enums, not free-text strings**, enforced twice: SQLAlchemy's `Enum` type
  (`native_enum=False`, so adding a status later is a normal migration, not
  a non-transactional `ALTER TYPE`) rejects an invalid value in Python before
  it reaches the database, and a `CHECK` constraint (migration `002`)
  rejects it in the database too, independent of which code path wrote the
  row. See `backend/app/infrastructure/database/base.py`.
- Migrations are hand-written (`backend/migrations/versions/`), reviewed like
  any other code change, rather than blindly trusting autogenerate.

## Reference generation

References are generated server-side, before insert
(`backend/app/infrastructure/database/reference_generator.py`):

- **PostgreSQL**: one native sequence per entity (`customer_ref_seq`,
  `transaction_ref_seq`, `support_case_ref_seq`, `dispute_ref_seq`),
  created in migration `001`. `nextval()` is atomic and non-blocking across
  concurrent transactions, and a value is never reused even if the
  transaction that consumed it rolls back.
- **SQLite** (unit/API tests only): an in-process, thread-safe counter, since
  SQLite has no standalone sequence object.
- A `UNIQUE` constraint on every `reference` column is the backstop
  regardless of how the value was produced.

Formats: `CUS-{n:05d}`, `TXN-{n:05d}`, `CASE-{n:04d}`, `DSP-{n:04d}`.

## Duplicate-dispute constraint

A **partial unique index** enforces "at most one active dispute per
transaction" at the database level, independent of and in addition to the
application-level check in `DisputeService`:

```sql
CREATE UNIQUE INDEX uq_disputes_open_per_transaction
    ON disputes (transaction_id)
    WHERE status IN ('OPEN', 'UNDER_REVIEW');
```

Verified under real concurrent load in
`backend/tests/integration/test_postgres_dispute_concurrency.py` (five
threads race to dispute the same transaction; exactly one succeeds).

## Seed data

`backend/scripts/seed_demo_data.py` creates two customers and five
transactions covering all four statuses (`SUCCESS`, `FAILED`, `PENDING`,
`REVERSED`) with fixed, documented references. Idempotent — safe to re-run.
No real customer or financial data is used.

## Migrations

```text
001_create_domain_tables.py               -- all four tables + sequences (Postgres)
002_add_status_check_constraints.py       -- CHECK constraints (Postgres only;
                                              SQLite tests get the same
                                              guarantee from the ORM's Enum
                                              type on Base.metadata directly)
```
