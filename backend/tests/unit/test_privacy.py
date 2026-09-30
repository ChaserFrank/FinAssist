"""Masking helpers used to keep personal data out of unauthenticated responses."""

import pytest

from app.core.privacy import mask_email, mask_phone


@pytest.mark.parametrize(
    ("phone", "expected"),
    [
        ("+254700000021", "+254*******21"),
        ("+254700000001", "+254*******01"),
        ("12345", "*****"),  # too short to reveal anything
    ],
)
def test_mask_phone(phone: str, expected: str) -> None:
    assert mask_phone(phone) == expected


@pytest.mark.parametrize(
    ("email", "expected"),
    [
        ("bob@example.com", "b**@example.com"),
        ("alice.kamau@example.com", "a**********@example.com"),
        ("a@example.com", "a**@example.com"),  # never reveals length of very short names
        ("not-an-email", "************"),
    ],
)
def test_mask_email(email: str, expected: str) -> None:
    assert mask_email(email) == expected


def test_masked_values_never_contain_original_local_part() -> None:
    assert "obby" not in mask_email("bobby@example.com")
    assert "0000" not in mask_phone("+254700000021")
