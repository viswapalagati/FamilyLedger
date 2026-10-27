"""ledger tests — SKELETON (§20, rows "Attribution", "Validation", "Account heads").

Implement each case, then drop the skipTest line.
"""

from django.template.loader import get_template
from django.test import SimpleTestCase, TestCase

from ledger.views import EntryUpdateView


class EntryUpdateViewTests(SimpleTestCase):
    def test_edit_view_uses_existing_entry_form_template(self):
        template_name = EntryUpdateView().get_template_names()[0]

        self.assertEqual(template_name, "ledger/entry_form.html")
        self.assertIsNotNone(get_template(template_name))

class AttributionTests(TestCase):
    def test_my_income_is_by_member_not_recorder(self):
        self.skipTest("TODO BR-1 — per-member figures filter on member, not recorded_by")

    def test_on_behalf_entry_via_view_sets_recorded_by_to_actor(self):
        self.skipTest("TODO §3 — member = chosen person, recorded_by = acting user")

    def test_account_head_kind_must_match_txn_type(self):
        self.skipTest("TODO BR-6 — full_clean() rejects a mismatched head")

    def test_cross_family_member_rejected_on_clean(self):
        self.skipTest("TODO BR-15 — a member of another family is rejected")


class AccountHeadTests(TestCase):
    def test_created_head_is_family_scoped_and_stamped(self):
        self.skipTest("TODO FR-4.2 / FR-4.7 — family set, created_by set")

    def test_head_in_use_is_archived_not_deleted(self):
        self.skipTest("TODO FR-4.6 — archive when transactions reference it")

    def test_unused_head_is_deleted(self):
        self.skipTest("TODO FR-4.6 — delete when unused")

    def test_duplicate_top_level_head_name_blocked(self):
        self.skipTest("TODO BR-7 — full_clean() rejects a duplicate top-level name")
