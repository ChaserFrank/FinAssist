# ADR-003: Local-First IBM Integration

## Status

Accepted

## Context

As instructed by the team lead, the team to get the project working locally while
the IBM TechZone environment is being prepared. Backend, frontend,
database, and business-rule development should not be blocked on IBM
service availability.

## Decision

Develop FinAssist against local/mock implementations of the AI and
orchestration interfaces before connecting to IBM TechZone:

```text
AIService (port)
  MockAIService        → used locally
  WatsonXAIService      → used once IBM TechZone is available

WorkflowPort (port)
  LocalWorkflowAdapter        → used locally
  WatsonOrchestrateAdapter    → used once IBM TechZone is available
```

Application code depends only on the `AIService` / `WorkflowPort`
interfaces, never on a concrete adapter, so swapping implementations
requires no application-layer changes.

## Consequences

- Backend, frontend, database, and business-rule work can proceed in
  parallel, independent of IBM environment availability.
- Integration with watsonx.ai and Watson Orchestrate becomes a
  replaceable infrastructure concern (Milestone 9), not a foundational
  dependency the whole system is built around.
- We accept that `MockAIService` and `LocalWorkflowAdapter` behavior may
  not perfectly match production IBM behavior, and integration testing
  against real IBM services is still required before the project is
  considered complete.
