# Development

## Prerequisites

- Docker + Docker Compose
- Python 3.12+ (only needed if running outside Docker)
- Node 22+ (for frontend work)

## Running locally

```bash
cp .env.example .env
# Edit .env: set POSTGRES_PASSWORD to a real value, e.g.
#   openssl rand -hex 16
docker compose up --build
docker compose exec backend alembic upgrade head
docker compose exec backend python -m scripts.seed_demo_data
curl http://localhost:8000/health
```

Frontend (separate terminal):

```bash
cd frontend
npm install
echo "VITE_API_BASE_URL=http://localhost:8000" > .env
npm run dev
```

The backend's `CORS_ORIGINS` default already allows Vite's dev server
(`http://localhost:5173`). If you run the frontend on a different port
(e.g. `npm run preview`), add that origin to `CORS_ORIGINS` in `.env` and
restart the backend.

## Running tests / lint

```bash
cd backend
pip install .[dev]
DATABASE_URL="sqlite://" pytest --ignore=tests/integration   # unit + API, no DB needed
ruff check .
python -m scripts.check_secrets ..                            # guardrail: no hard-coded secrets
```

Integration tests exercise real PostgreSQL behaviour (sequences, the
partial unique index, concurrent dispute creation) that SQLite cannot
prove:

```bash
docker compose up -d postgres
TEST_DATABASE_URL=postgresql+psycopg://finassist:<password>@localhost:5432/finassist \
  REQUIRE_INTEGRATION=1 pytest tests/integration
```

## Git strategy

- `main` always represents a working state. No direct commits to `main`.
- One feature branch per logical change: `feature/<short-description>`.
- Example: `git switch -c feature/transaction-api`.
- Open a PR, get at least one review (there are two of us — review each
  other), merge, delete the branch.

## Commit convention

```text
feat: add transaction domain model
fix: prevent disputes for resolved transactions
test: cover transaction lookup errors
docs: document local development setup
chore: add postgres compose service
```

## Pull requests

Every PR should answer (see `.github/pull_request_template.md`):

- What changed, and why?
- How was it tested?
- Are there database/API/configuration changes?
- Anything the reviewer should specifically inspect?

Branch protection on `main` requires CI to pass and at least one review.

## Definition of done

**Backend feature:**

- [ ] Implementation complete
- [ ] Business rules documented
- [ ] Tests added
- [ ] API contract documented (`docs/api.md`)
- [ ] Error cases handled with a defined `ErrorCode`
- [ ] Logging considered
- [ ] No secrets committed (`python -m scripts.check_secrets ..`)
- [ ] CI passes
- [ ] PR reviewed

**Frontend feature:**

- [ ] UI implemented
- [ ] API integrated
- [ ] Loading / error / empty states handled
- [ ] Validation
- [ ] PR reviewed

## Team roles

Francis Kimani (team lead) owns architecture, API contracts, database
conventions, Git conventions, definition of done, and integration
boundaries. 

Milkah owns frontend implementation independently once a
contract is agreed — she should not need to understand backend
repository internals, and the backend should not dictate frontend
component structure beyond the agreed API.
