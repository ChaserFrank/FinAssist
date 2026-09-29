# FinAssist Backend

FastAPI application implementing the FinAssist backend: the authoritative
layer that validates AI-derived intent, enforces business rules, and
persists application state.

## Responsibility

Per the project's architectural principle, the backend:

- validates and authorizes every operation (AI output is never trusted directly)
- owns all business rules (transaction eligibility, dispute rules, etc.)
- is the only component that talks to PostgreSQL
- exposes a small set of controlled capabilities
  (`app/infrastructure/orchestration/workflow_port.py`) that an
  orchestrator — local today, Watson Orchestrate later — can call; it is
  never handed direct database access

## Local development (without Docker)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install .[dev]

cp ../.env.example ../.env
# Edit .env: set DATABASE_URL to a Postgres instance you control, e.g.
#   DATABASE_URL=postgresql+psycopg://finassist:<password>@localhost:5432/finassist
alembic upgrade head
python -m scripts.seed_demo_data
uvicorn app.main:app --reload
```

Then visit `http://localhost:8000/health` and `http://localhost:8000/docs`
(interactive OpenAPI docs, auto-generated from the route/schema
definitions).

## Tests

```bash
DATABASE_URL="sqlite://" pytest --ignore=tests/integration   # 83 tests, no DB needed
```

- `tests/unit/` — business rules in isolation: dispute eligibility (ADR-005),
  AI-output validation (ADR-002), config/secret handling, the secret
  scanner itself, privacy masking.
- `tests/api/` — full HTTP contract tests via `TestClient`, backed by an
  in-memory SQLite database (`tests/conftest.py`).
- `tests/integration/` — real PostgreSQL only: DB sequences, the partial
  unique index preventing duplicate active disputes, and a genuine
  concurrent-request race (5 threads). Requires `TEST_DATABASE_URL` and
  `REQUIRE_INTEGRATION=1`; skips cleanly otherwise.

```bash
docker compose up -d postgres
TEST_DATABASE_URL=postgresql+psycopg://finassist:<password>@localhost:5432/finassist \
  REQUIRE_INTEGRATION=1 pytest tests/integration   # 9 tests
```

## Lint and secrets

```bash
ruff check .
python -m scripts.check_secrets ..
```

The secrets scanner is dependency-free and reports file/line/rule only,
never the matched value — see `docs/security.md`.

## Migrations

```bash
alembic upgrade head                          # apply migrations
alembic revision -m "add X"                   # hand-write a new migration
```

Alembic reads `DATABASE_URL` from application configuration
(`app/config.py`, a `SecretStr` — see `docs/security.md`), so it always
targets the same database as the running app.

```text
migrations/versions/
├── 001_create_domain_tables.py           # customers, transactions, support_cases, disputes + sequences
└── 002_add_status_check_constraints.py   # DB-level CHECK constraints on every status column
```

## Architecture layers

```text
app/
├── api/
│   ├── routes/            # HTTP only — no business logic, no DB access
│   │   ├── health.py
│   │   ├── transactions.py, customers.py
│   │   ├── support_cases.py, support_messages.py
│   │   └── disputes.py
│   └── dependencies.py    # FastAPI DI: get_db, get_*_service
│
├── application/            # Use cases ("what can the system do?")
│   ├── transaction_service.py, customer_service.py
│   ├── support_service.py
│   ├── dispute_service.py        # owns the create-dispute transaction (ADR-006)
│   └── message_service.py        # the "orchestrator": AI -> WorkflowPort -> reply
│
├── domain/                 # Entities and enums
│   ├── customer/, transaction/, support/, dispute/
│   └── each: models.py (SQLAlchemy ORM entity) + enums.py (status enum)
│
├── infrastructure/
│   ├── database/            # engine/session, declarative base, status-enum helpers,
│   │                          reference_generator (DB sequences)
│   ├── repositories/        # thin persistence: add/flush only, never commit (ADR-006)
│   ├── ai/                  # AIService port + AIInterpretation schema (ADR-002),
│   │                          MockAIService (implemented), WatsonXAIService (placeholder)
│   └── orchestration/       # WorkflowPort + LocalWorkflowAdapter (implemented),
│                              WatsonOrchestrateAdapter (placeholder)
│
├── schemas/                 # Pydantic request/response contracts
├── core/                    # exceptions.py (ErrorCode + AppError + handlers),
│                              privacy.py (contact-detail masking), logging.py
└── config.py                # Settings — DATABASE_URL/API keys are SecretStr, no defaults
```

**Where new code belongs:**

- A new HTTP endpoint → `api/routes/`, calling into `application/`
- A new business rule → the relevant `application/*_service.py` (services
  own their transaction boundary — see ADR-006)
- A new database query → `infrastructure/repositories/` (repositories
  never commit)
- A new external integration → `infrastructure/ai/` or
  `infrastructure/orchestration/`, behind the existing `AIService` /
  `WorkflowPort` interfaces
- A new request/response shape → `schemas/`

Routes never contain business logic, direct database queries, or session
management — they call one service method and shape its return value into
a response.
