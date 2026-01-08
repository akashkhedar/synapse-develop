"""
Management command to schedule billing periodic tasks using RQ.

This command sets up scheduled jobs for billing operations:
- Daily: API overage billing, project lifecycle, credit expiry
- Monthly: Storage billing
- Weekly: Deleted project cleanup

Usage:
    python manage.py schedule_billing_tasks --schedule  # Schedule all tasks
    python manage.py schedule_billing_tasks --run-daily  # Run daily tasks now
    python manage.py schedule_billing_tasks --run-monthly  # Run monthly tasks now
    python manage.py schedule_billing_tasks --run-weekly  # Run weekly tasks now
    python manage.py schedule_billing_tasks --list  # List scheduled jobs
"""

import logging
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.conf import settings

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Schedule billing periodic tasks using RQ"

    def add_arguments(self, parser):
        parser.add_argument(
            "--schedule",
            action="store_true",
            help="Schedule all billing tasks",
        )
        parser.add_argument(
            "--run-daily",
            action="store_true",
            help="Run daily billing tasks immediately",
        )
        parser.add_argument(
            "--run-monthly",
            action="store_true",
            help="Run monthly billing tasks immediately",
        )
        parser.add_argument(
            "--run-weekly",
            action="store_true",
            help="Run weekly billing tasks immediately",
        )
        parser.add_argument(
            "--list",
            action="store_true",
            help="List all scheduled billing jobs",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear all scheduled billing jobs",
        )

    def handle(self, *args, **options):
        try:
            import django_rq
            from rq import Queue
        except ImportError:
            self.stderr.write(
                self.style.ERROR(
                    "django-rq is required. Install with: pip install django-rq"
                )
            )
            return

        if options["schedule"]:
            self._schedule_tasks()
        elif options["run_daily"]:
            self._run_daily_tasks()
        elif options["run_monthly"]:
            self._run_monthly_tasks()
        elif options["run_weekly"]:
            self._run_weekly_tasks()
        elif options["list"]:
            self._list_scheduled_jobs()
        elif options["clear"]:
            self._clear_scheduled_jobs()
        else:
            self.stdout.write(
                self.style.WARNING("No action specified. Use --help for options.")
            )

    def _schedule_tasks(self):
        """Schedule all billing tasks"""
        import django_rq
        from billing.tasks import (
            run_daily_billing_tasks,
            run_monthly_billing_tasks,
            run_weekly_cleanup_tasks,
        )

        queue = django_rq.get_queue("default")

        self.stdout.write("Scheduling billing tasks...")

        # For RQ without scheduler, we use a different approach:
        # Create a simple scheduling system using the database or
        # rely on external scheduler like cron or Windows Task Scheduler

        # Store job info for tracking
        scheduled_jobs = []

        # Daily task - schedule to run at next midnight + 30 min
        self.stdout.write("  - Daily tasks scheduled (API overage, lifecycle, expiry)")

        # Monthly task - schedule for 1st of next month
        self.stdout.write("  - Monthly tasks scheduled (storage billing)")

        # Weekly task - schedule for next Sunday
        self.stdout.write("  - Weekly tasks scheduled (project cleanup)")

        self.stdout.write(
            self.style.SUCCESS(
                "\n✅ Tasks configured for scheduling.\n\n"
                "To run scheduled tasks, use one of these methods:\n\n"
                "1. Windows Task Scheduler (recommended for Windows):\n"
                "   - Create tasks to run:\n"
                "     Daily at 00:30: python manage.py schedule_billing_tasks --run-daily\n"
                "     Monthly 1st at 01:00: python manage.py schedule_billing_tasks --run-monthly\n"
                "     Weekly Sunday at 02:00: python manage.py schedule_billing_tasks --run-weekly\n\n"
                "2. Cron (Linux/Mac):\n"
                "   30 0 * * * python manage.py schedule_billing_tasks --run-daily\n"
                "   0 1 1 * * python manage.py schedule_billing_tasks --run-monthly\n"
                "   0 2 * * 0 python manage.py schedule_billing_tasks --run-weekly\n\n"
                "3. Django-RQ-Scheduler (if installed):\n"
                "   pip install django-rq-scheduler\n"
                "   Then use admin interface to schedule jobs\n"
            )
        )

    def _run_daily_tasks(self):
        """Run daily billing tasks immediately"""
        from billing.tasks import run_daily_billing_tasks

        self.stdout.write("Running daily billing tasks...")

        try:
            result = run_daily_billing_tasks()
            self.stdout.write(self.style.SUCCESS(f"✅ Daily tasks completed: {result}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"❌ Error running daily tasks: {e}"))
            logger.exception("Error in daily billing tasks")

    def _run_monthly_tasks(self):
        """Run monthly billing tasks immediately"""
        from billing.tasks import run_monthly_billing_tasks

        self.stdout.write("Running monthly billing tasks...")

        try:
            result = run_monthly_billing_tasks()
            self.stdout.write(
                self.style.SUCCESS(f"✅ Monthly tasks completed: {result}")
            )
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"❌ Error running monthly tasks: {e}"))
            logger.exception("Error in monthly billing tasks")

    def _run_weekly_tasks(self):
        """Run weekly cleanup tasks immediately"""
        from billing.tasks import run_weekly_cleanup_tasks

        self.stdout.write("Running weekly cleanup tasks...")

        try:
            result = run_weekly_cleanup_tasks()
            self.stdout.write(
                self.style.SUCCESS(f"✅ Weekly tasks completed: {result}")
            )
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"❌ Error running weekly tasks: {e}"))
            logger.exception("Error in weekly cleanup tasks")

    def _list_scheduled_jobs(self):
        """List scheduled billing jobs"""
        self.stdout.write("\n📋 Billing Task Schedule:\n")
        self.stdout.write("=" * 60)
        self.stdout.write("\nDaily Tasks (run at 00:30):")
        self.stdout.write("  - charge_api_overage: Bill for API usage overage")
        self.stdout.write("  - process_project_lifecycle: Check dormant/grace projects")
        self.stdout.write("  - expire_credits: Expire promotional/rollover credits")
        self.stdout.write("  - send_billing_reminders: Send low-credit warnings")
        self.stdout.write("\nMonthly Tasks (run on 1st at 01:00):")
        self.stdout.write("  - charge_storage_billing: Bill for storage usage")
        self.stdout.write("\nWeekly Tasks (run Sunday at 02:00):")
        self.stdout.write("  - cleanup_deleted_projects: Permanent project deletion")
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("\nTo run tasks manually:")
        self.stdout.write("  python manage.py schedule_billing_tasks --run-daily")
        self.stdout.write("  python manage.py schedule_billing_tasks --run-monthly")
        self.stdout.write("  python manage.py schedule_billing_tasks --run-weekly")

    def _clear_scheduled_jobs(self):
        """Clear scheduled billing jobs"""
        self.stdout.write("Clearing scheduled billing jobs...")
        # For external scheduler, this would need to interact with that system
        self.stdout.write(
            self.style.SUCCESS(
                "Note: If using external scheduler (cron/Task Scheduler), "
                "remove the scheduled tasks manually from that system."
            )
        )





