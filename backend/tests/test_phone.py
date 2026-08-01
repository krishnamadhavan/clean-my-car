"""Unit tests for phone normalization."""

import pytest
from app.core.phone import normalize_indian_phone
from fastapi import HTTPException


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("9876543210", "+919876543210"),
        ("+91 98765 43210", "+919876543210"),
        ("919876543210", "+919876543210"),
        ("09876543210", "+919876543210"),
    ],
)
def test_normalize_valid(raw: str, expected: str) -> None:
    assert normalize_indian_phone(raw) == expected


@pytest.mark.parametrize("raw", ["", "123", "5123456789", "987654321"])
def test_normalize_invalid(raw: str) -> None:
    with pytest.raises(HTTPException):
        normalize_indian_phone(raw)
