# ADR-002: AI Interprets, Backend Authorizes

## Status

Accepted

## Context

A naive architecture would let the LLM decide and directly execute
actions (e.g. `LLM → refund_money()`). This makes the AI model
authoritative over financial and support outcomes, which is both a
correctness risk (models hallucinate structured data) and a security
risk (no controlled boundary between natural language and state
changes).

## Decision

Adopt the principle: **AI interprets. Orchestration coordinates. Backend
authorizes. Database persists.**

Concretely:

- watsonx.ai only produces structured intent from natural language.
- Watson Orchestrate only coordinates calls to backend capabilities; it
  contains no business rules.
- FastAPI validates, authenticates/authorizes, applies business rules,
  and is the only component that touches PostgreSQL directly.
- **AI-extracted values are treated as untrusted input.** The backend
  independently retrieves and verifies referenced entities (e.g. it
  looks up the real transaction amount rather than trusting the amount
  the AI extracted from the message).
- The AI must be allowed to classify a message as `unknown` rather than
  being forced into one of the known workflows.

## Consequences

- Every AI-driven action has a corresponding, independently-callable
  backend API — useful for testing and for other clients (CLI, future
  mobile app) that bypass AI entirely.
- Slightly more implementation work up front (defining backend
  capabilities and validation) in exchange for a system that fails safe
  when the AI is wrong.
