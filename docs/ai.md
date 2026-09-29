# AI Integration

## Status

**Implemented (mock).** `MockAIService` (`backend/app/infrastructure/ai/mock_ai_service.py`)
is a deterministic, keyword-based stand-in for watsonx.ai. It does the same
*job* — text in, validated structured intent out — with no network call, no
credentials, and no real language understanding. `WatsonXAIService`
(`watsonx_ai_service.py`) remains a documented placeholder until IBM TechZone
access is available; swapping it in requires no application-layer change
(ADR-003).

## Contract

`backend/app/infrastructure/ai/ai_port.py` defines the shape every provider
must produce, as a validated Pydantic model (`AIInterpretation`), not a bare
dict:

```python
class AIInterpretation(BaseModel):
    intent: Intent                          # closed enum, see below
    transaction_reference: str | None       # must match ^TXN-\d{4,9}$ or is rejected
    case_reference: str | None              # must match ^CASE-\d{4,9}$ or is rejected
    amount: Decimal | None                  # must be >= 0
    currency: str | None
    confidence: float                       # 0.0-1.0
    requires_transaction_lookup: bool
```

Intents:

```text
transaction_status
payment_failed
payment_dispute
support_case_status
unknown
```

`unknown` is a required, valid output — the assistant must be able to say it
didn't understand rather than being forced into a workflow.

## Untrusted-input principle (ADR-002)

Every provider's raw output is passed through `parse_ai_output()` before
anything else touches it. Malformed output — a transaction reference in the
wrong shape, a negative amount, an intent outside the closed set — is
**discarded and replaced with `unknown`**, not partially trusted. This is
enforced in code, not just policy: see
`backend/tests/unit/test_ai_interpretation.py`.

Even a *well-formed* interpretation is only a hint:

- `transaction_reference` is used to **look up** the transaction; the backend
  never trusts an AI-stated status, amount, or ownership.
- `amount` is only ever **compared** against the real transaction's amount
  (surfaced to the customer as `amount_mismatch`); it never substitutes for
  the real amount in a reply or a dispute record.
- `SupportMessageService` re-derives every fact in its reply from the
  backend's own data (`docs/architecture.md`'s "backend authorizes"
  boundary), never from the AI's text.

## Configuration

```text
WATSONX_API_KEY
WATSONX_PROJECT_ID
WATSONX_URL
```

Empty locally (no default — see `docs/security.md`). No network call is made
until `WatsonXAIService` is implemented and these are populated.

## What's deliberately not built yet

- Conversation memory across messages (`docs/database.md`'s deferred
  `support_conversations` / `support_messages` tables) — each
  `POST /api/v1/support/messages` call is stateless today.
- A real NLU model. `MockAIService`'s keyword matching is intentionally
  simple; it exists to exercise the AI/backend boundary correctly, not to be
  a good chatbot.
