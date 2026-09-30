# ADR-006: Application Services Own the Database Transaction Boundary

## Status

Accepted

## Context

The original repository skeleton had routes wrap service calls in
`with service._session.begin():`. Three problems with that shape:

1. It reaches into a service's "private" `_session` attribute from the HTTP
   layer, breaking encapsulation and coupling routes to an implementation
   detail.
2. If a route forgets the `with` block (easy to miss in a new endpoint), a
   multi-step write (e.g. support case + dispute) is not atomic.
3. It made unit tests wrap `DisputeService` calls in their own
   `db_session.begin()`, which does not match how the API actually calls it.

## Decision

Application services own commit and rollback for every write they perform.
Repositories only `add()` and `flush()` — they never `commit()`. Routes call
a service method and use its return value directly; they never touch the
session.

```python
# repository: no commit
def create(self, ...) -> Dispute:
    self._session.add(dispute)
    self._session.flush()   # id is populated; not yet durable
    return dispute

# service: owns the boundary
def create_dispute(self, ...) -> Dispute:
    try:
        dispute = self._create_dispute_inner(...)
        self._session.commit()
        return dispute
    except IntegrityError as exc:
        self._session.rollback()
        if _is_active_dispute_violation(exc):
            raise AppError(ErrorCode.DISPUTE_NOT_ELIGIBLE, ...) from exc
        raise
    except Exception:
        self._session.rollback()
        raise
```

The `IntegrityError` branch is narrowed to the specific constraint it expects
(`uq_disputes_open_per_transaction` on Postgres, or the equivalent SQLite
message) via `_is_active_dispute_violation`. Any other integrity error
(a foreign-key violation, a genuine bug) is re-raised rather than silently
reported to the customer as "not eligible" — see the unhandled-exception path
in `app.main`, which logs it and returns `INTERNAL_ERROR`.

## Consequences

- A route is now just: validate input -> call one service method -> shape the
  response. No route can forget to commit or accidentally leave a
  half-written pair of rows.
- Tests call services exactly as routes do (no test-only `session.begin()`
  wrapper), so a passing unit test is a more faithful proxy for the real
  code path.
- Nesting is still safe: `SupportMessageService` calls `DisputeService`
  through `LocalWorkflowAdapter`, and each inner service commits its own
  work. If a future flow needs several service calls to succeed or fail
  together, that flow's own service method — not the route — must own a
  single transaction spanning them.
