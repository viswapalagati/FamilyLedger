"""ledger forms — SKELETON. Implement per §15 (rows AccountHeadForm,
TransactionForm, RecurringTemplateForm) and §4.4 / §4.5 / §4.10.

All three narrow every ModelChoiceField queryset to ``self.family`` and
re-validate FKs server-side (BR-15). TransactionForm/RecurringTemplateForm set
``recorded_by`` = the acting member; ``member`` defaults to the acting member
but may be any active family member (on-behalf, §3 / BR-4). Head kind must equal
the entry type (BR-6).
"""
from core.forms import FamilyModelForm
from families.models import FamilyMember
from .models import (
    AccountHead,
    Budget,
    GoalContribution,
    RecurringTemplate,
    SavingsGoal,
    Transaction,
)  # noqa: F401
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from assets.models import BankAccount  # noqa: F401


class AccountHeadForm(FamilyModelForm):
    """name, kind, parent? (FR-4.1, FR-4.3). Set created_by on create (FR-4.7)."""

    class Meta:
        model = AccountHead
        fields = ["name", "kind", "parent"]  # TODO §12.4: ["name", "kind", "parent"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.family = self.family
        self.fields["parent"].required = False
        self.fields["parent"].queryset = AccountHead.objects.filter(
            family=self.family, is_archived=False
        ).exclude(pk=self.instance.pk or 0)

    def clean(self):
        cleaned = super().clean()
        parent, kind = cleaned.get("parent"), cleaned.get("kind")
        if parent and kind and parent.kind != kind:
            self.add_error("parent", "Parent head must be the same kind (income/expense).")
        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.family = self.family
        if not obj.pk and self.acting_member:
            obj.created_by = self.acting_member
        if commit:
            obj.save()
        return obj


class BudgetForm(FamilyModelForm):
    year = forms.IntegerField(min_value=2000, max_value=9999)

    class Meta:
        model = Budget
        fields = ["account_head", "amount", "year", "month"]
        widgets = {
            "year": forms.NumberInput(attrs={"min": 2000, "max": 9999}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.family = self.family
        self.fields["account_head"].queryset = AccountHead.objects.filter(
            family=self.family,
            kind="expense",
            is_archived=False,
        )
    def save(self, commit=True):
        budget = super().save(commit=False)
        budget.family = self.family
        if not budget.pk:
            budget.created_by = self.acting_member
        if commit:
            budget.save()
        return budget


class SavingsGoalForm(FamilyModelForm):
    class Meta:
        model = SavingsGoal
        fields = ["name", "description", "target_amount", "target_date"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "target_date": forms.DateInput(attrs={"type": "date"}),
        }

    def save(self, commit=True):
        goal = super().save(commit=False)
        goal.family = self.family
        if not goal.pk:
            goal.created_by = self.acting_member
        if commit:
            goal.save()
        return goal


class GoalContributionForm(forms.ModelForm):
    class Meta:
        model = GoalContribution
        fields = ["amount", "contributed_on", "note"]
        widgets = {
            "contributed_on": forms.DateInput(attrs={"type": "date"}),
        }


class TransactionForm(FamilyModelForm):
    """member, txn_type, account_head, amount, occurred_at (datetime-local),
    merchant_or_source, description, payment_method, bank_account?, attachment?
    (FR-5.1). See §15 for scoping/validation/save behaviour."""

    class Meta:
        model = Transaction
        fields = ["member", "txn_type", "account_head", "amount", "occurred_at",
            "merchant_or_source", "description", "payment_method",
            "bank_account", "attachment",]  # TODO §12.5 field list per §15
        widgets = {
            "occurred_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
            "description": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.family = self.family
        self.fields["occurred_at"].input_formats = ["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S"]

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.family = self.family
        obj.recorded_by = self.acting_member
        if commit:
            obj.save()
        return obj


class RecurringTemplateForm(FamilyModelForm):
    """member, txn_type, account_head, amount, merchant_or_source, description,
    payment_method, bank_account?, frequency, start_date, end_date? (FR-10.1).
    Set next_run_date = start_date when unset."""

    class Meta:
        model = RecurringTemplate
        fields = [
            "member", "txn_type", "account_head", "amount", "merchant_or_source",
            "description", "payment_method", "bank_account", "frequency",
            "start_date", "end_date",
        ]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 2}),
        }

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.family = self.family
        obj.recorded_by = self.acting_member
        if not obj.next_run_date:
            obj.next_run_date = obj.start_date
        if commit:
            obj.save()
        return obj

    