# ADR-001: Modular Monolith, Not Microservices

## Status

Accepted

## Context

FinAssist has:

- two developers
- a short project timeline
- synthetic data
- one primary workflow
- no production traffic
- no requirement for independent scaling

A microservices split (customer-service, transaction-service,
support-service, dispute-service, ai-service, orchestration-service,
notification-service) would introduce network failures, service
discovery, multiple deployments, inter-service auth, distributed
logging, more Docker containers, and harder local development — without
providing meaningful value at this scale.

## Decision

Build FinAssist as a **modular monolith**: one FastAPI application, one
PostgreSQL database, one repository (monorepo), with clear internal
module boundaries (transaction / support / dispute) enforced through
layered architecture (api / application / domain / infrastructure)
rather than network boundaries.

## Consequences

- A single PR can span frontend → API → domain → database when a feature
  genuinely crosses those layers.
- If the system later needs independent scaling or team ownership per
  module, modules can be extracted into services — the internal boundary
  already exists, so this is a refactor, not a rewrite.
- We accept the trade-off of not having independent deployability per
  module, which is not a requirement for this MVP.
