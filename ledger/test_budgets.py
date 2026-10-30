import datetime as dt
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from families.models import Family, FamilyMember
from ledger.budgets import budget_statuses
from ledger.forms import BudgetForm
from ledger.models import AccountHead, Budget, Transaction, TxnType


class BudgetFeatureTests(TestCase):
    def setUp(self):
        today = timezone.localdate()
        self.year = today.year
        self.month = today.month
        user = get_user_model().objects.create_user(
            email="admin@example.com",
            password="test-password",
        )
        self.family = Family.objects.create(name="Test family")
        self.member = FamilyMember.objects.create(
            family=self.family,
            user=user,
            full_name="Family Admin",
            relationship=FamilyMember.Relationship.SELF,
            is_family_admin=True,
        )
        self.head = AccountHead.objects.create(
            family=self.family,
            name="Groceries",
            kind=TxnType.EXPENSE,
        )
        self.budget = Budget.objects.create(
            family=self.family,
            account_head=self.head,
            year=self.year,
            month=self.month,
            amount=Decimal("1000.00"),
            created_by=self.member,
        )
        self.client.force_login(user)

    def add_transaction(self, amount, txn_type=TxnType.EXPENSE):
        head = self.head
        if txn_type == TxnType.INCOME:
            head = AccountHead.objects.create(
                family=self.family,
                name="Salary",
                kind=TxnType.INCOME,
            )
        occurred_at = timezone.make_aware(
            dt.datetime(self.year, self.month, 15, 12)
        )
        return Transaction.objects.create(
            family=self.family,
            member=self.member,
            recorded_by=self.member,
            txn_type=txn_type,
            account_head=head,
            amount=Decimal(amount),
            occurred_at=occurred_at,
        )

    def test_alert_thresholds_and_income_exclusion(self):
        self.add_transaction("790.00")
        self.add_transaction("5000.00", txn_type=TxnType.INCOME)
        statuses = budget_statuses(self.family, self.year, self.month)
        self.assertEqual(statuses[0]["spent"], Decimal("790.00"))
        self.assertIsNone(statuses[0]["alert"])

        self.add_transaction("10.00")
        self.assertEqual(
            budget_statuses(self.family, self.year, self.month)[0]["alert"],
            "warning",
        )

        self.add_transaction("200.00")
        self.assertEqual(
            budget_statuses(self.family, self.year, self.month)[0]["alert"],
            "exceeded",
        )

    def test_budget_page_shows_month_spending_and_alert(self):
        self.add_transaction("850.00")

        response = self.client.get(
            f"/ledger/budgets/?month={self.year:04d}-{self.month:02d}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["budget_statuses"][0]["spent"], Decimal("850.00"))
        self.assertEqual(response.context["budget_alerts"][0]["alert"], "warning")

    def test_dashboard_shows_current_month_budget_alert(self):
        self.add_transaction("850.00")

        response = self.client.get("/dashboard/?scope=family")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["budget_alerts"][0]["alert"], "warning")

    def test_budget_can_only_be_created_by_family_admin(self):
        next_month = (
            dt.date(self.year, self.month, 28) + dt.timedelta(days=4)
        ).replace(day=1)
        response = self.client.post(
            "/ledger/budgets/add/",
            {
                "account_head": self.head.pk,
                "amount": "500.00",
                "year": next_month.year,
                "month": next_month.month,
            },
        )
        self.assertRedirects(
            response,
            f"/ledger/budgets/?month={next_month.year:04d}-{next_month.month:02d}",
            fetch_redirect_response=False,
        )
        self.assertEqual(Budget.objects.filter(family=self.family).count(), 2)

        self.member.is_family_admin = False
        self.member.save(update_fields=["is_family_admin"])
        self.client.raise_request_exception = False
        response = self.client.post(
            "/ledger/budgets/add/",
            {
                "account_head": self.head.pk,
                "amount": "300.00",
                "year": next_month.year,
                "month": next_month.month,
            },
        )
        self.assertEqual(response.status_code, 403)

    def test_budget_month_query_must_be_valid(self):
        response = self.client.get("/ledger/budgets/?month=not-a-month")
        self.assertEqual(response.status_code, 404)

    def test_budget_form_only_accepts_expense_categories_from_this_family(self):
        income_head = AccountHead.objects.create(
            family=self.family,
            name="Salary",
            kind=TxnType.INCOME,
        )
        form = BudgetForm(
            data={
                "account_head": income_head.pk,
                "amount": "500.00",
                "year": self.year,
                "month": self.month,
            },
            family=self.family,
            acting_member=self.member,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("account_head", form.errors)

    def test_other_family_spending_is_not_included(self):
        other_family = Family.objects.create(name="Other family")
        other_user = get_user_model().objects.create_user(
            email="other@example.com",
            password="test-password",
        )
        other_member = FamilyMember.objects.create(
            family=other_family,
            user=other_user,
            full_name="Other member",
        )
        other_head = AccountHead.objects.create(
            family=other_family,
            name="Groceries",
            kind=TxnType.EXPENSE,
        )
        Transaction.objects.create(
            family=other_family,
            member=other_member,
            recorded_by=other_member,
            txn_type=TxnType.EXPENSE,
            account_head=other_head,
            amount=Decimal("950.00"),
            occurred_at=timezone.make_aware(
                dt.datetime(self.year, self.month, 15, 12)
            ),
        )

        statuses = budget_statuses(self.family, self.year, self.month)

        self.assertEqual(statuses[0]["spent"], Decimal("0"))
        self.assertIsNone(statuses[0]["alert"])
