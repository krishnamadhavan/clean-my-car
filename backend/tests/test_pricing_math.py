"""Unit tests for pricing math helpers."""

from __future__ import annotations

from datetime import date

from app.core.pricing_math import (
    count_service_days,
    days_in_month,
    pro_rate_amount_paise,
    pro_rate_interior_entitlement,
    remaining_days_in_month,
    split_gst_paise,
)


def test_remaining_and_full_month() -> None:
    assert days_in_month(2026, 8) == 31
    assert remaining_days_in_month(date(2026, 8, 1)) == 31
    assert remaining_days_in_month(date(2026, 8, 16)) == 16
    assert remaining_days_in_month(date(2026, 8, 31)) == 1


def test_pro_rate_amount() -> None:
    full = 3100_00  # 3100 rupees in paise
    assert pro_rate_amount_paise(full, date(2026, 8, 1)) == full
    # 16/31 of month
    assert pro_rate_amount_paise(full, date(2026, 8, 16)) == int(round(full * 16 / 31))


def test_pro_rate_interior() -> None:
    assert pro_rate_interior_entitlement(4, date(2026, 8, 1)) == 4
    assert pro_rate_interior_entitlement(0, date(2026, 8, 15)) == 0
    # mid-month scales down
    mid = pro_rate_interior_entitlement(4, date(2026, 8, 16))
    assert 0 <= mid <= 4


def test_count_service_days_mon_wed_fri() -> None:
    # Aug 2026: Sat=1 … Mon=3, Wed=5, Fri=7 …
    start = date(2026, 8, 3)  # Monday
    end = date(2026, 8, 9)  # Sunday
    # Mon 3, Wed 5, Fri 7 → 3
    assert count_service_days(start, service_weekdays=[0, 2, 4], end=end) == 3


def test_split_gst_inclusive() -> None:
    base, gst, total = split_gst_paise(11800, include_gst=True, gst_rate_bps=1800)
    assert total == 11800
    assert base + gst == total
    assert base == 10000
    assert gst == 1800


def test_split_gst_exclusive() -> None:
    base, gst, total = split_gst_paise(10000, include_gst=False, gst_rate_bps=1800)
    assert base == 10000
    assert gst == 1800
    assert total == 11800
