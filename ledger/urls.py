from django.urls import path

from . import views

app_name = "ledger"

urlpatterns = [
    # account heads
    path("heads/", views.HeadListView.as_view(), name="head_list"),
    path("heads/add/", views.HeadCreateView.as_view(), name="head_add"),
    path("heads/<int:pk>/edit/", views.HeadUpdateView.as_view(), name="head_edit"),
    path("heads/<int:pk>/archive/", views.HeadArchiveView.as_view(), name="head_archive"),
    # transactions
    path("income/", views.IncomeListView.as_view(), name="income_list"),
    path("expenses/", views.ExpenseListView.as_view(), name="expense_list"),
    path("entries/add/", views.EntryCreateView.as_view(), name="entry_add"),
    path("entries/<int:pk>/edit/", views.EntryUpdateView.as_view(), name="entry_edit"),
    path("entries/<int:pk>/delete/", views.EntryDeleteView.as_view(), name="entry_delete"),
    # recurring
    path("recurring/", views.RecurringListView.as_view(), name="recurring_list"),
    path("recurring/add/", views.RecurringCreateView.as_view(), name="recurring_add"),
    path("recurring/<int:pk>/edit/", views.RecurringUpdateView.as_view(), name="recurring_edit"),
    path("recurring/<int:pk>/delete/", views.RecurringDeleteView.as_view(), name="recurring_delete"),

    path("budgets/", views.BudgetListView.as_view(), name="budget_list"),
    path("budgets/add/", views.BudgetCreateView.as_view(), name="budget_add"),
    path("budgets/<int:pk>/edit/", views.BudgetUpdateView.as_view(), name="budget_edit"),
    path("budgets/<int:pk>/delete/", views.BudgetDeleteView.as_view(), name="budget_delete"),
    path("goals/", views.SavingsGoalListView.as_view(), name="savings_goal_list"),
    path("goals/add/", views.SavingsGoalCreateView.as_view(), name="savings_goal_add"),
    path(
        "goals/<int:pk>/edit/",
        views.SavingsGoalUpdateView.as_view(),
        name="savings_goal_edit",
    ),
    path(
        "goals/<int:pk>/delete/",
        views.SavingsGoalDeleteView.as_view(),
        name="savings_goal_delete",
    ),
    path(
        "goals/<int:goal_pk>/contribute/",
        views.GoalContributionCreateView.as_view(),
        name="goal_contribute",
    ),
    path("audit/", views.AuditHistoryView.as_view(), name="audit_history"),
]

