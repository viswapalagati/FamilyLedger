"""ledger admin — SKELETON (FR-14.1).

Register AccountHead, Transaction, RecurringTemplate with useful list_display /
list_filter / search_fields / date_hierarchy / autocomplete_fields. See §14.
Transaction.occurred_date is read-only.
"""

from django.contrib import admin

from .models import AccountHead, RecurringTemplate, Transaction


@admin.register(AccountHead)
class AccountHeadAdmin(admin.ModelAdmin):
    list_display = ["name", "family", "kind", "parent", "is_archived"]
    list_filter = ["family", "kind", "is_archived"]
    search_fields = ["name"]


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        "occurred_date", "family", "member", "txn_type", "account_head",
        "amount", "merchant_or_source", "recorded_by",
    ]
    list_filter = ["family", "txn_type", "payment_method", "occurred_date"]
    search_fields = ["merchant_or_source", "description"]
    date_hierarchy = "occurred_date"
    autocomplete_fields = ["member", "recorded_by", "account_head", "bank_account"]
    readonly_fields = ["occurred_date"]


@admin.register(RecurringTemplate)
class RecurringTemplateAdmin(admin.ModelAdmin):
    list_display = [
        "family", "member", "txn_type", "amount", "frequency",
        "next_run_date", "is_active",
    ]
    list_filter = ["family", "txn_type", "frequency", "is_active"]