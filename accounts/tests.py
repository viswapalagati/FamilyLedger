"""accounts tests — SKELETON (§20, row "Sign-up").

Implement each case, then drop the skipTest line.
"""

from django.test import TestCase


class SignupFlowTests(TestCase):
    def test_signup_creates_user_family_and_admin_member(self):
        self.skipTest("TODO FR-1.3 — User + Family + self/admin/has_login member; "
                      "added_by=self; Family.created_by set")

    def test_signup_rejects_mismatched_passwords(self):
        self.skipTest("TODO FR-1.2/FR-1.5 — nothing is created on error")

    def test_login_with_email_and_profile_edit(self):
        self.skipTest("TODO FR-3.1/FR-3.5 — login by email; profile edit syncs member")
