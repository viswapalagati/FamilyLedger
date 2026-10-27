"""assets forms — SKELETON. Implement per §15 (row "BankAccountForm / ... ") and
§4.6-§4.9.

Every form scopes ``owner`` to the family's active members (initial = the acting
member) and, on create, stamps ``family`` and ``registered_by`` = acting member.
"""

from django import forms 
from core.forms import FamilyModelForm
from .models import BankAccount, DigitalAsset, OtherFinancialInfo, PhysicalAsset

_DATE = forms.DateInput(attrs={"type":"date"})

class OwnedItemForm(FamilyModelForm):
    """Base: scope ``owner`` to the family; stamp family + registered_by (§15)."""

    # TODO: __init__ (owner queryset + initial), save() (family + registered_by)

    owner_filed = "owner"
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.family = self.family
        if not self.instance.pk:
            self.instance.registered_by = self.acting_member
            self.fields["owner"].initial = self.acting_member
        self.fields["owner"].queryset = self.family.members.filter(
            status="active"
            ).order_by("full_name")

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.family = self.family
        if not obj.pk:
            obj.registered_by = self.acting_member
        if commit:
            obj.save()
        return obj


class BankAccountForm(OwnedItemForm):
    class Meta:
        model = BankAccount
        fields = [
            "owner", "name", "bank_name", "account_holder_name", "account_number",
            "account_type", "ifsc", "branch_name", "opening_balance",
            "current_balance", "currency", "is_active", "notes",
            ]  




class PhysicalAssetForm(OwnedItemForm):
    class Meta:
        model = PhysicalAsset
        fields = [
            "owner", "name", "asset_type", "acquisition_date", "acquisition_cost",
            "current_value", "valuation_date", "quantity", "unit", "location",
            "is_active", "notes",

        ]  

        widgets = {"acquisition_date": _DATE, "valuation_date": _DATE} 


class DigitalAssetForm(OwnedItemForm):
    class Meta:
        model = DigitalAsset
        fields = [
            "owner", "name", "asset_type", "provider_or_platform", "identifier",
            "invested_amount", "current_value", "valuation_date", "units",
            "maturity_date", "is_active", "notes",
        ]  

        widgets = {"valuation_date": _DATE, "maturity_date": _DATE}


class OtherFinancialInfoForm(OwnedItemForm):
    class Meta:
        model = OtherFinancialInfo
        fields = [
            "owner", "name", "info_type", "amount", "direction", "counterparty",
            "start_date", "end_date", "is_active", "notes",
        ]  # TODO §12.7.4 + owner, is_active, notes
        widgets = {"start_date": _DATE, "edn_date":_DATE}
