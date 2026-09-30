"""Customer API schemas.

Pydantic models for the customer resource.  The API never exposes the
internal UUID — only the human-friendly ``reference`` — and returns contact
details **masked** (see ``app.core.privacy``).
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CustomerResponse(BaseModel):
    """Response shape for ``GET /api/v1/customers/{reference}``."""

    model_config = ConfigDict(from_attributes=True)

    reference: str
    name: str
    phone: str
    email: str
    created_at: datetime
