"""Helpers for masking personal data before it leaves the API.

There is no authentication yet (see docs/security.md), so endpoints that
return customer details must not expose full contact data to any caller.
"""


def mask_phone(phone: str) -> str:
    """``+254700000021`` -> ``+254*******21`` (keep prefix and last two digits)."""
    if len(phone) <= 6:
        return "*" * len(phone)
    return f"{phone[:4]}{'*' * (len(phone) - 6)}{phone[-2:]}"


def mask_email(email: str) -> str:
    """``bob@example.com`` -> ``b**@example.com`` (keep first char and domain)."""
    local, sep, domain = email.partition("@")
    if not sep:
        return "*" * len(email)
    return f"{local[:1]}{'*' * max(len(local) - 1, 2)}@{domain}"
