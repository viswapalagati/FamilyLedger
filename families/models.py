"""families models — SKELETON.

Implement per §12.2 (Family) and §12.3 (FamilyMember). Enumerations are from
§24 and are given here to save you typing; the *fields* are yours to add.

Key points to honour:
  * Family.financial_year_start_month (1-12, default 4)  -- BR-9
  * FamilyMember.user is a nullable OneToOne to accounts.User
    (related_name="family_member")  -- null => no login
  * status active/inactive; members are soft-deleted, never removed  -- BR-8
  * helpers: Family.active_members; FamilyMember.initials / age / is_active_member
  * Meta: add ``ordering`` once the fields exist (Family by name, member by full_name)
"""

from datetime import date

from django.conf import settings  # noqa: F401
from django.db import models

from core.models import TimeStampedModel


class Family(TimeStampedModel):
    # TODO §12.2: name, financial_year_start_month, created_by (FK FamilyMember, null)

    name = models.CharField(max_length=120)
    financial_year_start_month = models.PositiveSmallIntegerField(
        default=4,
        help_text="Month the financial year begins (1=Jan … 12=Dec). India defaults to April.",
    )
    created_by = models.ForeignKey(
        "families.FamilyMember",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    class Meta:
        verbose_name_plural = "families"
        ordering = ["name"]

    def __str__(self):
        return self.name

    # TODO §12.2: active_members property, Meta.ordering = ["name"]
    @property
    def active_members(self):
        return self.members.filter(status=FamilyMember.Status.ACTIVE)
    

class FamilyMember(TimeStampedModel):
    class Relationship(models.TextChoices):    
        SELF = "self", "Self"
        SPOUSE = "spouse", "Spouse"
        FATHER = "father", "Father"
        MOTHER = "mother", "Mother"
        SON = "son", "Son"
        DAUGHTER = "daughter", "Daughter"
        BROTHER = "brother", "Brother"
        SISTER = "sister", "Sister"
        GRANDFATHER = "grandfather", "Grandfather"
        GRANDMOTHER = "grandmother", "Grandmother"
        FATHER_IN_LAW = "father_in_law", "Father-in-law"
        MOTHER_IN_LAW = "mother_in_law", "Mother-in-law"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"

    family = models.ForeignKey("Family", on_delete=models.CASCADE, related_name="members")
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="family_member",
    )
    full_name = models.CharField(max_length=120)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True, default="")
    date_of_birth = models.DateField(null=True, blank=True)
    relationship = models.CharField(
        max_length=40,
        choices=Relationship.choices,
        default=Relationship.OTHER,
    )
    has_login = models.BooleanField(default=False)
    is_family_admin = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    added_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="added_members",
    )

    class Meta:
        ordering = ["full_name"]

    @property
    def is_active_member(self):
        return self.status == self.Status.ACTIVE

    @property
    def initials(self):
        parts = [part for part in self.full_name.split() if part]
        if not parts:
            return ""
        return "".join(part[0].upper() for part in parts[:3])

    @property
    def age(self):
        if not self.date_of_birth:
            return None

        today = date.today()
        age = today.year - self.date_of_birth.year
        if (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day):
            age -= 1
        return age

    def __str__(self):
        return getattr(self, "full_name", f"Member #{self.pk}")
