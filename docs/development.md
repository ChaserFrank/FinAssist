# Development

## Prerequisites

- Docker + Docker Compose
- Python 3.12+ (only needed if running outside Docker)

## Running locally

```bash
cp .env.example .env
docker compose up --build
curl http://localhost:8000/health
```

## Running tests / lint

```bash
cd backend
pip install .[dev]
pytest
ruff check .
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

Avoid vague commits like `update`, `fixed stuff`, `final2`.

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
- [ ] No secrets committed
- [ ] CI passes
- [ ] PR reviewed

**Frontend feature:**

- [ ] UI implemented
- [ ] API integrated
- [ ] Loading / error / empty states handled
- [ ] Validation
- [ ] PR reviewed

## Team roles

ChaserFrank (team lead) owns architecture, API contracts, database
conventions, Git conventions, definition of done, and integration
boundaries. Milkah owns frontend implementation independently once a
contract is agreed — she should not need to understand backend
repository internals, and the backend should not dictate frontend
component structure beyond the agreed API.
