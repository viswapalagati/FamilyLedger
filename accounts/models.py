"""accounts.User — SKELETON (minimal, bootable).

The project needs *some* custom user for ``AUTH_USER_MODEL`` to resolve and for
``migrate`` / ``createsuperuser`` to work, so the bare essentials are provided.

Complete it per §12.1 (Data Model — accounts.User):
  * add ``first_name``, ``last_name``, ``phone``
  * add ``get_full_name()`` / ``get_short_name()``
  * add ``family_member_or_none`` (safe reverse one-to-one accessor) and a
    ``family`` property
  * the login form uses ``email`` as USERNAME_FIELD (already set)
"""

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=60, blank=True, default="")
    last_name = models.CharField(max_length=60, blank=True, default="")
    phone = models.CharField(max_length=30, blank=True, default="")
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        ordering = ["email"]

    def __str__(self):
        return self.email

    def get_full_name(self):
        full_name = " ".join(part for part in [self.first_name, self.last_name] if part)
        return full_name or self.email

    def get_short_name(self):
        return self.first_name or self.email

    @property
    def family_member_or_none(self):
        try:
            from families.models import FamilyMember
            return self.family_member
        except FamilyMember.DoesNotExist:
            return None

    @property
    def family(self):
        member = self.family_member_or_none
        return member.family if member else None
