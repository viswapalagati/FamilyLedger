"""assets tests — SKELETON (§20, row "Net worth" + isolation).

Implement each case, then drop the skipTest line.
"""

from django.test import TestCase


class NetWorthTests(TestCase):
    def test_family_net_worth(self):
        self.skipTest("TODO BR-11 — bank + physical + digital + receivable - liability")

    def test_member_net_worth_is_scoped_to_owner(self):
        self.skipTest("TODO BR-11 — per-member figure filters each term by owner")

    def test_inactive_assets_are_excluded(self):
        self.skipTest("TODO BR-11 — only is_active rows count")


class AssetScopingTests(TestCase):
    def test_asset_list_hides_other_families(self):
        self.skipTest("TODO BR-2 — list only shows the acting family's assets")

    def test_cross_family_object_is_404(self):
        self.skipTest("TODO BR-2 — editing another family's asset returns 404")
