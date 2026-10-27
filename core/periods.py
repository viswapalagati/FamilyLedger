"""Reporting-period resolution — SKELETON.

Implement per §16.1 (resolver table + worked examples), §4.11 (FR-11.*),
BR-9 (financial year) and BR-10 (period bounds).

The report views expect ``resolve_period()`` to return an object exposing
``period_type``, ``start``, ``end`` (inclusive; ``None`` for all-time),
``label`` and an ``is_bounded`` flag.
"""

from __future__ import annotations

import datetime as dt  # noqa: F401
from dataclasses import dataclass
import calendar

MONTH = "month"
QUARTER = "quarter"
CALENDAR_YEAR = "calendar_year"
FINANCIAL_YEAR = "financial_year"
ALL_TIME = "all_time"

PERIOD_CHOICES = [
    (MONTH, "Month"),
    (QUARTER, "Quarter"),
    (CALENDAR_YEAR, "Calendar year"),
    (FINANCIAL_YEAR, "Financial year"),
    (ALL_TIME, "All-time"),
]

VALID_PERIODS = {key for key, _ in PERIOD_CHOICES}


@dataclass(frozen=True)
class Period:
    period_type: str
    start: dt.date | None
    end: dt.date | None
    label: str

    @property
    def is_bounded(self) -> bool:
        return self.start is not None and self.end is not None

def _last_day(year: int, month: int) -> int:
    return calendar.monthrange(year, month)[1]

def _add_months(year: int, month: int, months: int) -> tuple[int, int]:
    index = (year * 12 + (month - 1)) + months
    return index // 12, index % 12 + 1

def _fy_label(start_year: int) -> str:
    return f"FY {start_year}-{str(start_year + 1)[-2:]}"

def resolve_period(
    period_type: str,
    anchor: dt.date | None = None,
    fy_start_month: int = 4,
) -> Period:
    """Return the :class:`Period` for ``period_type`` around ``anchor``."""

    anchor = anchor or dt.date.today()
    if period_type not in VALID_PERIODS:
        period_type = MONTH

    if period_type == MONTH:
        start = anchor.replace(day=1)
        end = anchor.replace(day=_last_day(anchor.year, anchor.month))
        return Period(period_type, start, end, start.strftime("%B %Y"))

    if period_type == QUARTER:
        q = (anchor.month - 1) // 3
        start_month = q * 3 + 1
        start = dt.date(anchor.year, start_month, 1)
        end_year, end_month = _add_months(anchor.year, start_month, 2)
        end = dt.date(end_year, end_month, _last_day(end_year, end_month))
        return Period(period_type, start, end, f"Q{q + 1} {anchor.year}")

    if period_type == CALENDAR_YEAR:
        start = dt.date(anchor.year, 1, 1)
        end = dt.date(anchor.year, 12, 31)
        return Period(period_type, start, end, str(anchor.year))

    if period_type == FINANCIAL_YEAR:
        fy_start_month = fy_start_month or 4
        start_year = anchor.year if anchor.month >= fy_start_month else anchor.year - 1
        start = dt.date(start_year, fy_start_month, 1)
        end_year, end_month = _add_months(start_year, fy_start_month, 12)
        # end is the day before the next FY starts
        end = dt.date(end_year, end_month, 1) - dt.timedelta(days=1)
        return Period(period_type, start, end, _fy_label(start_year))

    return Period(ALL_TIME, None, None, "All-time")
    
    


def parse_anchor(value):
    """Parse an ISO date string; fall back to today on error (§16.1)."""
    raise NotImplementedError("Implement parse_anchor per §16.1")



def month_buckets(period: Period)-> list[tuple[dt.date, dt.date, str]]:
    """Split a bounded period into month-sized buckets for the trend chart (§16.1)."""
    """Split a bounded period into month-sized buckets for bar/line charts.

    For an unbounded (all-time) period the caller should fall back to a
    per-year grouping; this helper only handles bounded periods.
    """

    if not period.is_bounded:
        return [] 
    buckets: list[tuple[dt.date, dt.date, str]] = []
    year, month = period.start.year, period.start.month
    while dt.date(year, month, 1) <= period.end:
        b_start = dt.date(year, month, 1)
        b_end = dt.date(year, month, _last_day(year, month))
        if b_end > period.end:
            b_end = period.end
        buckets.append((b_start, b_end, b_start.strftime("%b %Y")))
        year, month = _add_months(year, month, 1)
    return buckets