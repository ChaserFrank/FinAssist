"""Health check endpoint.

Deliberately independent of the database and any application/domain
services, so it can be used as an infrastructure-level liveness check
(Docker healthcheck, load balancer probe, CI smoke test) without pulling
in the rest of the system.
"""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def get_health() -> dict[str, str]:
    """Return a minimal liveness signal."""
    return {"status": "ok"}
