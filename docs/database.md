# Database

## Status

No domain tables exist yet. This document records the **proposed** schema
so implementation in a later milestone follows an agreed shape rather than
being invented ad hoc.

## Engine

PostgreSQL, accessed via SQLAlchemy 2.x. Connection setup lives in
`backend/app/infrastructure/database/`. Schema changes will be managed
through Alembic migrations — never manual `CREATE TABLE` statements.

## Proposed tables

```text
customers
---------
id UUID PK
name
phone
email
created_at
updated_at

transactions
------------
id UUID PK
reference
customer_id FK
amount
currency
status          -- enum: PENDING, SUCCESS, FAILED, REVERSED
payment_method
created_at
updated_at

support_cases
-------------
id UUID PK
reference
customer_id FK
transaction_id FK nullable
category
description
status          -- enum: OPEN, IN_REVIEW, RESOLVED, CLOSED
created_at
updated_at

disputes
--------
id UUID PK
support_case_id FK
transaction_id FK
reason
status          -- enum: OPEN, UNDER_REVIEW, RESOLVED, REJECTED
created_at
updated_at
```

Deferred until genuinely needed (not part of the MVP):

```text
support_conversations (id, customer_id, status, created_at, updated_at)
support_messages (id, conversation_id, role, content, created_at)
```

## Conventions

- **UUID internally, human-friendly reference externally.** `id` is a
  UUID primary key; `reference` (e.g. `TXN-84721`, `CASE-1042`) is what
  customers and the API surface. Customers should never see a raw UUID.
- **Enums, not free-text strings**, for every status field — workflow
  logic depends on a predictable, controlled state model.
- Migrations are managed with Alembic (`backend/migrations/`), generated
  via `alembic revision --autogenerate` once models exist.

## Seed data

`backend/scripts/seed_demo_data.py` will populate reproducible synthetic
data once the schema exists — e.g. `CUS-10001`, `TXN-84721` with
`SUCCESS` / `FAILED` / `PENDING` / `REVERSED` scenarios. No real customer
or financial data will ever be used.
