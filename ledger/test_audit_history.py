import datetime as dt
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from families.models import Family, FamilyMember
from ledger.models import (
    AccountHead,
    AuditEvent,
    Budget,
    GoalContribution,
    SavingsGoal,
    Transaction,
    TxnType,
)


class AuditHistoryTests(TestCase):
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
        self.family = Family.objects.create(name="Audit test family")
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
        self.head = AccountHead.objects.create(
            family=self.family,
            name="Groceries",
            kind=TxnType.EXPENSE,
        )

    def test_budget_create_update_delete_are_retained_in_history(self):
        self.client.force_login(self.admin_user)
        next_month = timezone.localdate().month % 12 + 1
        year = timezone.localdate().year + (
            1 if next_month == 1 else 0
        )
        create_response = self.client.post(
            "/ledger/budgets/add/",
            {
                "account_head": self.head.pk,
                "year": year,
                "month": next_month,
                "amount": "500.00",
            },
        )
        self.assertEqual(create_response.status_code, 302)
        budget = Budget.objects.get(family=self.family)
        self.assertEqual(
            AuditEvent.objects.filter(
                entity_type=AuditEvent.EntityType.BUDGET,
                action=AuditEvent.Action.CREATED,
                entity_id=str(budget.pk),
            ).count(),
            1,
        )

        update_response = self.client.post(
            f"/ledger/budgets/{budget.pk}/edit/",
            {
                "account_head": self.head.pk,
                "year": year,
                "month": next_month,
                "amount": "750.00",
            },
        )
        self.assertEqual(update_response.status_code, 302)
        updated_event = AuditEvent.objects.get(
            entity_type=AuditEvent.EntityType.BUDGET,
            action=AuditEvent.Action.UPDATED,
            entity_id=str(budget.pk),
        )
        self.assertEqual(updated_event.changes["before"]["amount"], "500.00")
        self.assertEqual(updated_event.changes["after"]["amount"], "750.00")

        delete_response = self.client.post(
            f"/ledger/budgets/{budget.pk}/delete/",
            {},
        )
        self.assertEqual(delete_response.status_code, 302)
        self.assertFalse(Budget.objects.filter(pk=budget.pk).exists())
        deleted_event = AuditEvent.objects.get(
            entity_type=AuditEvent.EntityType.BUDGET,
            action=AuditEvent.Action.DELETED,
            entity_id=str(budget.pk),
        )
        self.assertEqual(deleted_event.changes["before"]["amount"], "750.00")

    def test_goal_create_update_delete_are_audited(self):
        self.client.force_login(self.admin_user)
        create_response = self.client.post(
            "/ledger/goals/add/",
            {
                "name": "Emergency fund",
                "description": "Long-term reserve",
                "target_amount": "1000.00",
                "target_date": "",
            },
        )
        self.assertEqual(create_response.status_code, 302)
        goal = SavingsGoal.objects.get(name="Emergency fund")

        update_response = self.client.post(
            f"/ledger/goals/{goal.pk}/edit/",
            {
                "name": "Emergency reserve",
                "description": "Long-term reserve",
                "target_amount": "1250.00",
                "target_date": "",
            },
        )
        self.assertEqual(update_response.status_code, 302)
        updated_event = AuditEvent.objects.get(
            entity_type=AuditEvent.EntityType.SAVINGS_GOAL,
            action=AuditEvent.Action.UPDATED,
            entity_id=str(goal.pk),
        )
        self.assertEqual(updated_event.changes["before"]["name"], "Emergency fund")
        self.assertEqual(updated_event.changes["after"]["name"], "Emergency reserve")

        delete_response = self.client.post(
            f"/ledger/goals/{goal.pk}/delete/",
            {},
        )
        self.assertEqual(delete_response.status_code, 302)
        self.assertFalse(SavingsGoal.objects.filter(pk=goal.pk).exists())
        self.assertTrue(
            AuditEvent.objects.filter(
                entity_type=AuditEvent.EntityType.SAVINGS_GOAL,
                action=AuditEvent.Action.DELETED,
                entity_id=str(goal.pk),
            ).exists()
        )

    def test_transaction_create_update_delete_are_audited(self):
        self.client.force_login(self.member_user)
        timestamp = timezone.localtime().strftime("%Y-%m-%dT%H:%M")
        response = self.client.post(
            "/ledger/entries/add/",
            {
                "member": self.member.pk,
                "txn_type": TxnType.EXPENSE,
                "account_head": self.head.pk,
                "amount": "25.00",
                "occurred_at": timestamp,
                "merchant_or_source": "Market",
                "description": "Food",
                "payment_method": "cash",
                "bank_account": "",
                "attachment": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        transaction = Transaction.objects.get(family=self.family)
        self.assertTrue(
            AuditEvent.objects.filter(
                entity_type=AuditEvent.EntityType.TRANSACTION,
                action=AuditEvent.Action.CREATED,
                entity_id=str(transaction.pk),
            ).exists()
        )

        response = self.client.post(
            f"/ledger/entries/{transaction.pk}/edit/",
            {
                "member": self.member.pk,
                "txn_type": TxnType.EXPENSE,
                "account_head": self.head.pk,
                "amount": "35.00",
                "occurred_at": timestamp,
                "merchant_or_source": "Market",
                "description": "Updated food",
                "payment_method": "cash",
                "bank_account": "",
                "attachment": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        updated_event = AuditEvent.objects.get(
            entity_type=AuditEvent.EntityType.TRANSACTION,
            action=AuditEvent.Action.UPDATED,
            entity_id=str(transaction.pk),
        )
        self.assertEqual(updated_event.changes["before"]["amount"], "25.00")
        self.assertEqual(updated_event.changes["after"]["amount"], "35.00")

        response = self.client.post(
            f"/ledger/entries/{transaction.pk}/delete/",
            {},
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Transaction.objects.filter(pk=transaction.pk).exists())
        self.assertTrue(
            AuditEvent.objects.filter(
                entity_type=AuditEvent.EntityType.TRANSACTION,
                action=AuditEvent.Action.DELETED,
                entity_id=str(transaction.pk),
            ).exists()
        )

    def test_audit_history_is_family_admin_only_and_family_scoped(self):
        event = AuditEvent.objects.create(
            family=self.family,
            actor=self.admin_member,
            actor_name=self.admin_member.full_name,
            actor_email=self.admin_user.email,
            action=AuditEvent.Action.CREATED,
            entity_type=AuditEvent.EntityType.SAVINGS_GOAL,
            entity_id="17",
            summary="Created savings goal",
            changes={"after": {"name": "Emergency fund"}},
        )
        other_family = Family.objects.create(name="Other family")
        other_event = AuditEvent.objects.create(
            family=other_family,
            actor_name="Other Admin",
            actor_email="other@example.com",
            action=AuditEvent.Action.CREATED,
            entity_type=AuditEvent.EntityType.SAVINGS_GOAL,
            entity_id="22",
            summary="Other family's goal",
            changes={},
        )

        self.client.force_login(self.member_user)
        self.client.raise_request_exception = False
        response = self.client.get("/ledger/audit/")
        self.assertEqual(response.status_code, 403)

        self.client.force_login(self.admin_user)
        response = self.client.get("/ledger/audit/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, event.summary)
        self.assertNotContains(response, other_event.summary)

    def test_contribution_creation_is_audited_with_actor(self):
        goal = SavingsGoal.objects.create(
            family=self.family,
            name="Holiday",
            target_amount=Decimal("500.00"),
            created_by=self.admin_member,
        )
        self.client.force_login(self.member_user)

        response = self.client.post(
            f"/ledger/goals/{goal.pk}/contribute/",
            {
                "amount": "50.00",
                "contributed_on": dt.date.today().isoformat(),
                "note": "First deposit",
            },
        )

        self.assertEqual(response.status_code, 302)
        contribution = GoalContribution.objects.get(goal=goal)
        event = AuditEvent.objects.get(
            entity_type=AuditEvent.EntityType.GOAL_CONTRIBUTION,
            entity_id=str(contribution.pk),
        )
        self.assertEqual(event.actor, self.member)
        self.assertEqual(event.changes["after"]["amount"], "50.00")
