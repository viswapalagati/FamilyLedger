"""dashboard views — SKELETON. Implement per §4.12 (FR-12.*), §14.2, §16.

Routes (dashboard/urls.py, already wired):
  /dashboard/               OverviewView       (default landing page)
  /dashboard/family/        FamilyReportView   (forces family scope)
  /dashboard/member/<pk>/   MemberReportView   (scope pinned to the URL member)
  /dashboard/category/<pk>/ CategoryDrillView
  /dashboard/api/chart/<slug>/  ChartDataView  (JsonResponse; slugs:
                                income-expense, expense-by-head, monthly-series)

Build the Chart.js configs server-side and hand them to the template as JSON
(see core/static/core/app.js, which reads ``<canvas data-chart='...'>``).
All four page views use ScopePeriodMixin; see §14.2 for the exact context keys
each template reads.
"""

from django.views.generic import TemplateView, View

from core.mixins import ScopePeriodMixin  # noqa: F401
from . import services  # noqa: F401
from ledger.models import Transaction, TxnType  # noqa: F401
import json
from django.shortcuts import get_object_or_404
from ledger.models import AccountHead  # noqa: F401
from django.http import JsonResponse

print("dashboard views.py loaded")


def _pie(labels, values, palette="categorical"):
    return {
        "type": "doughnut",
        "data": {
            "labels": labels,
            "datasets": [{"data": values, "_palette": palette}],
        },
        "options": {"plugins": {"legend": {"position": "right"}}, "cutout": "58%"},
    }

def _bar_income_expense(series):
    return {
        "type": "bar",
        "data": {
            "labels": series["labels"],
            "datasets": [
                {"label": "Income", "data": series["income"], "_palette": "income"},
                {"label": "Expense", "data": series["expense"], "_palette": "expense"},
            ],
        },
        "options": {
            "scales": {"y": {"beginAtZero": True}},
            "plugins": {"legend": {"position": "bottom"}},
        },
    }


class OverviewView(ScopePeriodMixin, TemplateView):
    """FR-12.1. Template: dashboard/overview.html."""

    template_name = "dashboard/overview.html"
    # TODO: totals, expense_rows, income_rows, top_*_merchants, recurring_count,
    #       recent, member_breakdown (family scope only), net_worth, the three
    #       chart_*_json blobs, filter_ctx, scope_title.

    print("OverviewView initialized")
    def get_context_data(self, **kwargs):
        try:
            context = super().get_context_data(**kwargs)
            print("printing context of overviewView", context)
            txns = self.scope_transactions(Transaction.objects.all())
            totals = services.period_totals(txns)
            expense_rows = services.by_head(txns, TxnType.EXPENSE)
            income_rows = services.by_head(txns, TxnType.INCOME)
            series = services.series_by_month(txns, self.period)
            print("2")

            context["totals"] = totals
            context["expense_rows"] = expense_rows[:8]
            context["income_rows"] = income_rows[:8]
            print("3")
            context["top_expense_merchants"] = services.top_merchants(txns, TxnType.EXPENSE)
            context["top_income_sources"] = services.top_merchants(txns, TxnType.INCOME)
            context["anomaly_count"] = 0
            print("4")
            context["recurring_count"] = self.family.recurring_templates.filter(is_active=True).count()
            context["recent"] = txns.select_related("member", "account_head", "recorded_by")[:8]
            print("5")

            if self.scope_member is None:
                context["member_breakdown"] = services.member_breakdown(self.family, self.period)
            else:
                context["member_breakdown"] = None
            print("6")

            nw_member = self.scope_member if self.scope_member else None
            print("nw_member:", nw_member)
            context["net_worth"] = services.net_worth(self.family, nw_member)
            print("7")

            context["chart_income_expense_json"] = json.dumps(
                _pie(["Income", "Expense"], [float(totals["income"]), float(totals["expense"])], "semantic")
            )
            context["chart_expense_head_json"] = json.dumps(
                _pie([r["label"] for r in expense_rows], [float(r["total"]) for r in expense_rows])
            )
            print("8")
            context["chart_series_json"] = json.dumps(_bar_income_expense(series))

            context["filter_ctx"] = self.get_filter_ctx()
            context["scope_title"] = (
                "Whole family" if self.scope_member is None
                else ("You" if self.scope_member.pk == self.acting_member.pk else self.scope_member.full_name)
            )
            print("9")
            print("OverviewView context data prepared", context)
            return context
        
        except Exception as e:
            print("Error in OverviewView get_context_data:", e)
            

    
        


class FamilyReportView(ScopePeriodMixin, TemplateView):
    """FR-12.2. Forces family scope. Template: dashboard/family_report.html."""

    template_name = "dashboard/family_report.html"
    default_scope = "family"
    # TODO: force scope = family in _prepare_scope_period(); build context.

    def _prepare_scope_period(self):
        super()._prepare_scope_period()
        self.scope = "family"
        self.scope_member = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        txns = self.scope_transactions(Transaction.objects.all())
        context["totals"] = services.period_totals(txns)
        context["member_breakdown"] = services.member_breakdown(self.family, self.period)
        context["expense_rows"] = services.by_head(txns, TxnType.EXPENSE)
        context["income_rows"] = services.by_head(txns, TxnType.INCOME)
        series = services.series_by_month(txns, self.period)
        context["chart_series_json"] = json.dumps(_bar_income_expense(series))
        context["chart_expense_head_json"] = json.dumps(
            _pie(
                [r["label"] for r in context["expense_rows"]],
                [float(r["total"]) for r in context["expense_rows"]],
            )
        )
        context["net_worth"] = services.net_worth(self.family)
        context["filter_ctx"] = self.get_filter_ctx()
        return context


class MemberReportView(ScopePeriodMixin, TemplateView):
    """FR-12.3. Scope pinned to the URL's member. Template: dashboard/member_report.html."""

    template_name = "dashboard/member_report.html"
    # TODO: resolve the member from self.kwargs['pk'] (404 if not in the family);
    #       pin scope_member; build context.


    def _prepare_scope_period(self):
        super()._prepare_scope_period()
        member = get_object_or_404(self.family.members, pk=self.kwargs["pk"])
        self.scope = f"member:{member.pk}"
        self.scope_member = member

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        member = self.scope_member
        txns = self.scope_transactions(Transaction.objects.all())
        context["member"] = member
        context["totals"] = services.period_totals(txns)
        context["expense_rows"] = services.by_head(txns, TxnType.EXPENSE)
        context["income_rows"] = services.by_head(txns, TxnType.INCOME)
        series = services.series_by_month(txns, self.period)
        context["chart_series_json"] = json.dumps(_bar_income_expense(series))
        context["chart_expense_head_json"] = json.dumps(
            _pie(
                [r["label"] for r in context["expense_rows"]],
                [float(r["total"]) for r in context["expense_rows"]],
            )
        )
        context["recent"] = txns.select_related("account_head", "recorded_by")[:12]
        context["net_worth"] = services.net_worth(self.family, member)
        context["filter_ctx"] = self.get_filter_ctx()
        return context



class CategoryDrillView(ScopePeriodMixin, TemplateView):
    """FR-12.4. Template: dashboard/category_drill.html."""

    template_name = "dashboard/category_drill.html"
    # TODO: resolve the AccountHead (family-scoped, 404 otherwise); by-merchant
    #       breakdown + transaction list for the scope & period.
    template_name = "dashboard/category_drill.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        head = get_object_or_404(AccountHead, pk=self.kwargs["pk"], family=self.family)
        txns = self.scope_transactions(Transaction.objects.filter(account_head=head))
        context["head"] = head
        context["merchant_rows"] = services.top_merchants(txns, head.kind, limit=50)
        context["transactions"] = txns.select_related("member", "recorded_by")[:200]
        context["total"] = services.period_totals(txns)
        context["filter_ctx"] = self.get_filter_ctx()
        return context




class ChartDataView(ScopePeriodMixin, View):
    """FR-12.6. JSON chart configs. slug in {income-expense, expense-by-head,
    monthly-series}; honours ?scope / ?period / ?anchor."""

    def get(self, request, *args, **kwargs):
        self._prepare_scope_period()
        slug = kwargs["slug"]
        txns = self.scope_transactions(Transaction.objects.all())

        if slug == "income-expense":
            totals = services.period_totals(txns)
            return JsonResponse(
                _pie(["Income", "Expense"],
                     [float(totals["income"]), float(totals["expense"])], "semantic")
            )
        if slug == "expense-by-head":
            rows = services.by_head(txns, TxnType.EXPENSE)
            return JsonResponse(
                _pie([r["label"] for r in rows], [float(r["total"]) for r in rows])
            )
        if slug == "monthly-series":
            return JsonResponse(_bar_income_expense(services.series_by_month(txns, self.period)))
        return JsonResponse({"error": "unknown chart"}, status=404)
