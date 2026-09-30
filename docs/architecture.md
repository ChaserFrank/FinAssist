# Architecture

## Principle

> AI interprets. Orchestration coordinates. Backend authorizes. Database persists.

FinAssist is a payment-support workflow system with an AI interface, not
an AI agent trusted to act on the world directly.

## Style: modular monolith

See `decisions/001-modular-monolith.md`. One FastAPI application, one
PostgreSQL database, internal module boundaries (transaction / support /
dispute) rather than separate services.

## Layers (backend)

```text
API layer            → HTTP only, no business logic
Application layer    → use cases ("what can the system do?")
Domain layer          → entities, enums, business rules
Infrastructure layer  → DB, AI adapters, orchestration adapters
```

Dependency direction always points inward: infrastructure depends on
application/domain interfaces, never the reverse.

## AI and orchestration boundary

See `decisions/002-ai-backend-boundary.md`. The backend exposes
capabilities (e.g. `get_transaction`, `create_dispute`) that Watson
Orchestrate calls; it never receives direct database access, and its
output is treated as untrusted input that the backend independently
verifies.

```text
AIService (port)
  ├── MockAIService        (local development)
  └── WatsonXAIService     (IBM TechZone)

WorkflowPort (port)
  ├── LocalWorkflowAdapter       (local development)
  └── WatsonOrchestrateAdapter   (IBM TechZone)
```

See `decisions/003-local-first-integration.md` for why local/mock
adapters come first.

## End-to-end flow (implemented)

```text
Customer message
      │
      ▼
AI produces structured intent (untrusted)
      │
      ▼
Orchestrator calls a backend capability
      │
      ▼
Backend validates, authorizes, applies business rules
      │
      ▼
PostgreSQL persists the result
      │
      ▼
AI phrases the (backend-authoritative) result back to the customer
```

## Milestone sequence

1. ✅ Repository + architecture foundation
2. ✅ Local infrastructure (Docker Compose, Postgres, FastAPI, Alembic, health)
3. ✅ Domain (Customer, Transaction, SupportCase, Dispute) — see ADR-004, ADR-005
4. ✅ Transaction workflow (get transaction, ownership-scoped)
5. ✅ Dispute workflow (investigate → validate → create case → create dispute) — ADR-005, ADR-006
6. ✅ Frontend (customer input → API → result) — `POST /api/v1/support/messages`
7. ✅ Local AI adapter (message → structured intent) — `MockAIService`, ADR-002
8. ✅ Local orchestration (intent → tool → backend → result) — `LocalWorkflowAdapter`
9. ⬜ IBM integration (swap in `WatsonXAIService` / `WatsonOrchestrateAdapter`)
10. End-to-end hardening (tests, logging, error handling, security, docs, demo)

## What we are deliberately not building

Kubernetes, Kafka, microservices, Redis, Celery, event sourcing, CQRS,
GraphQL, a service mesh, complex custom auth, multi-agent architecture, or
real payment integration. The MVP goal is the smallest architecture that
gives strong boundaries and solves the actual problem.
