# Security

## Incident: hard-coded database credential (resolved)

A previous revision of this repository committed a real-looking database
password in three places: `backend/app/config.py` (as the `DATABASE_URL`
default), `docker-compose.yml` (as a shell-fallback default), and
`.env.example`. **If this was ever pushed to a remote repository, treat that
credential as compromised: rotate the database password (and any account
that reused it) regardless of what this document says next.**

What changed:

- `Settings.DATABASE_URL` has **no default**. A missing value now fails
  application startup immediately with a clear error, instead of silently
  falling back to a credential that happened to be in source control.
- `docker-compose.yml` requires `POSTGRES_PASSWORD` from your `.env` file
  (`${POSTGRES_PASSWORD:?Set POSTGRES_PASSWORD in .env}`) — Compose refuses
  to start rather than defaulting.
- `.env.example` documents the required variables with **no values**, plus
  a one-line command to generate a strong one (`openssl rand -hex 16`).
- `DATABASE_URL`, `WATSONX_API_KEY`, and `ORCHESTRATE_API_KEY` are now
  `pydantic.SecretStr`, so they render as `**********` in reprs, logs, and
  tracebacks. The real value is only unwrapped at the exact point of use
  (`get_secret_value()`, called in exactly two places: engine creation and
  the Alembic env script).
- `backend/tests/integration/test_postgres_dispute_concurrency.py` no longer
  has a default connection string; it reads `TEST_DATABASE_URL` and skips
  cleanly if unset.

## Incident 2: GitGuardian flagged the CI-only credential and a test fixture (resolved)

Opening a PR into `main` surfaced 4 GitGuardian findings. Two were the
*same* literal password from Incident 1 above, still present in earlier
commits on the branch — GitGuardian scans every commit in a PR's range,
not just the final diff, so fixing a file's current content does not by
itself clear a finding tied to an older commit. **If this branch is shared
with anyone else, do not force-push over it without telling them first**;
otherwise the fix is to rewrite this feature branch's history before
merging:

```bash
git checkout <your-branch>
git fetch origin
git reset --soft origin/main   # uncommit everything on this branch, keep the files
git commit -m "feat: FinAssist backend, frontend integration, and security fixes"
git push --force-with-lease
```

This squashes the branch into one clean commit containing only the current
(already-fixed) file contents, so the old commits containing the real
password no longer exist anywhere in the PR's history for GitGuardian to
find. `--force-with-lease` (not plain `--force`) refuses to overwrite the
branch if someone else has pushed to it since you last fetched.

The other two findings were in *current* files and both were genuine, if
low-risk, patterns worth fixing rather than ignoring:

- `.github/workflows/ci.yml` had a literal ephemeral Postgres password
  (`finassist_ci:finassist_ci`) in the workflow's `services:` block. That
  block requires its credentials as a literal at YAML-parse time (services
  start before any step runs), which is structurally the same
  "password committed to a file" pattern regardless of how low-stakes the
  database behind it is. Fixed by starting PostgreSQL from a step instead
  (`docker run`), generating the password at runtime with `openssl rand
  -hex 16` and passing it through `$GITHUB_ENV` — no credential-shaped
  string is ever written to the file. See `.github/workflows/ci.yml` and
  `backend/tests/unit/test_no_hardcoded_secrets.py::
  test_ci_workflow_never_writes_a_literal_database_password`.
- `backend/tests/unit/test_no_hardcoded_secrets.py` built its "fake
  secret" test fixtures by concatenating string fragments (e.g.
  `"Zx9" + "qLm2" + "Vt"`) assigned to a variable named `_PW`. That defeats
  *our own* regex scanner (which is the point — the fragments never appear
  as one literal), but a variable named like a credential holding
  string-literal fragments still visually matches the exact
  hardcoded-assignment shape these tools exist to catch, disguised or not.
  Fixed by generating every fake value at runtime with
  `secrets.token_hex()` instead, so no secret-shaped literal of any kind
  exists in that file's source. `.gitguardian.yaml` also lists this file
  under `secret.ignored_paths` as a second, independent layer, since it
  necessarily contains AWS-key-/GitHub-token-*shaped* strings to verify our
  scanner recognizes those shapes.

## Automated secret scanning

`backend/scripts/check_secrets.py` is a dependency-free scanner
(`python -m scripts.check_secrets`) that looks for: credentialed URIs,
literal password/token/API-key assignments, secret defaults in
shell/Compose fallback syntax, and known vendor key formats (AWS, GitHub,
OpenAI-style, Slack, private-key blocks, JWTs). It reports **file, line, and
rule only — never the matched value**, so its own output (and CI logs)
cannot leak what it caught. (The two example patterns above this paragraph,
and the two throwaway CI-only credentials in `.github/workflows/ci.yml`,
are annotated `# pragma: allowlist secret` — the scanner's documented
escape hatch for false positives, explained in the script's own docstring.)

- `make secrets-check` runs it as part of the test suite
  (`tests/unit/test_no_hardcoded_secrets.py`), so a new hard-coded secret
  fails CI the same way a broken test would, not just a pre-commit hook
  someone can skip with `--no-verify`.
- This complements, and does not replace, GitGuardian / gitleaks scanning
  on the actual git history — this scanner only sees the working tree.

## Configuration and secrets

- No credential, password, token, or connection string with embedded
  credentials appears anywhere in source control (verified by the scanner
  above, re-run against this repository before every handoff).
- All configuration comes from environment variables via
  `backend/app/config.py` (Pydantic Settings). `.env` is git-ignored;
  `.env.example` documents every variable with no real values.
- `backend/.dockerignore` excludes `.env*` (except `.env.example`) so a
  local secret can never be baked into a built image layer.
- The Postgres port and the backend's own port are bound to
  `127.0.0.1` in `docker-compose.yml`, not `0.0.0.0` — not reachable from
  the local network by default.
- The Docker image runs as an unprivileged user (`appuser`, uid 10001), not
  root.
- IBM credentials (`WATSONX_API_KEY`, `ORCHESTRATE_API_KEY`) are empty
  locally and only populated once IBM TechZone access exists.

## Personal data

- `GET /api/v1/customers/{reference}` returns **masked** phone and email
  (`app/core/privacy.py`) — `+254*******21`, `b**@example.com` — because
  there is no authentication yet (see below) and the reference alone is not
  proof of identity.
- `POST /api/v1/support/messages` treats `customer_reference` as a *claimed*
  identity: a request for another customer's transaction or case is
  answered exactly like a request for one that doesn't exist
  (`outcome: "not_found"`), so the endpoint cannot be used to enumerate
  which references belong to other customers. See `docs/api.md`.
- No real customer or financial data exists anywhere in this project — all
  seed/demo data is synthetic (`docs/database.md`).

## AI-extracted data is untrusted input

An AI-derived transaction reference, case reference, or amount is validated
against a closed schema before use, and even valid values are only ever used
to *look up* or *compare against* the backend's own authoritative data —
never substituted for it. See `docs/ai.md` and ADR-002.

## Logging

`backend/app/core/logging.py` configures the root logger at startup.
Current policy, enforced in the exception handlers
(`backend/app/core/exceptions.py`):

- Unhandled exceptions are always logged with a full traceback server-side,
  but the client only ever receives `{"error": {"code": "INTERNAL_ERROR", ...}}`
  — never a stack trace or exception message.
- Only HTTP method and path are logged for an error, never the query string
  or request body (which may contain a customer's free-text message or
  dispute reason).
- Never logged: passwords, API keys/tokens, full financial details.

## Access control

Not yet implemented. `customer_reference` is currently a claimed identity
with no proof of ownership — see "Personal data" above for the mitigations
in place (masking, not-found-not-mismatch responses) in the absence of
authentication. Real authentication is required before this system handles
non-synthetic data, and is intentionally out of scope for this MVP
(`docs/architecture.md`, "what we are deliberately not building").

## CORS

Configurable via `CORS_ORIGINS` (comma-separated), defaulting to the Vite
dev server (`http://localhost:5173`). Only `GET`/`POST` and the headers the
frontend actually sends are allowed; credentials are not sent
cross-origin. Set `CORS_ORIGINS` explicitly for any deployment other than
local development.

## Branch protection

`main` requires CI to pass (tests, lint, and the secrets check) and at least
one review before merge — see `docs/development.md`.
