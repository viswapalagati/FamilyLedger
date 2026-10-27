from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import TestCase


class UnlinkedSuperuserDashboardTests(TestCase):
    def test_unlinked_superuser_is_guided_to_admin(self):
        user = get_user_model().objects.create_superuser(
            email="admin@example.com",
            password="test-password",
        )
        self.client.force_login(user)

        response = self.client.get("/dashboard/")

        self.assertRedirects(response, "/admin/", fetch_redirect_response=False)
        queued_messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(queued_messages), 1)
        self.assertEqual(queued_messages[0].level, messages.WARNING)
        self.assertIn("active FamilyMember", str(queued_messages[0]))

    def test_unlinked_regular_user_is_still_forbidden(self):
        user = get_user_model().objects.create_user(
            email="user@example.com",
            password="test-password",
        )
        self.client.force_login(user)
        self.client.raise_request_exception = False

        response = self.client.get("/dashboard/")

        self.assertEqual(response.status_code, 403)
