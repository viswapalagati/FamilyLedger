"""``manage.py seed_demo`` — SKELETON.

Implement per §18 (Seed / Demo Data):
  * 3 families, 2-5 members each, a mix of has-login / no-login, one admin each
  * every login uses password ``Test@123``
  * one family on a non-April financial year
  * account heads + ~6-8 months of transactions + a bank account and a digital
    asset per logged-in member + one physical asset + one owed_by_us liability +
    one monthly recurring template per family
  * ``--wipe`` clears demo data first; idempotent per family
  * console output must be ASCII-only (Windows cp1252)
"""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create 3 demo families with members, transactions and assets (§18)."

    def add_arguments(self, parser):
        parser.add_argument("--wipe", action="store_true", help="Delete demo data first.")

    def handle(self, *args, **options):
        raise NotImplementedError("Implement seed_demo per §18")
