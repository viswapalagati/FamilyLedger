"""assets admin — SKELETON (FR-14.1).

Register BankAccount, PhysicalAsset, DigitalAsset, OtherFinancialInfo with a
shared ModelAdmin base (list_display incl. owner + value, list_filter by family
and is_active, autocomplete for family/owner/registered_by). See §14.
"""

from django.contrib import admin

from .models import BankAccount, DigitalAsset, OtherFinancialInfo, PhysicalAsset


class _OwnedAdmin(admin.ModelAdmin):
    list_display = ["name", "family", "owner", "is_active"]
    list_filter = ["family", "is_active"]
    search_fields = ["name", "owner__full_name"]
    autocomplete_fields = ["family", "owner", "registered_by"]


@admin.register(BankAccount)
class BankAccountAdmin(_OwnedAdmin):
    list_display = ["name", "family", "owner", "bank_name", "account_type", "current_balance", "is_active"]
    search_fields = ["name", "bank_name", "owner__full_name"]


@admin.register(PhysicalAsset)
class PhysicalAssetAdmin(_OwnedAdmin):
    list_display = ["name", "family", "owner", "asset_type", "current_value", "is_active"]


@admin.register(DigitalAsset)
class DigitalAssetAdmin(_OwnedAdmin):
    list_display = ["name", "family", "owner", "asset_type", "current_value", "is_active"]


@admin.register(OtherFinancialInfo)
class OtherFinancialInfoAdmin(_OwnedAdmin):
    list_display = ["name", "family", "owner", "info_type", "direction", "amount", "is_active"]