"""ledger models — SKELETON.

Implement per §12.4 (AccountHead), §12.5 (Transaction), §12.6 (RecurringTemplate),
BR-1, BR-6, BR-7, BR-15, and §16.3 (advance()).

Reminders:
  * money = DecimalField(max_digits=12, decimal_places=2)   -- BR-13
  * Transaction carries BOTH ``member`` (earner/spender) and ``recorded_by``
    (typist) -- the whole product depends on not confusing them (§3 / BR-1)
  * ``occurred_at`` is a user-entered date-time; derive an indexed
    ``occurred_date`` in save()  -- FR-5.2, FR-5.10
  * AccountHead uniqueness: (family, name, parent) AND (family, name) where
    parent is null -- BR-7 (silence models.W036; enforce top-level in full_clean())
  * every editable model needs ``editable_by(member)``  -- BR-5
"""

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from django.core.validators import MinValueValidator
from datetime import timedelta


from core.models import TimeStampedModel
from families.models import Family, FamilyMember  # noqa: F401
from assets.models import BankAccount
MONEY = dict(max_digits=12, decimal_places=2)
  # noqa: F401

class TxnType(models.TextChoices):
    INCOME = "income", "Income"
    EXPENSE = "expense", "Expense"


class PaymentMethod(models.TextChoices):
    CASH = "cash", "Cash"
    BANK = "bank", "Bank transfer"
    CARD = "card", "Card"
    UPI = "upi", "UPI"
    WALLET = "wallet", "Wallet"
    CHEQUE = "cheque", "Cheque"
    OTHER = "other", "Other"


class AccountHead(TimeStampedModel):
    # TODO §12.4: family, name, kind (TxnType), parent (FK self), created_by, is_archived
    # TODO: Meta constraints (BR-7); clean() (parent same family + same kind);
    #       editable_by(member) -> True

    def __str__(self):
        return getattr(self, "name", f"AccountHead #{self.pk}")

    """A category, scoped per family and shared across all members."""

    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name="account_heads",null=True, blank=True)
    name = models.CharField(max_length=80)
    kind = models.CharField(max_length=10, choices=TxnType.choices)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="children"
    )
    created_by = models.ForeignKey(
        FamilyMember, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    is_archived = models.BooleanField(default=False)

    class Meta:
        ordering = ["kind", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["family", "name", "parent"], name="uniq_head_per_family"
            ),
            models.UniqueConstraint(
                fields=["family", "name"],
                condition=models.Q(parent__isnull=True),
                name="uniq_toplevel_head_per_family",
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_kind_display()})"

    def clean(self):
        super().clean()
        if self.parent_id:
            if self.parent.family_id != self.family_id:
                raise ValidationError({"parent": "Parent head must be in the same family."})
            if self.parent.kind != self.kind:
                raise ValidationError({"parent": "Parent head must be the same kind."})

    def editable_by(self, member):
        return True  # any active member may manage account heads




class TransactionQuerySet(models.QuerySet):
    """Custom QuerySet for Transaction model. Provides additional methods for
    filtering transactions based on type, member, and period."""

    def income(self):
        return self.filter(txn_type=TxnType.INCOME)

    def expense(self):
        return self.filter(txn_type=TxnType.EXPENSE)

    def for_member(self, member):
        return self.filter(member=member)

    def in_period(self, period):
        if not period.is_bounded:
            return self
        return self.filter(occurred_date__range=(period.start, period.end))

    
class Transaction(TimeStampedModel):
    # TODO §12.5: family, member (PROTECT), recorded_by (PROTECT), txn_type,
    #             account_head (PROTECT), amount, occurred_at, occurred_date
    #             (editable=False, db_index=True), description, merchant_or_source,
    #             payment_method, bank_account (assets.BankAccount, SET_NULL),
    #             is_recurring, recurring_template (SET_NULL), attachment
    # TODO: Meta ordering [-occurred_at] + the two composite indexes (§12.5)
    # TODO: custom QuerySet (income/expense/for_member/in_period)
    # TODO: clean() (BR-6, BR-15); save() (derive occurred_date);
    #       signed_amount; editable_by(member)

    def __str__(self):
        return f"Transaction #{self.pk}"

    """A single income or expense event.

    ``member`` = who earned/spent it (attribution).
    ``recorded_by`` = who entered it (audit); set from the acting user.
    """

    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name="transactions",null=True, blank=True)
    member = models.ForeignKey(
        FamilyMember, on_delete=models.PROTECT, related_name="transactions"
    )
    recorded_by = models.ForeignKey(
        FamilyMember, on_delete=models.PROTECT, related_name="recorded_transactions"
    )

    txn_type = models.CharField(max_length=10, choices=TxnType.choices)
    account_head = models.ForeignKey(
        AccountHead, on_delete=models.PROTECT, related_name="transactions"
    )
    amount = models.DecimalField(validators=[MinValueValidator(Decimal("0.01"))], **MONEY)

    occurred_at = models.DateTimeField(default=timezone.now)
    occurred_date = models.DateField(editable=False, db_index=True)

    description = models.TextField(blank=True)
    merchant_or_source = models.CharField(max_length=150, blank=True, db_index=True)
    payment_method = models.CharField(
        max_length=10, choices=PaymentMethod.choices, default=PaymentMethod.CASH
    )
    bank_account = models.ForeignKey(
        "assets.BankAccount",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="transactions",
    )

    is_recurring = models.BooleanField(default=False)
    recurring_template = models.ForeignKey(
        "ledger.RecurringTemplate",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="generated_transactions",
    )
    attachment = models.FileField(upload_to="receipts/%Y/%m/", null=True, blank=True)

    objects = TransactionQuerySet.as_manager()

    class Meta:
        ordering = ["-occurred_at"]
        indexes = [
            models.Index(fields=["family", "txn_type", "occurred_date"]),
            models.Index(fields=["member", "txn_type", "occurred_date"]),
        ]

    def __str__(self):
        return f"{self.get_txn_type_display()} {self.amount} · {self.merchant_or_source or self.account_head.name}"

    def clean(self):
        super().clean()
        if self.account_head_id and self.account_head.kind != self.txn_type:
            raise ValidationError(
                {"account_head": "Account head kind must match the transaction type."}
            )
        for field in ("member", "recorded_by"):
            obj = getattr(self, field, None)
            if obj and obj.family_id != self.family_id:
                print(obj.family_id, self.family_id)
                print("member validation") 
                raise ValidationError({field: "Must belong to this family."})
        if self.bank_account_id and self.bank_account.family_id != self.family_id:
            raise ValidationError({"bank_account": "Bank account must belong to this family."})

    def save(self, *args, **kwargs):
        if self.occurred_at:
            self.occurred_date = timezone.localtime(self.occurred_at).date()
        else:
            self.occurred_date = timezone.localdate()
        super().save(*args, **kwargs)

    @property
    def signed_amount(self) -> Decimal:
        return self.amount if self.txn_type == TxnType.INCOME else -self.amount

    def editable_by(self, member):
        return member.is_family_admin or member.pk in {self.member_id, self.recorded_by_id}


class RecurringTemplate(TimeStampedModel):
    class Frequency(models.TextChoices):
        WEEKLY = "weekly", "Weekly"
        MONTHLY = "monthly", "Monthly"
        QUARTERLY = "quarterly", "Quarterly"
        YEARLY = "yearly", "Yearly"

    # TODO §12.6: family, member, recorded_by, txn_type, account_head, amount,
    #             merchant_or_source, description, payment_method, bank_account,
    #             frequency, start_date, end_date, next_run_date, is_active
    # TODO: advance(from_date) per §16.3; editable_by(member)

    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name="recurring_templates")
    member = models.ForeignKey(
        FamilyMember, on_delete=models.PROTECT, related_name="recurring_templates"
    )
    recorded_by = models.ForeignKey(
        FamilyMember, on_delete=models.PROTECT, related_name="recorded_recurring_templates"
    )
    txn_type = models.CharField(max_length=10, choices=TxnType.choices)
    account_head = models.ForeignKey(
        AccountHead, on_delete=models.PROTECT, related_name="recurring_templates"
    )
    amount = models.DecimalField(validators=[MinValueValidator(Decimal("0.01"))], **MONEY)
    merchant_or_source = models.CharField(max_length=150, blank=True, db_index=True)
    description = models.TextField(blank=True)
    payment_method = models.CharField(
        max_length=10, choices=PaymentMethod.choices, default=PaymentMethod.CASH
    )
    bank_account = models.ForeignKey(
        "assets.BankAccount",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="recurring_templates",
    )
    frequency = models.CharField(max_length=10, choices=Frequency.choices)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    next_run_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)   

    class Meta:
        ordering = ["next_run_date"]

    def __str__(self):
        return f"{self.get_frequency_display()} {self.get_txn_type_display()} {self.amount}"

    def clean(self):
        super().clean()
        if self.account_head_id and self.account_head.kind != self.txn_type:
            raise ValidationError({"account_head": "Account head kind must match the type."})

    def advance(self, from_date):
        if self.frequency == self.Frequency.WEEKLY:
            return from_date + timedelta(days=7)
        month = from_date.month - 1
        step = {"monthly": 1, "quarterly": 3, "yearly": 12}[self.frequency]
        month += step
        year = from_date.year + month // 12
        month = month % 12 + 1
        day = min(from_date.day, [31, 29 if year % 4 == 0 else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
        return from_date.replace(year=year, month=month, day=day)

    def editable_by(self, member):
        return member.is_family_admin or member.pk in {self.member_id, self.recorded_by_id}
