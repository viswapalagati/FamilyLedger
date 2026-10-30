from decimal import Decimal

from django.db.models import Sum

from .models import GoalContribution, SavingsGoal


def savings_goal_statuses(family):
    contributions = dict(
        GoalContribution.objects.filter(family=family)
        .values_list("goal_id")
        .annotate(total=Sum("amount"))
    )
    goals = (
        SavingsGoal.objects.filter(family=family)
        .prefetch_related("contributions__member")
    )
    statuses = []
    for goal in goals:
        saved = contributions.get(goal.pk, Decimal("0"))
        percent = saved * 100 / goal.target_amount
        statuses.append(
            {
                "goal": goal,
                "saved": saved,
                "remaining": max(goal.target_amount - saved, Decimal("0")),
                "percent": percent,
                "progress_percent": min(percent, Decimal("100")),
                "is_complete": saved >= goal.target_amount,
            }
        )
    return statuses
