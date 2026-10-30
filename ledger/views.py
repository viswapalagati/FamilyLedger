"""ledger views — SKELETON. Implement per §4.4, §4.5, §4.10, §6, §14.2, §15.

Routes (ledger/urls.py, already wired):
  heads/               HeadListView            heads/add/           HeadCreateView
  heads/<pk>/edit/     HeadUpdateView          heads/<pk>/archive/  HeadArchiveView (POST)
  income/              IncomeListView          expenses/            ExpenseListView
  entries/add/         EntryCreateView         entries/<pk>/edit/   EntryUpdateView
  entries/<pk>/delete/ EntryDeleteView
  recurring/           RecurringListView       recurring/add/       RecurringCreateView
  recurring/<pk>/edit/ RecurringUpdateView     recurring/<pk>/delete/ RecurringDeleteView
"""

import datetime as dt

from django.views.generic import (
    CreateView,
    DeleteView,
    ListView,
    TemplateView,
    UpdateView,
    View,
)

from core.mixins import (  # noqa: F401
    FamilyAdminRequiredMixin,
    FamilyFormKwargsMixin,
    FamilyRequiredMixin,
    FamilyScopedQuerysetMixin,
    RecordEditPermissionMixin,
    ScopePeriodMixin,
)

from django.db import models, transaction as db_transaction
from ledger.models import Transaction, TxnType, AccountHead  # noqa: F401
from .forms import TransactionForm, AccountHeadForm # noqa: F401
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.db.models import Count
from django.urls import reverse, reverse_lazy
from django.db.models import Sum
from .models import Budget, GoalContribution, RecurringTemplate, SavingsGoal
from .forms import (
    BudgetForm,
    GoalContributionForm,
    RecurringTemplateForm,
    SavingsGoalForm,
)
from .budgets import budget_statuses
from .savings import savings_goal_statuses
from .audit import audit_snapshot, record_audit_event
from .models import AuditEvent
from django.http import Http404


class AuditUpdateMixin:
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self._audit_before = audit_snapshot(self.object)
        return super().post(request, *args, **kwargs)


# --- Account heads (FR-4.*) ------------------------------------------------ #
class HeadListView(FamilyRequiredMixin, FamilyScopedQuerysetMixin, ListView):
    """Grouped by kind, with txn counts (FR-4.5). Template: ledger/head_list.html.
    Context keys the template expects: ``income_heads``, ``expense_heads``."""
    template_name = "ledger/head_list.html" 
    model = AccountHead 
    form_class = AccountHeadForm

    def get_queryset(self):
        return super().get_queryset().select_related("parent", "created_by")


    def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs) 
            heads = list(self.get_queryset())
            context["income_heads"] = [h for h in heads if h.kind == TxnType.INCOME]
            context["expense_heads"] = [h for h in heads if h.kind == TxnType.EXPENSE]
            return context



class HeadCreateView(FamilyRequiredMixin, FamilyFormKwargsMixin, CreateView):
    """Template: core/object_form.html. Set created_by (FR-4.7)."""  
    template_name = "core/object_form.html"
    model = AccountHead
    form_class = AccountHeadForm
    success_url = reverse_lazy("ledger:head_list")


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_title"] = "New account head"
        context["form_help"] = "Categories are shared across the whole family."
        context["submit_label"] = "Create head"
        context["cancel_url"] = self.success_url
        return context

    def form_valid(self, form):
        messages.success(self.request, "Account head created.")
        return super().form_valid(form)


class HeadUpdateView(FamilyRequiredMixin, FamilyScopedQuerysetMixin,
                     FamilyFormKwargsMixin, UpdateView):
    """Template: core/object_form.html."""
    template_name = "core/object_form.html"
    model = AccountHead
    form_class = AccountHeadForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_title"] = f"Edit {self.object.name}"
        context["submit_label"] = "Save head"
        context["cancel_url"] = self.success_url
        return context


    def get_success_url(self):
        return reverse_lazy("ledger:head_list")


class HeadArchiveView(FamilyRequiredMixin, FamilyScopedQuerysetMixin, View):
    """POST only (FR-4.6): delete if unused, else toggle is_archived."""

    # TODO: implement post()
    def post(self, request, *args, **kwargs):
        head = get_object_or_404(AccountHead, pk=kwargs["pk"], family=self.family)
        if head.transactions.exists():
            head.is_archived = not head.is_archived
            head.save(update_fields=["is_archived", "updated_at"])
            state = "archived" if head.is_archived else "restored"
            messages.info(request, f"“{head.name}” {state} (it has transactions).")
        else:
            head.delete()
            messages.success(request, "Account head deleted.")
        return redirect("ledger:head_list")


# --- Transactions (FR-5.*) ---------------------------------------------- #
class _TransactionListView(ScopePeriodMixin, ListView):
    """Shared base for the income/expense lists (FR-5.8). Template:
    ledger/transaction_list.html. Filters: scope, period, head, merchant, method;
    paginate 40; expose period total + count. Set ``txn_type`` on the subclass."""

    template_name = "ledger/transaction_list.html"
    context_object_name = "transactions"
    paginate_by = 40
    txn_type = TxnType.EXPENSE  # override in subclass
    # TODO: get_queryset(), get_context_data() (see §14.2 for the context keys the
    #       template reads: total, count, txn_type, is_income, heads,
    #       selected_head, merchant_q, selected_method, method_choices, filter_ctx)

    def get_queryset(self):
        qs = self.scope_transactions(
            Transaction.objects.filter(txn_type=self.txn_type)
        ).select_related("member", "recorded_by", "account_head", "bank_account")

        head = self.request.GET.get("head")
        merchant = self.request.GET.get("merchant")
        method = self.request.GET.get("method")
        if head:
            qs = qs.filter(account_head_id=head)
        if merchant:
            qs = qs.filter(merchant_or_source__icontains=merchant)
        if method:
            qs = qs.filter(payment_method=method)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = self.get_queryset()
        context["total"] = qs.aggregate(v=Sum("amount"))["v"] or 0
        context["count"] = qs.count()
        context["txn_type"] = self.txn_type
        context["is_income"] = self.txn_type == TxnType.INCOME
        context["heads"] = AccountHead.objects.filter(
            family=self.family, kind=self.txn_type
        )
        context["selected_head"] = self.request.GET.get("head", "")
        context["merchant_q"] = self.request.GET.get("merchant", "")
        context["selected_method"] = self.request.GET.get("method", "")
        context["method_choices"] = Transaction._meta.get_field("payment_method").choices
        extra = []
        for key in ("head", "merchant", "method"):
            if self.request.GET.get(key):
                extra.append((key, self.request.GET[key]))
        context["filter_ctx"] = self.get_filter_ctx(extra=extra)
        return context



class IncomeListView(_TransactionListView):
    txn_type = TxnType.INCOME


class ExpenseListView(_TransactionListView):
    txn_type = TxnType.EXPENSE


class EntryCreateView(FamilyRequiredMixin, FamilyFormKwargsMixin, CreateView):
    """Add an entry (FR-5.1). Template: ledger/entry_form.html.
    Support ?member= and ?type= prefill (FR-5.7). recorded_by = acting member."""
    template_name = "ledger/entry_form.html"
    model = Transaction
    form_class = TransactionForm
    
    def get_initial(self):
        initial = super().get_initial()
        initial["occurred_at"] = timezone.localtime().strftime("%Y-%m-%dT%H:%M")
        if self.request.GET.get("type") in (TxnType.INCOME, TxnType.EXPENSE):
            initial["txn_type"] = self.request.GET["type"]
        member_pk = self.request.GET.get("member")
        if member_pk and self.family.members.filter(pk=member_pk).exists():
            initial["member"] = member_pk
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_title"] = "Add an entry"
        return context

    @db_transaction.atomic
    def form_valid(self, form):
        obj = form.save()
        self.object = obj
        record_audit_event(
            family=self.family,
            actor=self.acting_member,
            action=AuditEvent.Action.CREATED,
            entity_type=AuditEvent.EntityType.TRANSACTION,
            instance=obj,
        )
        messages.success(
            self.request,
            f"{obj.get_txn_type_display()} of ₹{obj.amount} recorded for {obj.member.full_name}.",
        )
        self.object = obj
        target = "ledger:income_list" if obj.txn_type == TxnType.INCOME else "ledger:expense_list"
        return redirect(target)
    

    


class EntryUpdateView(FamilyRequiredMixin, FamilyScopedQuerysetMixin,
                      FamilyFormKwargsMixin, RecordEditPermissionMixin,
                      AuditUpdateMixin, UpdateView):
    """Edit an entry (FR-5.9). Template: ledger/entry_form.html."""
    template_name = "ledger/entry_form.html"
    model = Transaction
    form_class = TransactionForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_title"] = "Edit entry"
        return context

    @db_transaction.atomic
    def form_valid(self, form):
        response = super().form_valid(form)
        record_audit_event(
            family=self.family,
            actor=self.acting_member,
            action=AuditEvent.Action.UPDATED,
            entity_type=AuditEvent.EntityType.TRANSACTION,
            instance=self.object,
            before=self._audit_before,
        )
        return response

    def get_success_url(self):
        messages.success(self.request, "Entry updated.")
        if self.object.txn_type == TxnType.INCOME:
            return reverse("ledger:income_list")
        return reverse("ledger:expense_list")
         


class EntryDeleteView(FamilyRequiredMixin, FamilyScopedQuerysetMixin,
                      RecordEditPermissionMixin, DeleteView):
    """Delete an entry (FR-5.9). Template: core/object_confirm_delete.html."""
    template_name = "core/object_confirm_delete.html"
    model = Transaction

    @db_transaction.atomic
    def form_valid(self, form):
        before = audit_snapshot(self.object)
        record_audit_event(
            family=self.family,
            actor=self.acting_member,
            action=AuditEvent.Action.DELETED,
            entity_type=AuditEvent.EntityType.TRANSACTION,
            instance=self.object,
            before=before,
        )
        return super().form_valid(form)

    def get_success_url(self):
        if self.object.txn_type == TxnType.INCOME:
            return reverse("ledger:income_list")

        return reverse("ledger:expense_list")


# --- Recurring templates (FR-10.*) ---------------------------------- #
class RecurringListView(FamilyRequiredMixin, FamilyScopedQuerysetMixin, ListView):
    """Template: ledger/recurring_list.html. context_object_name = 'templates'."""
    
    model = RecurringTemplate
    template_name = "ledger/recurring_list.html"
    context_object_name = "templates"
    def get_queryset(self):
        return super().get_queryset().select_related("member", "account_head")


class RecurringCreateView(FamilyRequiredMixin, FamilyFormKwargsMixin, CreateView):
    """Template: core/object_form.html."""
    model = RecurringTemplate
    form_class = RecurringTemplateForm
    template_name = "core/object_form.html"
    success_url = reverse_lazy("ledger:recurring_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_title"] = "New recurring entry"
        context["form_help"] = (
            "FamilyLedger will create a transaction on each due date when "
            "'generate_recurring' runs."
        )
        context["submit_label"] = "Create schedule"
        context["cancel_url"] = self.success_url
        return context


class RecurringUpdateView(FamilyRequiredMixin, FamilyScopedQuerysetMixin,
                          FamilyFormKwargsMixin, RecordEditPermissionMixin, UpdateView):
    """Template: core/object_form.html."""
    model = RecurringTemplate
    form_class = RecurringTemplateForm
    template_name = "core/object_form.html"
    success_url = reverse_lazy("ledger:recurring_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_title"] = "Edit recurring entry"
        context["submit_label"] = "Save schedule"
        context["cancel_url"] = self.success_url
        return context


class RecurringDeleteView(FamilyRequiredMixin, FamilyScopedQuerysetMixin,
                          RecordEditPermissionMixin, DeleteView):
    """Template: core/object_confirm_delete.html."""
    model = RecurringTemplate
    template_name = "core/object_confirm_delete.html"
    success_url = reverse_lazy("ledger:recurring_list")

    def get_success_url(self):
        messages.success(self.request, "Recurring entry removed.")
        return super().get_success_url()


class BudgetListView(FamilyRequiredMixin, TemplateView):
    template_name = "ledger/budget_list.html"

    def get_month(self):
        value = self.request.GET.get("month")
        if not value:
            today = timezone.localdate()
            return today.year, today.month
        try:
            month = dt.datetime.strptime(value, "%Y-%m")
        except ValueError as exc:
            raise Http404("Use YYYY-MM for the budget month.") from exc
        if month.strftime("%Y-%m") != value:
            raise Http404("Use YYYY-MM for the budget month.")
        return month.year, month.month

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year, month = self.get_month()
        statuses = budget_statuses(self.family, year, month)
        month_date = dt.date(year, month, 1)
        previous = month_date.replace(day=1) - dt.timedelta(days=1)
        next_month = (
            month_date.replace(day=28) + dt.timedelta(days=4)
        ).replace(day=1)
        context.update(
            {
                "budget_statuses": statuses,
                "budget_alerts": [item for item in statuses if item["alert"]],
                "budget_month": month_date,
                "previous_month": previous.strftime("%Y-%m"),
                "next_month": next_month.strftime("%Y-%m"),
            }
        )
        return context


class BudgetCreateView(FamilyAdminRequiredMixin, FamilyFormKwargsMixin, CreateView):
    model = Budget
    form_class = BudgetForm
    template_name = "core/object_form.html"
    success_url = reverse_lazy("ledger:budget_list")

    def get_initial(self):
        initial = super().get_initial()
        today = timezone.localdate()
        initial.update(year=today.year, month=today.month)
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            form_title="Set a monthly budget",
            form_help="Budgets are shared with your family. Alerts appear at 80% and 100% of the limit.",
            submit_label="Save budget",
            cancel_url=self.success_url,
        )
        return context

    @db_transaction.atomic
    def form_valid(self, form):
        messages.success(self.request, "Budget saved.")
        response = super().form_valid(form)
        record_audit_event(
            family=self.family,
            actor=self.acting_member,
            action=AuditEvent.Action.CREATED,
            entity_type=AuditEvent.EntityType.BUDGET,
            instance=self.object,
        )
        return response

    def get_success_url(self):
        return (
            f"{reverse('ledger:budget_list')}?"
            f"month={self.object.year:04d}-{self.object.month:02d}"
        )


class BudgetUpdateView(
    FamilyAdminRequiredMixin,
    FamilyScopedQuerysetMixin,
    FamilyFormKwargsMixin,
    AuditUpdateMixin,
    UpdateView,
):
    model = Budget
    form_class = BudgetForm
    template_name = "core/object_form.html"
    success_url = reverse_lazy("ledger:budget_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            form_title="Edit budget",
            submit_label="Save changes",
            cancel_url=self.success_url,
        )
        return context

    @db_transaction.atomic
    def form_valid(self, form):
        messages.success(self.request, "Budget updated.")
        response = super().form_valid(form)
        record_audit_event(
            family=self.family,
            actor=self.acting_member,
            action=AuditEvent.Action.UPDATED,
            entity_type=AuditEvent.EntityType.BUDGET,
            instance=self.object,
            before=self._audit_before,
        )
        return response

    def get_success_url(self):
        return (
            f"{reverse('ledger:budget_list')}?"
            f"month={self.object.year:04d}-{self.object.month:02d}"
        )


class BudgetDeleteView(
    FamilyAdminRequiredMixin,
    FamilyScopedQuerysetMixin,
    DeleteView,
):
    model = Budget
    template_name = "core/object_confirm_delete.html"
    success_url = reverse_lazy("ledger:budget_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = self.success_url
        return context

    @db_transaction.atomic
    def form_valid(self, form):
        before = audit_snapshot(self.object)
        messages.success(self.request, "Budget deleted.")
        record_audit_event(
            family=self.family,
            actor=self.acting_member,
            action=AuditEvent.Action.DELETED,
            entity_type=AuditEvent.EntityType.BUDGET,
            instance=self.object,
            before=before,
        )
        return super().form_valid(form)

    def get_success_url(self):
        return (
            f"{reverse('ledger:budget_list')}?"
            f"month={self.object.year:04d}-{self.object.month:02d}"
        )


class SavingsGoalListView(FamilyRequiredMixin, TemplateView):
    template_name = "ledger/savings_goal_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["savings_goal_statuses"] = savings_goal_statuses(self.family)
        return context


class SavingsGoalCreateView(
    FamilyAdminRequiredMixin,
    FamilyFormKwargsMixin,
    CreateView,
):
    model = SavingsGoal
    form_class = SavingsGoalForm
    template_name = "core/object_form.html"
    success_url = reverse_lazy("ledger:savings_goal_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            form_title="Create a savings goal",
            form_help="Goals are shared with your family. Members can record contributions separately from ledger transactions.",
            submit_label="Create goal",
            cancel_url=self.success_url,
        )
        return context

    @db_transaction.atomic
    def form_valid(self, form):
        messages.success(self.request, "Savings goal created.")
        response = super().form_valid(form)
        record_audit_event(
            family=self.family,
            actor=self.acting_member,
            action=AuditEvent.Action.CREATED,
            entity_type=AuditEvent.EntityType.SAVINGS_GOAL,
            instance=self.object,
        )
        return response


class SavingsGoalUpdateView(
    FamilyAdminRequiredMixin,
    FamilyScopedQuerysetMixin,
    FamilyFormKwargsMixin,
    AuditUpdateMixin,
    UpdateView,
):
    model = SavingsGoal
    form_class = SavingsGoalForm
    template_name = "core/object_form.html"
    success_url = reverse_lazy("ledger:savings_goal_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            form_title=f"Edit {self.object.name}",
            submit_label="Save changes",
            cancel_url=self.success_url,
        )
        return context

    @db_transaction.atomic
    def form_valid(self, form):
        messages.success(self.request, "Savings goal updated.")
        response = super().form_valid(form)
        record_audit_event(
            family=self.family,
            actor=self.acting_member,
            action=AuditEvent.Action.UPDATED,
            entity_type=AuditEvent.EntityType.SAVINGS_GOAL,
            instance=self.object,
            before=self._audit_before,
        )
        return response


class SavingsGoalDeleteView(
    FamilyAdminRequiredMixin,
    FamilyScopedQuerysetMixin,
    DeleteView,
):
    model = SavingsGoal
    template_name = "core/object_confirm_delete.html"
    success_url = reverse_lazy("ledger:savings_goal_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = self.success_url
        return context

    @db_transaction.atomic
    def form_valid(self, form):
        before = audit_snapshot(self.object)
        record_audit_event(
            family=self.family,
            actor=self.acting_member,
            action=AuditEvent.Action.DELETED,
            entity_type=AuditEvent.EntityType.SAVINGS_GOAL,
            instance=self.object,
            before=before,
        )
        response = super().form_valid(form)
        messages.success(self.request, "Savings goal deleted.")
        return response


class GoalContributionCreateView(
    FamilyRequiredMixin,
    CreateView,
):
    model = GoalContribution
    form_class = GoalContributionForm
    template_name = "core/object_form.html"

    def get_goal(self):
        return get_object_or_404(
            SavingsGoal,
            pk=self.kwargs["goal_pk"],
            family=self.family,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        goal = self.get_goal()
        context.update(
            form_title=f"Contribute to {goal.name}",
            form_help="This contribution updates goal progress only; it does not create a ledger transaction.",
            submit_label="Record contribution",
            cancel_url=reverse("ledger:savings_goal_list"),
        )
        return context

    @db_transaction.atomic
    def form_valid(self, form):
        contribution = form.save(commit=False)
        contribution.goal = self.get_goal()
        contribution.family = self.family
        contribution.member = self.acting_member
        contribution.save()
        self.object = contribution
        record_audit_event(
            family=self.family,
            actor=self.acting_member,
            action=AuditEvent.Action.CREATED,
            entity_type=AuditEvent.EntityType.GOAL_CONTRIBUTION,
            instance=contribution,
        )
        messages.success(self.request, "Savings contribution recorded.")
        return redirect("ledger:savings_goal_list")


class AuditHistoryView(
    FamilyAdminRequiredMixin,
    ListView,
):
    model = AuditEvent
    template_name = "ledger/audit_history.html"
    context_object_name = "audit_events"
    paginate_by = 50

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(family=self.family)
            .select_related("actor")
        )
