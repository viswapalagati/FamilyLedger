"""dashboard tests — SKELETON (§20, rows "Aggregation" + scope isolation).

Implement each case, then drop the skipTest line.
"""

from django.test import TestCase


class AggregationTests(TestCase):
    def test_family_totals_equal_sum_of_member_totals(self):
        self.skipTest("TODO FR-12.8 / BR-12")

    def test_expense_by_head_sums_to_expense_total(self):
        self.skipTest("TODO §16.2")

    def test_savings_rate(self):
        self.skipTest("TODO BR-12 — net / income * 100, 0 when income is 0")

    def test_member_breakdown_sorted_by_spend(self):
        self.skipTest("TODO §16.2")


class ScopeIsolationTests(TestCase):
    def test_dashboard_only_sees_own_family(self):
        self.skipTest("TODO BR-2")

    def test_scope_to_foreign_member_falls_back_to_self(self):
        self.skipTest("TODO FR-11.3")
