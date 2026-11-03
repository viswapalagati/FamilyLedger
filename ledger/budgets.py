from decimal import Decimal

from django.db.models import Sum

from .models import Budget, Transaction, TxnType


ALERT_THRESHOLD = Decimal("80")


def budget_statuses(family, year, month):
    spent_by_head = dict(
        Transaction.objects.filter(
            family=family,
            txn_type=TxnType.EXPENSE,
            occurred_date__year=year,
            occurred_date__month=month,
        )
        .values_list("account_head_id")
        .annotate(total=Sum("amount"))
    )
    statuses = []
    for budget in (
        Budget.objects.filter(family=family, year=year, month=month)
        .select_related("account_head")
    ):
        spent = spent_by_head.get(budget.account_head_id, Decimal("0"))
        percent = spent * 100 / budget.amount
        if percent >= 100:
            alert = "exceeded"
        elif percent >= ALERT_THRESHOLD:
            alert = "warning"
        else:
            alert = None
        statuses.append(
            {
                "budget": budget,
                "spent": spent,
                "remaining": max(budget.amount - spent, Decimal("0")),
                "percent": percent,
                "progress_percent": min(percent, Decimal("100")),
                "alert": alert,
            }
        )
    return statuses
