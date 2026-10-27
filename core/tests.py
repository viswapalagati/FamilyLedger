"""core tests — SKELETON (§20, row "Period resolver").

Fill in each case, then remove the skipTest call.
"""

from django.test import SimpleTestCase


class PeriodResolverTests(SimpleTestCase):
    def test_month_bounds_and_label(self):
        self.skipTest("TODO §16.1 — 1st..last day of month, label 'February 2026'")

    def test_quarter_bounds(self):
        self.skipTest("TODO §16.1 — calendar quarter containing the anchor")

    def test_calendar_year_bounds(self):
        self.skipTest("TODO §16.1 — Jan 1 .. Dec 31")

    def test_financial_year_april_before_and_after_start(self):
        self.skipTest("TODO BR-9 — anchor 2026-03-20 -> FY 2025-26; 2026-04-02 -> FY 2026-27")

    def test_financial_year_non_april_start(self):
        self.skipTest("TODO BR-9 — January-start FY equals the calendar year")

    def test_month_buckets_span_period(self):
        self.skipTest("TODO §16.1 — one bucket per month across a bounded period")
