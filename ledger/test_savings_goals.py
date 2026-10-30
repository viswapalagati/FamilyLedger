from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from families.models import Family, FamilyMember
from ledger.models import GoalContribution, SavingsGoal, Transaction
from ledger.savings import savings_goal_statuses


class SavingsGoalFeatureTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin_user = user_model.objects.create_user(
            email="admin@example.com",
            password="test-password",
        )
        self.member_user = user_model.objects.create_user(
            email="member@example.com",
            password="test-password",
        )
        self.family = Family.objects.create(name="Test family")
        self.admin_member = FamilyMember.objects.create(
            family=self.family,
            user=self.admin_user,
            full_name="Family Admin",
            relationship=FamilyMember.Relationship.SELF,
            is_family_admin=True,
        )
        self.member = FamilyMember.objects.create(
            family=self.family,
            user=self.member_user,
            full_name="Family Member",
        )
        self.goal = SavingsGoal.objects.create(
            family=self.family,
            name="Emergency fund",
            target_amount=Decimal("1000.00"),
            created_by=self.admin_member,
        )

    def test_admin_can_create_goal(self):
        self.client.force_login(self.admin_user)

        response = self.client.post(
            "/ledger/goals/add/",
            {
                "name": "Family holiday",
                "description": "Trip savings",
                "target_amount": "2500.00",
                "target_date": "",
            },
        )

        self.assertRedirects(
            response,
            "/ledger/goals/",
            fetch_redirect_response=False,
        )
        goal = SavingsGoal.objects.get(name="Family holiday")
        self.assertEqual(goal.family, self.family)
        self.assertEqual(goal.created_by, self.admin_member)

    def test_non_admin_cannot_manage_goals(self):
        self.client.force_login(self.member_user)
        self.client.raise_request_exception = False

        response = self.client.get("/ledger/goals/add/")

        self.assertEqual(response.status_code, 403)

    def test_member_contribution_updates_goal_without_ledger_transaction(self):
        self.client.force_login(self.member_user)

        response = self.client.post(
            f"/ledger/goals/{self.goal.pk}/contribute/",
            {
                "amount": "250.00",
                "contributed_on": "2026-10-28",
                "note": "Monthly saving",
            },
        )

        self.assertRedirects(
            response,
            "/ledger/goals/",
            fetch_redirect_response=False,
        )
        contribution = GoalContribution.objects.get(goal=self.goal)
        self.assertEqual(contribution.family, self.family)
        self.assertEqual(contribution.member, self.member)
        self.assertEqual(Transaction.objects.count(), 0)
        status = savings_goal_statuses(self.family)[0]
        self.assertEqual(status["saved"], Decimal("250.00"))
        self.assertEqual(status["remaining"], Decimal("750.00"))
        self.assertFalse(status["is_complete"])

    def test_contributions_can_reach_goal_and_progress_is_capped(self):
        GoalContribution.objects.create(
            goal=self.goal,
            family=self.family,
            member=self.member,
            amount=Decimal("1200.00"),
        )

        status = savings_goal_statuses(self.family)[0]

        self.assertTrue(status["is_complete"])
        self.assertEqual(status["remaining"], Decimal("0"))
        self.assertEqual(status["progress_percent"], Decimal("100"))

    def test_member_cannot_contribute_to_another_family_goal(self):
        other_family = Family.objects.create(name="Other family")
        other_goal = SavingsGoal.objects.create(
            family=other_family,
            name="Other goal",
            target_amount=Decimal("500.00"),
        )
        self.client.force_login(self.member_user)
        self.client.raise_request_exception = False

        response = self.client.get(
            f"/ledger/goals/{other_goal.pk}/contribute/"
        )

        self.assertEqual(response.status_code, 404)

    def test_goal_list_shows_progress_and_member_contribution(self):
        GoalContribution.objects.create(
            goal=self.goal,
            family=self.family,
            member=self.member,
            amount=Decimal("400.00"),
        )
        self.client.force_login(self.member_user)

        response = self.client.get("/ledger/goals/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Emergency fund")
        self.assertContains(response, "Family Member")
        self.assertEqual(
            response.context["savings_goal_statuses"][0]["saved"],
            Decimal("400.00"),
        )

    def test_non_admin_cannot_delete_goal(self):
        self.client.force_login(self.member_user)
        self.client.raise_request_exception = False

        response = self.client.post(
            f"/ledger/goals/{self.goal.pk}/delete/",
            {},
        )

        self.assertEqual(response.status_code, 403)
        self.assertTrue(SavingsGoal.objects.filter(pk=self.goal.pk).exists())
