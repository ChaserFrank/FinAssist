"""Customer routes.

HTTP layer only -- no business logic, no direct database access.
Customer lookup uses the human-friendly reference, never the internal UUID.

Contact details are masked in the response: there is no authentication yet,
so the API must not hand full phone/email to arbitrary callers.
"""

from fastapi import APIRouter, Depends

from app.api.dependencies import get_customer_service
from app.application.customer_service import CustomerService
from app.core.privacy import mask_email, mask_phone
from app.schemas.customer import CustomerResponse

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("/{reference}", response_model=CustomerResponse)
def get_customer(
    reference: str,
    service: CustomerService = Depends(get_customer_service),
) -> CustomerResponse:
    """Retrieve a customer (contact details masked) by reference, e.g. CUS-10021.

    Raises HTTP 404 (CUSTOMER_NOT_FOUND) if the reference does not exist.
    """
    customer = service.get_customer(reference)
    return CustomerResponse(
        reference=customer.reference,
        name=customer.name,
        phone=mask_phone(customer.phone),
        email=mask_email(customer.email),
        created_at=customer.created_at,
    )
