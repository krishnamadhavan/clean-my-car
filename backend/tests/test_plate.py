"""Indian plate number validation tests."""

from __future__ import annotations

import pytest

from app.core.plate import normalize_indian_plate, plate_format_kind


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (None, None),
        ("", None),
        ("   ", None),
        # standard format
        ("ka 01 ab 1234", "KA01AB1234"),
        ("KA01AB1234", "KA01AB1234"),
        ("DL-3C-AB-1234", "DL3CAB1234"),
        ("MH12A1234", "MH12A1234"),
        ("TN10XX9999", "TN10XX9999"),
        # BH series
        ("26BH1234AB", "26BH1234AB"),
        ("26 bh 1234 ab", "26BH1234AB"),
        ("22-BH-9999-ZZ", "22BH9999ZZ"),
    ],
)
def test_normalize_valid_plates(raw: str | None, expected: str | None) -> None:
    assert normalize_indian_plate(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "1234",
        "INVALID",
        "KA01",  # too short
        "KA01AB12345",  # too many digits
        "K01AB1234",  # 1-letter state
        "KA011234",  # legacy without series — not accepted
        "MH121234",
        "KA01@B1234",
        "2BH1234AB",  # year must be 2 digits
        "26BH123AB",  # number must be 4 digits
        "26BH1234A",  # series must be 2 letters
    ],
)
def test_normalize_rejects_invalid(raw: str) -> None:
    with pytest.raises(ValueError, match="Invalid Indian vehicle plate"):
        normalize_indian_plate(raw)


def test_plate_format_kind() -> None:
    assert plate_format_kind("KA01AB1234") == "standard"
    assert plate_format_kind("26BH1234AB") == "bh"
