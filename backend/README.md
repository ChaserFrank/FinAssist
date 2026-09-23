# FinAssist Backend

FastAPI application implementing the FinAssist backend: the authoritative
layer that validates AI-derived intent, enforces business rules, and
persists application state.

## Responsibility

Per the project's architectural principle, the backend:

- validates and authorizes every operation (AI output is never trusted directly)
- owns all business rules (transaction eligibility, dispute rules, etc.)
- is the only component that talks to PostgreSQL
- exposes a small set of controlled capabilities that Watson Orchestrate
  can call — it is never handed direct database access

## Local development (without Docker)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install .[dev]

cp ../.env.example ../.env   # if not already done at the repo root
uvicorn app.main:app --reload
```

Then visit `http://localhost:8000/health` and `http://localhost:8000/docs`.

## Tests

```bash
pytest
```

The `/health` test (`tests/api/test_health.py`) requires no external
services. As domain/repository tests are added, `tests/unit` will cover
business rules in isolation, `tests/integration` will exercise
repositories against a real database, and `tests/api` will cover HTTP
contracts.

## Lint

```bash
ruff check .
```

## Migrations

```bash
alembic upgrade head          # apply migrations
alembic revision --autogenerate -m "add X"   # generate a new migration
```

Alembic reads `DATABASE_URL` from application configuration
(`app/config.py`), so it always targets the same database as the running
app — there's nothing to keep in sync separately in `alembic.ini`.

No domain migrations exist yet, because no domain models exist yet.

## Architecture layers

```text
app/
├── api/              # HTTP layer only — no business logic, no DB access
│   ├── routes/
│   └── dependencies.py
├── application/      # Use cases ("what can the system do?")
├── domain/           # Entities, enums, and business rules
├── infrastructure/   # External technology: DB, AI adapters, orchestration adapters
├── schemas/          # Pydantic request/response contracts
└── core/             # Cross-cutting: error taxonomy, logging
```

**Where new code belongs:**

- A new HTTP endpoint → `api/routes/`, calling into `application/`
- A new business rule → `domain/<entity>/` or the relevant `application/*_service.py`
- A new database query → `infrastructure/repositories/`
- A new external integration → `infrastructure/ai/` or `infrastructure/orchestration/`,
  behind the existing `AIService` / `WorkflowPort` interfaces
- A new request/response shape → `schemas/`

Routes never contain business logic or direct database queries — they
delegate to application services. Domain rules stay independent of
whether the caller was HTTP, Watson Orchestrate, or a test.
