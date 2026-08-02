"""Indian vehicle registration plate normalization and validation.

When a plate is provided it must match either:

- **Standard** (state RTO series): e.g. ``KA01AB1234``
- **Bharat (BH) series**: e.g. ``26BH1234AB``

``None`` / empty remains valid (plate is optional on the vehicle).
"""

from __future__ import annotations

import re

# Standard private format: SS + RTO (1–2 digits) + series (1–3 letters) + 4 digits
# Examples: KA01AB1234, DL3CAB1234, MH12A1234, TN10XX9999
_PLATE_STANDARD = re.compile(r"^[A-Z]{2}[0-9]{1,2}[A-Z]{1,3}[0-9]{4}$")

# Bharat series: YY + BH + 4 digits + 2 letters (e.g. 26BH1234AB)
_PLATE_BH = re.compile(r"^[0-9]{2}BH[0-9]{4}[A-Z]{2}$")


def normalize_indian_plate(raw: str | None) -> str | None:
    """Normalize plate text; return ``None`` if empty.

    Raises:
        ValueError: if non-empty and matches neither standard nor BH pattern.
    """
    if raw is None:
        return None
    cleaned = re.sub(r"[\s\-]+", "", raw).upper()
    if not cleaned:
        return None
    if not (_PLATE_STANDARD.fullmatch(cleaned) or _PLATE_BH.fullmatch(cleaned)):
        raise ValueError(
            "Invalid Indian vehicle plate. "
            "Use standard format (e.g. KA01AB1234) or BH series (e.g. 26BH1234AB)."
        )
    return cleaned


def plate_format_kind(normalized: str) -> str:
    """Return ``'standard'`` or ``'bh'`` for an already-validated normalized plate."""
    if _PLATE_STANDARD.fullmatch(normalized):
        return "standard"
    if _PLATE_BH.fullmatch(normalized):
        return "bh"
    raise ValueError("Plate is not a valid Indian registration number")
