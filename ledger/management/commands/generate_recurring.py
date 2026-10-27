"""``manage.py generate_recurring`` — SKELETON.

Implement per §16.3 (pseudocode + rules) and FR-10.2-10.5:
  * for each active template with next_run_date <= today, create one Transaction
    per missed occurrence and advance next_run_date
  * stop at end_date, then deactivate the template
  * generated transactions: is_recurring=True, linked to the template,
    recorded_by = the template's recorder
  * ``--dry-run`` reports the count and writes nothing
  * idempotent: running twice the same day creates nothing extra
  * schedule it via OS cron / Windows Task Scheduler (no Celery)
"""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create transactions for every recurring template that is due (§16.3)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Report only; write nothing.")

    def handle(self, *args, **options):
        raise NotImplementedError("Implement per §16.3")
