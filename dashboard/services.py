"""dashboard aggregation service — SKELETON.

Implement per §16.2 (function table + worked examples), §4.12 (FR-12.*),
BR-11 (net worth) and BR-12 (savings figures).

All functions are pure: they take querysets / a family / a period and return
plain dicts / lists. Do the maths in the database (aggregate / annotate /
values) -- never sum Python lists (FR-12.7). Family totals must equal the sum of
per-member totals for the same period (FR-12.8 / BR-12).
"""

from ledger.models import Transaction,TxnType
from django.db.models.functions import Coalesce
from django.db.models import DecimalField, Value, Sum
from decimal import Decimal
from core.periods import month_buckets
from assets.models import BankAccount, PhysicalAsset, DigitalAsset, OtherFinancialInfo

ZERO = Value(Decimal("0.00"), output_field=DecimalField(max_digits=14, decimal_places=2))

def _sum(qs, field="amount"):
    return qs.aggregate(v=Coalesce(Sum(field), ZERO))["v"]

def period_totals(txn_qs):
    """-> {income, expense, net, savings_rate}  (BR-12)."""

    income = _sum(txn_qs.filter(txn_type=TxnType.INCOME))
    expense = _sum(txn_qs.filter(txn_type=TxnType.EXPENSE))
    net = income - expense
    savings_rate = (net/income * 100) if income else 0

    return {
        "income" : income,
        "expense" : expense,
        "net" : net,
        "savings_rate" : round(savings_rate,1)
    }



def by_head(txn_qs, txn_type)-> list[dict]:
    """-> [{label, total, head_id}] ordered by total desc."""

    rows = (
        txn_qs.filter(txn_type=txn_type)
        .values("account_head_id", "account_head__name")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    )
    return [
        {"label": r["account_head__name"], "total": r["total"], "head_id": r["account_head_id"]}
        for r in rows
    ]

    


def top_merchants(txn_qs, txn_type, limit=8) -> list[dict]:
    rows = (
        txn_qs.filter(txn_type=txn_type)
        .exclude(merchant_or_source="")
        .values("merchant_or_source")
        .annotate(total=Sum("amount"))
        .order_by("-total")[:limit] 
    )
    return [{"label": r["merchant_or_source"], "total": r["total"]} for r in rows] 
    




def series_by_month(txn_qs, period):
    """-> {labels: [...], income: [...], expense: [...]} across month buckets."""
    """Income vs expense totals per month bucket in the period."""

    buckets = month_buckets(period)
    labels, income, expense = [], [], []
    for b_start, b_end, label in buckets:
        window = txn_qs.filter(occurred_date__range=(b_start, b_end))
        labels.append(label)
        income.append(float(_sum(window.filter(txn_type=TxnType.INCOME))))
        expense.append(float(_sum(window.filter(txn_type=TxnType.EXPENSE))))
    return {"labels": labels, "income": income, "expense": expense}


def member_breakdown(family, period) -> list[dict]:
    base = Transaction.objects.filter(family=family)
    if period.is_bounded:
        base = base.filter(occurred_date__range=(period.start, period.end))
    out = []
    for member in family.active_members:
        m_qs = base.filter(member=member)
        totals = period_totals(m_qs)
        out.append({
            "member": member,
            "income": totals["income"],
            "expense": totals["expense"],
            "net": totals["net"],
        })
    out.sort(key=lambda r: r["expense"], reverse=True)
    return out


def net_worth(family, member=None) -> dict:
    """Bank + physical + digital current values, plus receivables minus
    liabilities from OtherFinancialInfo. Filter by ``member`` for a per-person
    figure, otherwise the whole family."""

    def scoped(model):
        qs = model.objects.filter(family=family, is_active=True)
        return qs.filter(owner=member) if member else qs

    bank = _sum(scoped(BankAccount), "current_balance")
    physical = _sum(scoped(PhysicalAsset), "current_value")
    digital = _sum(scoped(DigitalAsset), "current_value")
    receivable = _sum(
        scoped(OtherFinancialInfo).filter(direction=OtherFinancialInfo.Direction.OWED_TO_US)
    )
    liability = _sum(
        scoped(OtherFinancialInfo).filter(direction=OtherFinancialInfo.Direction.OWED_BY_US)
    )
    total = bank + physical + digital + receivable - liability
    return {
        "bank": bank,
        "physical": physical,
        "digital": digital,
        "receivable": receivable,
        "liability": liability,
        "total": total,
    }
