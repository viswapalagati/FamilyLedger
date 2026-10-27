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

from multiprocessing import context

from django.views.generic import (
    CreateView,
    DeleteView,
    ListView,
    UpdateView,
    View,
)

from core.mixins import (  # noqa: F401
    FamilyFormKwargsMixin,
    FamilyRequiredMixin,
    FamilyScopedQuerysetMixin,
    RecordEditPermissionMixin,
    ScopePeriodMixin,
)

from django.db import models
from ledger.models import Transaction, TxnType, AccountHead  # noqa: F401
from .forms import TransactionForm, AccountHeadForm # noqa: F401
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.db.models import Count
from django.urls import reverse, reverse_lazy
from django.db.models import Sum
from .models import RecurringTemplate
from .forms import RecurringTemplateForm 


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

    def form_valid(self, form):
        obj = form.save()
        messages.success(
            self.request,
            f"{obj.get_txn_type_display()} of ₹{obj.amount} recorded for {obj.member.full_name}.",
        )
        self.object = obj
        target = "ledger:income_list" if obj.txn_type == TxnType.INCOME else "ledger:expense_list"
        return redirect(target)
    

    


class EntryUpdateView(FamilyRequiredMixin, FamilyScopedQuerysetMixin,
                      FamilyFormKwargsMixin, RecordEditPermissionMixin, UpdateView):
    """Edit an entry (FR-5.9). Template: ledger/entry_form.html."""
    template_name = "ledger/entry_form.html"
    model = Transaction
    form_class = TransactionForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_title"] = "Edit entry"
        return context

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
