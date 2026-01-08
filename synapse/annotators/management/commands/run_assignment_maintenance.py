"""
Django management command to run periodic assignment maintenance.

Usage:
    python manage.py run_assignment_maintenance

This command should be run periodically (e.g., via cron) to:
- Reassign stale tasks
- Balance workload across annotators
- Assign new tasks to annotators who completed their batch
"""

from django.core.management.base import BaseCommand
from annotators.tasks import periodic_assignment_maintenance
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Run periodic assignment maintenance for all active projects"

    def add_arguments(self, parser):
        parser.add_argument(
            "--async",
            action="store_true",
            help="Run as background job instead of synchronously",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Starting assignment maintenance..."))

        try:
            if options["async"]:
                # Queue as background job
                job = periodic_assignment_maintenance.delay()
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Queued maintenance job: {job.id}")
                )
            else:
                # Run synchronously
                result = periodic_assignment_maintenance()
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Maintenance complete: {result}")
                )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error: {e}"))
            logger.exception("Error running assignment maintenance")
            raise





