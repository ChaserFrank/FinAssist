# AI Integration (watsonx.ai)

## Status

Not yet implemented. This document records the intended contract and
boundary.

## Role

watsonx.ai's job is narrow: **understand natural language and produce
structured intent.** It does not decide outcomes and it does not call
backend operations directly.

## Structured output contract

```json
{
  "intent": "payment_dispute",
  "transaction_reference": null,
  "amount": 3500,
  "currency": "KES",
  "confidence": 0.94,
  "requires_transaction_lookup": true
}
```

Supported intents (initial set):

```text
transaction_status
payment_failed
payment_dispute
support_case_status
unknown
```

`unknown` is a required, valid output — the model must be allowed to say
it doesn't understand a message rather than being forced into one of the
known workflows.

## Untrusted input principle

**AI output is treated as untrusted input and must be validated before
influencing application behavior.** If the AI extracts a transaction
reference and amount, the backend independently retrieves the real
transaction and verifies the amount — it never trusts the AI's numbers
directly.

## Adapter boundary

```text
application code
      │
      ▼
AIService (Protocol, backend/app/infrastructure/ai/ai_port.py)
      │
      ├── MockAIService        — local development, canned responses to fixed example messages
      └── WatsonXAIService     — calls watsonx.ai using WATSONX_API_KEY / WATSONX_PROJECT_ID / WATSONX_URL
```

Application code depends only on the `AIService` interface, never on a
concrete implementation — see `decisions/003-local-first-integration.md`.

## Configuration

```text
WATSONX_API_KEY
WATSONX_PROJECT_ID
WATSONX_URL
```

Empty locally. No network calls are made until these are populated and
`WatsonXAIService` is implemented.
