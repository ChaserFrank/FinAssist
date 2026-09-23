# Security

## Configuration and secrets

- No credentials are hardcoded anywhere in the codebase.
- All configuration comes from environment variables via
  `backend/app/config.py` (Pydantic Settings).
- `.env.example` documents every variable; a real `.env` is never
  committed (`.gitignore` excludes it).
- IBM credentials (`WATSONX_API_KEY`, `ORCHESTRATE_API_KEY`, etc.) are
  empty in local development and only populated once the IBM TechZone
  environment is available.

## Data boundaries

- **No real customer or financial data** is used anywhere in this
  project. All seed/demo data is synthetic (see `docs/database.md`).
- Watson Orchestrate is given controlled API capabilities
  (`get_transaction`, `create_dispute`, etc.), never direct database
  access — see `docs/orchestration.md`.
- AI-extracted values (amounts, references) are treated as **untrusted
  input** and independently verified against the database before they
  influence application behavior — see `docs/ai.md`.

## Logging

Planned observability fields: `request_id`, `workflow_id`, `intent`,
`transaction_reference`, `workflow status`, `duration`. The following
must never be logged:

- passwords
- API keys / tokens
- full sensitive financial information

`backend/app/core/logging.py` is currently a placeholder — this policy
applies once logging is implemented.

## Access control

Not yet implemented (no auth exists in the foundation stage). Will be
documented here once designed; the codebase deliberately avoids building
complex custom authentication ahead of an MVP that needs it (see
`docs/architecture.md`, "what we are deliberately not building").

## Branch protection

`main` requires CI to pass and at least one review before merge — see
`docs/development.md`.
