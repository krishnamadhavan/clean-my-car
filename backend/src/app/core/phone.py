"""Indian mobile number normalization and validation."""

from __future__ import annotations

import re

from fastapi import HTTPException, status

# 10-digit Indian mobile starting with 6-9
_INDIAN_MOBILE_BODY = re.compile(r"^[6-9]\d{9}$")


def normalize_indian_phone(raw: str) -> str:
    """Normalize to E.164 ``+91XXXXXXXXXX``.

    Accepts:
    - ``+9198XXXXXXXX``
    - ``9198XXXXXXXX``
    - ``098XXXXXXXX``
    - ``98XXXXXXXX``
    - digits with spaces/dashes
    """
    digits = re.sub(r"\D", "", raw or "")
    if not digits:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Phone number is required",
        )

    if digits.startswith("91") and len(digits) == 12:
        body = digits[2:]
    elif digits.startswith("0") and len(digits) == 11:
        body = digits[1:]
    elif len(digits) == 10:
        body = digits
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Invalid Indian mobile number",
        )

    if not _INDIAN_MOBILE_BODY.match(body):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Invalid Indian mobile number",
        )

    return f"+91{body}"
