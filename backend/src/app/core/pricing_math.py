"""Pure pricing helpers: GST split and calendar pro-rate (Module 6).

Pro-rate formula (v1 technical default for open PRD Q15):
  amount_due_now = round(full_monthly_paise * remaining_days / days_in_month)

``remaining_days`` counts the start date through the last day of that calendar
month (inclusive). Full month (start on day 1) ⇒ full monthly amount.

Entitlements:
  - Exterior: count of society service weekdays from start through month end.
  - Interior: round(full_interior_freq * remaining_days / days_in_month).
"""

from __future__ import annotations

import calendar
from datetime import date


def days_in_month(year: int, month: int) -> int:
    return calendar.monthrange(year, month)[1]


def remaining_days_in_month(start: date) -> int:
    """Inclusive days from ``start`` through month end."""
    dim = days_in_month(start.year, start.month)
    return max(0, dim - start.day + 1)


def pro_rate_amount_paise(full_monthly_paise: int, start: date) -> int:
    dim = days_in_month(start.year, start.month)
    remaining = remaining_days_in_month(start)
    if dim <= 0 or remaining <= 0:
        return 0
    if remaining >= dim:
        return full_monthly_paise
    return int(round(full_monthly_paise * remaining / dim))


def pro_rate_interior_entitlement(full_frequency: int, start: date) -> int:
    if full_frequency <= 0:
        return 0
    dim = days_in_month(start.year, start.month)
    remaining = remaining_days_in_month(start)
    if dim <= 0 or remaining <= 0:
        return 0
    if remaining >= dim:
        return full_frequency
    return int(round(full_frequency * remaining / dim))


def count_service_days(
    start: date,
    *,
    service_weekdays: list[int],
    end: date | None = None,
) -> int:
    """Count occurrences of society service weekdays from start..end inclusive.

    ``service_weekdays`` uses 0=Monday … 5=Saturday (Python ``date.weekday()``).
    """
    if not service_weekdays:
        return 0
    if end is None:
        end = date(start.year, start.month, days_in_month(start.year, start.month))
    if end < start:
        return 0

    allowed = set(service_weekdays)
    count = 0
    # Iterate day by day; months are short enough for v1.
    day_count = (end - start).days + 1
    for offset in range(day_count):
        d = date.fromordinal(start.toordinal() + offset)
        if d.weekday() in allowed:
            count += 1
    return count


def split_gst_paise(
    amount_paise: int,
    *,
    include_gst: bool,
    gst_rate_bps: int,
) -> tuple[int, int, int]:
    """Return (taxable_base_paise, gst_paise, total_paise).

    If amounts already include GST, reverse-calculate the tax component.
    If exclusive, add GST on top of ``amount_paise``.
    """
    if amount_paise <= 0 or gst_rate_bps <= 0:
        return amount_paise, 0, amount_paise

    if include_gst:
        # total = base * (1 + r) ⇒ base = total * 10000 / (10000 + r)
        base = int(round(amount_paise * 10000 / (10000 + gst_rate_bps)))
        gst = amount_paise - base
        return base, gst, amount_paise

    gst = int(round(amount_paise * gst_rate_bps / 10000))
    return amount_paise, gst, amount_paise + gst
