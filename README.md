# FinAssist

FinAssist is an AI-powered payment support and resolution agent, built for
the IBM Tech Training.

It is a **payment-support workflow system with an AI interface** — not an
"AI chatbot" that is trusted to act on the world directly.

## Core architectural principle

> **AI interprets. Orchestration coordinates. Backend authorizes. Database persists.**

| Component | Responsibility | Status                                   |
|---|---|------------------------------------------|
| React frontend | Collect and display information | Implemented                              |
| watsonx.ai | Understand natural language | `MockAIService` stand-in (ADR-003)       |
| Watson Orchestrate | Coordinate workflow/tool calls | `LocalWorkflowAdapter` stand-in (ADR-003) |
| FastAPI backend | Validate, enforce business rules, execute operations |  Implemented                            |
| PostgreSQL | Persist authoritative application state |  Implemented                             |

AI output is treated as **untrusted input**. The backend independently
verifies anything the AI extracts (transaction references, amounts, etc.)
before it influences application behavior — see `docs/ai.md`.

## Architecture

We are deliberately building a **modular monolith**, not microservices —
see `docs/decisions/001-modular-monolith.md` for the reasoning.

Read `docs/architecture.md` for the full picture, and `docs/decisions/`
for the Architecture Decision Records (ADRs) behind the major calls:

| ADR | Decision |
|---|---|
| 001 | Modular monolith, not microservices |
| 002 | AI interprets, backend authorizes (untrusted-input principle) |
| 003 | Local-first IBM integration (mock AI + local orchestration first) |
| 004 | Reference generation (DB sequences) and duplicate-dispute integrity (partial unique index) |
| 005 | Dispute eligibility matrix (which transaction states can be disputed, and why) |
| 006 | Application services own the database transaction boundary |

## Repository structure

```text
finassist/
├── backend/     # FastAPI application (see backend/README.md)
├── frontend/    # React application (Vite) — support chat UI
├── docs/        # Architecture, API contract, and decision records
├── infra/       # Supporting infrastructure config
└── .github/     # CI workflow, issue/PR templates
```

## Local prerequisites

- Docker and Docker Compose
- Python 3.12+ (only needed to run the backend outside Docker)
- Node 22+ (only needed to run the frontend)

## Getting started

```bash
cp .env.example .env
# Edit .env and set a real POSTGRES_PASSWORD, e.g.: openssl rand -hex 16
docker compose up --build
docker compose exec backend alembic upgrade head
docker compose exec backend python -m scripts.seed_demo_data
```

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

Frontend, in a separate terminal:

```bash
cd frontend
npm install
echo "VITE_API_BASE_URL=http://localhost:8000" > .env
npm run dev
# open http://localhost:5173
```

Try it: enter customer reference `CUS-10021` and message
*"I was charged 800 for TXN-84722 but it failed"* — this opens a support
case and a dispute against the seeded demo data. See `docs/api.md` for the
full endpoint reference.

## Running tests

```bash
cd backend
pip install ".[dev]"  
DATABASE_URL="sqlite://" pytest --ignore=tests/integration   # 83 tests, no DB needed
ruff check .
python -m scripts.check_secrets ..                            # no hard-coded secrets
```

Integration tests prove behaviour SQLite cannot (DB sequences, the partial
unique index, concurrent dispute creation under real load):

```bash
docker compose up -d postgres
TEST_DATABASE_URL=postgresql+psycopg://finassist:<password>@localhost:5432/finassist \
  REQUIRE_INTEGRATION=1 pytest tests/integration    # 9 tests
```

Frontend:

```bash
cd frontend && npm run build
```

CI (`.github/workflows/ci.yml`) runs all of the above — lint, secrets scan,
unit/API tests, migrations + integration tests against a real ephemeral
Postgres, and the frontend build — on every push and PR.

## Branch strategy

- `main` always represents a working state.
- One feature branch per logical change: `feature/<short-description>`.
- Pull requests require CI to pass and at least one review before merging.
- No direct commits to `main`.

See `docs/development.md` for full conventions (commit messages, PR
structure, definition of done).

## Current project status

**Core backend implemented and verified end to end**, per the architecture
proposal's milestones 1–8 (see `docs/architecture.md`). Verified against a
real PostgreSQL instance and a real browser driving the real frontend
against the real backend — not just the in-memory test suite.

Implemented:

- Domain models (Customer, Transaction, SupportCase, Dispute) with
  DB-enforced status enums and human-friendly references (`docs/database.md`)
- Full CRUD/lookup API under `/api/v1` (`docs/api.md`)
- Dispute business rules: eligibility matrix (ADR-005), duplicate-dispute
  prevention enforced at both the application and database level (ADR-004),
  verified under concurrent load against real Postgres
- The conversational flow — `POST /api/v1/support/messages` — wiring
  together `MockAIService` (ADR-002 untrusted-input validation) and
  `LocalWorkflowAdapter` (the orchestration boundary) with zero business
  logic in either
- React frontend wired to the real API (customer reference + free-text
  message → live backend response), not just a static form
- 92 automated tests (83 unit/API on SQLite, 9 integration on real
  PostgreSQL including a 5-thread concurrency race), all passing
- A consistent error envelope across every endpoint, including request
  validation errors
- Masked personal data on unauthenticated endpoints, and cross-customer
  lookups reported as "not found" rather than leaking ownership
  (`docs/security.md`)
- A dependency-free secret scanner (`scripts/check_secrets.py`) wired into
  both the test suite and CI

**Not yet implemented** (deliberately, per ADR-003 and the "what we are
deliberately not building" list in `docs/architecture.md`):

- Real watsonx.ai / Watson Orchestrate integration (Milestone 9) — the
  `AIService` / `WorkflowPort` interfaces are ready; only the IBM-backed
  adapters remain to be written once TechZone credentials exist
- Authentication (`docs/security.md`) — `customer_reference` is currently a
  claimed identity, mitigated but not replaced by masking and
  not-found-not-mismatch responses
- Conversation history / multi-turn context (`support_conversations` /
  `support_messages` tables remain deferred, as originally scoped)

