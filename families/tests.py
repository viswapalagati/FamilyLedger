"""families tests — SKELETON (§20, rows "Add member" and "Authorization").

Implement each case, then drop the skipTest line.
"""

from types import SimpleNamespace
from unittest.mock import Mock

from django.contrib.messages.storage.fallback import FallbackStorage
from django.template import Context, Template
from django.test import RequestFactory, SimpleTestCase, TestCase
from django.urls import reverse

from families.forms import AddMemberForm
from families.views import MemberCreateView


class AddMemberFormRenderingTests(SimpleTestCase):
    def test_login_fields_are_required_only_when_login_is_requested(self):
        member_data = {
            "full_name": "Taylor Smith",
            "relationship": "other",
            "email": "",
            "need_account_creation": "no",
            "password1": "",
            "password2": "",
        }
        without_login = AddMemberForm(data=member_data)
        self.assertTrue(without_login.is_valid(), without_login.errors)

        with_login = AddMemberForm(
            data={**member_data, "need_account_creation": "yes"}
        )
        self.assertFalse(with_login.is_valid())
        for field_name in ("email", "password1", "password2"):
            self.assertIn(field_name, with_login.errors)

    def test_template_fields_render_with_crispy(self):
        field_names = (
            "full_name",
            "relationship",
            "phone",
            "date_of_birth",
            "email",
            "need_account_creation",
            "password1",
            "password2",
        )
        fields = "".join(
            f'{{{{ form.{field_name}|as_crispy_field }}}}'
            for field_name in field_names
        )
        template = Template("{% load crispy_forms_tags %}" + fields)

        html = template.render(Context({"form": AddMemberForm()}))

        for field_name in field_names:
            self.assertIn(f'name="{field_name}"', html)


class MemberCreateViewTests(SimpleTestCase):
    def test_valid_form_redirects_to_created_member(self):
        request = RequestFactory().post("/families/members/add/")
        request.session = {}
        request._messages = FallbackStorage(request)
        member = SimpleNamespace(
            has_login=False,
            full_name="Taylor Smith",
            pk=42,
        )
        form = Mock()
        form.save.return_value = member
        view = MemberCreateView()
        view.request = request

        response = view.form_valid(form)

        self.assertRedirects(
            response,
            reverse("families:member_detail", kwargs={"pk": member.pk}),
            fetch_redirect_response=False,
        )


class AddMemberFlowTests(TestCase):
    def test_add_member_with_login_creates_user_and_sends_email(self):
        self.skipTest("TODO FR-2.2 / FR-13 — User created, email sent, no password in body, member can log in")

    def test_add_member_without_login(self):
        self.skipTest("TODO FR-2.3 — login-less member, no user, no email")

    def test_create_login_for_existing_member(self):
        self.skipTest("TODO FR-2.8 — login created and the member can then sign in")


class MemberAuthorizationTests(TestCase):
    def test_non_admin_cannot_manage_member(self):
        self.skipTest("TODO §6 — 403 on members/<pk>/manage/")

    def test_non_admin_cannot_open_family_settings(self):
        self.skipTest("TODO §6 — 403 on families/settings/")

    def test_admin_can_deactivate_member(self):
        self.skipTest("TODO FR-2.10 — status -> inactive")

    def test_inactive_member_is_locked_out(self):
        self.skipTest("TODO FR-2.11 — 403 for an inactive member")

    def test_cannot_view_other_family_member(self):
        self.skipTest("TODO BR-2 — 404 for a member of another family")
