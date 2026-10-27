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
]

