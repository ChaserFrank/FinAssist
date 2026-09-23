# FinAssist

FinAssist is an AI-powered payment support and resolution agent, built for
the IBM Tech Training Phase 3 project (Team 5).

It is a **payment-support workflow system with an AI interface** — not an
"AI chatbot" that is trusted to act on the world directly.

## Core architectural principle

> **AI interprets. Orchestration coordinates. Backend authorizes. Database persists.**

| Component | Responsibility |
|---|---|
| React frontend | Collect and display information |
| watsonx.ai | Understand natural language |
| Watson Orchestrate | Coordinate workflow/tool calls |
| FastAPI backend | Validate, enforce business rules, execute operations |
| PostgreSQL | Persist authoritative application state |

AI output is treated as **untrusted input**. The backend independently
verifies anything the AI extracts (transaction references, amounts, etc.)
before it influences application behavior.

## Architecture

We are deliberately building a **modular monolith**, not microservices —
see `docs/decisions/001-modular-monolith.md` for the reasoning. Two
developers, one primary workflow, no independent scaling requirement.

Read `docs/architecture.md` for the full picture, and `docs/decisions/`
for the Architecture Decision Records (ADRs) behind the major calls.

## Repository structure

```text
finassist/
├── backend/     # FastAPI application (see backend/README.md)
├── frontend/    # React application (owned by Milkah, not yet implemented)
├── docs/        # Architecture, API contract, and decision records
├── infra/       # Supporting infrastructure config
└── .github/     # CI workflow, issue/PR templates
```

## Local prerequisites

- Docker and Docker Compose
- (Optional, for running outside Docker) Python 3.12+

## Getting started

```bash
cp .env.example .env
docker compose up --build
```

Once running, verify the backend is up:

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

## Running tests

```bash
cd backend
pip install .[dev]
pytest
ruff check .
```

Or via Docker:

```bash
docker compose exec backend pytest
```

## Branch strategy

- `main` always represents a working state.
- One feature branch per logical change: `feature/<short-description>`.
- Pull requests require CI to pass and at least one review before merging.
- No direct commits to `main`.

See `docs/development.md` for full conventions (commit messages, PR
structure, definition of done).

## Current project status

**Foundation stage.** This repository currently provides:

- FastAPI application skeleton with a working `GET /health` endpoint
- Configuration via environment variables (Pydantic Settings)
- SQLAlchemy + PostgreSQL connection infrastructure (no domain tables yet)
- Alembic migration scaffolding (no domain migrations yet)
- Docker Compose for local development (`postgres` + `backend`)
- CI running lint and tests
- Architecture documentation and ADRs
- Reserved frontend workspace for Milkah

**Business logic (transactions, customers, support cases, disputes,
AI/orchestration integration) is intentionally not implemented yet.** See
`docs/decisions/` and the milestone sequence in `docs/architecture.md`
for what comes next.
