"""assets models — SKELETON.

Implement per §12.7 (abstract OwnedFinancialItem) and §12.7.1-12.7.4 (the four
concrete models). Enumerations (§24) are provided; the fields are yours.

Reminders:
  * shared fields on the abstract base: family (FK, CASCADE), owner (FK
    FamilyMember, PROTECT), registered_by (FK FamilyMember, PROTECT), name,
    notes, is_active  -- use related_name="%(class)ss_owned" /
    "%(class)ss_registered" to avoid reverse-accessor clashes
  * clean(): owner & registered_by must belong to ``family``  -- BR-15
  * editable_by(member): admin or member in {owner, registered_by}  -- BR-5
  * ``net_worth_value`` property, overridden per model (§12.7.*, BR-11):
      BankAccount   -> current_balance
      PhysicalAsset -> current_value
      DigitalAsset  -> current_value
      OtherFinancialInfo -> +amount if owed_to_us, -amount if owed_by_us, else 0
  * money = DecimalField(max_digits=12, decimal_places=2)
"""

from django.db import models

from django.core.exceptions import ValidationError
from core.models import TimeStampedModel
from django.utils import timezone
from decimal import Decimal
from families.models import Family, FamilyMember
MONEY = dict(max_digits=12, decimal_places=2)  # noqa: F401


class OwnedFinancialItem(TimeStampedModel):
    # TODO §12.7: family, owner, registered_by, name, notes, is_active
    # TODO: clean(), editable_by(member), net_worth_value

    class Meta:
        abstract = True

    def __str__(self):
        return getattr(self, "name", f"{type(self).__name__} #{self.pk}")

    
    family = models.ForeignKey(
        Family,
        on_delete=models.CASCADE,
        related_name="%(class)ss",
        null=True,
        blank=True
    )   
    owner = models.ForeignKey(
        FamilyMember,
        on_delete=models.PROTECT,
        related_name="%(class)ss_owned",
        null=True,
        blank=True
    )
    registered_by = models.ForeignKey(
        FamilyMember,
        on_delete=models.PROTECT,
        related_name="%(class)ss_registered",
        null=True,
        blank=True
    )
    name = models.CharField(max_length=120)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def clean(self):
        # Ensure owner and registered_by belong to the same family
        if self.owner and self.owner.family != self.family:
            raise ValidationError("Owner must belong to the same family.")
        if self.registered_by and self.registered_by.family != self.family:
            raise ValidationError("Registered by must belong to the same family.")
    def editable_by(self, member):
        # Admin or member in {owner, registered_by}
        return member.is_family_admin or member in {self.owner, self.registered_by} 
    def net_worth_value(self):
        # To be overridden in subclasses
        return Decimal("0.00")
    



class BankAccount(OwnedFinancialItem):
    class AccountType(models.TextChoices):
        SAVINGS = "savings", "Savings"
        CURRENT = "current", "Current"
        SALARY = "salary", "Salary"
        NRE = "nre", "NRE"
        NRO = "nro", "NRO"
        FD = "fd", "Fixed deposit"
        RD = "rd", "Recurring deposit"
        OTHER = "other", "Other"

    # TODO §12.7.1: bank_name, account_holder_name, account_number, account_type,
    #               ifsc, branch_name, opening_balance, current_balance, currency
    # TODO: masked_number property (last 4)

    bank_name = models.CharField(max_length=120, blank=True)
    account_holder_name = models.CharField(max_length=120, blank=True)
    account_number = models.CharField(max_length=34, blank=True)
    account_type = models.CharField(
        max_length=10, choices=AccountType.choices, default=AccountType.SAVINGS
    )
    ifsc = models.CharField("IFSC", max_length=15, blank=True)
    branch_name = models.CharField(max_length=120, blank=True)
    opening_balance = models.DecimalField(default=Decimal("0.00"), **MONEY)
    current_balance = models.DecimalField(default=Decimal("0.00"), **MONEY)
    currency = models.CharField(max_length=3, default="INR")

    @property
    def masked_number(self):
        digits = self.account_number.strip()
        return f"••••{digits[-4:]}" if len(digits) >= 4 else digits

    @property
    def net_worth_value(self) -> Decimal:
        return self.current_balance or Decimal("0.00")


class PhysicalAsset(OwnedFinancialItem):
    class AssetType(models.TextChoices):
        REAL_ESTATE = "real_estate", "Real estate"
        LAND = "land", "Land"
        VEHICLE = "vehicle", "Vehicle"
        JEWELLERY = "jewellery", "Jewellery"
        GOLD = "gold", "Gold"
        ELECTRONICS = "electronics", "Electronics"
        FURNITURE = "furniture", "Furniture"
        OTHER = "other", "Other"

    # TODO §12.7.2: asset_type, acquisition_date, acquisition_cost, current_value,
    #               valuation_date, quantity, unit, location
    asset_type = models.CharField(
        max_length=20, choices=AssetType.choices,default=AssetType.OTHER
    )
    acquisition_date = models.DateField(blank=True, null=True)
    acquisition_cost = models.DecimalField(null=True, blank=True, **MONEY)
    current_value = models.DecimalField(default=Decimal("0.00"), **MONEY)
    valuation_date = models.DateTimeField(null=True)
    quantity = models.DecimalField(default=Decimal("1.00"), max_digits=10, decimal_places=3)
    unit = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=150, blank=True)

    @property
    def net_worth_value(self) -> Decimal:
        return self.current_value or Decimal("0.00")


class DigitalAsset(OwnedFinancialItem):
    class AssetType(models.TextChoices):
        STOCKS = "stocks", "Stocks"
        MUTUAL_FUND = "mutual_fund", "Mutual fund"
        CRYPTO = "crypto", "Crypto"
        FIXED_DEPOSIT = "fixed_deposit", "Fixed deposit"
        BOND = "bond", "Bond"
        EPF_PF = "epf_pf", "EPF / PF"
        PPF = "ppf", "PPF"
        NPS = "nps", "NPS"
        INSURANCE = "insurance", "Insurance policy"
        WALLET = "wallet", "Wallet"
        DOMAIN = "domain", "Domain"
        OTHER = "other", "Other"

    # TODO §12.7.3: asset_type, provider_or_platform, identifier, invested_amount,
    #               current_value, valuation_date, units, maturity_date

    asset_type = models.CharField(max_length=15, choices=AssetType.choices, default=AssetType.OTHER)
    provider_or_platform = models.CharField(max_length=120, blank=True)
    identifier = models.CharField(max_length=80, blank=True, help_text="Folio / demat / policy no.")
    invested_amount = models.DecimalField( null=True, blank=True, **MONEY)
    current_value = models.DecimalField(default=Decimal("0.00"), **MONEY)
    valuation_date = models.DateField(null=True, blank=True)
    units = models.DecimalField(max_digits=16, decimal_places=4, null=True, blank=True)
    maturity_date = models.DateField(null=True, blank=True)

    @property
    def net_worth_value(self) -> Decimal:
        return self.current_value or Decimal("0.00")


class OtherFinancialInfo(OwnedFinancialItem):
    class InfoType(models.TextChoices):
        LOAN = "loan", "Loan"
        LIABILITY = "liability", "Liability"
        SUBSCRIPTION = "subscription", "Subscription"
        RECEIVABLE = "receivable", "Receivable"
        PAYABLE = "payable", "Payable"
        NOMINEE = "nominee", "Nominee info"
        OTHER = "other", "Other"

    class Direction(models.TextChoices):
        OWED_TO_US = "owed_to_us", "Owed to us (asset)"
        OWED_BY_US = "owed_by_us", "Owed by us (liability)"
        NONE = "none", "Not applicable"

    # TODO §12.7.4: info_type, amount, direction, counterparty, start_date, end_date
    info_type = models.CharField(max_length=15, choices=InfoType.choices, default=InfoType.OTHER)
    amount = models.DecimalField(default=Decimal("0.00"), **MONEY)
    direction = models.CharField(max_length=12, choices=Direction.choices, default=Direction.NONE)
    counterparty = models.CharField(max_length=150, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)


    class Meta(OwnedFinancialItem.Meta):
        verbose_name = "other financial info"
        verbose_name_plural = "other financial info"

    @property
    def net_worth_value(self) -> Decimal:
        if self.direction == self.Direction.OWED_TO_US:
            return self.amount or Decimal("0.00")
        if self.direction == self.Direction.OWED_BY_US:
            return -(self.amount or Decimal("0.00"))
        return Decimal("0.00")
