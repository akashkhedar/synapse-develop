"""
Django management command to manually trigger auto-assignment for a project.

Usage:
    python manage.py trigger_auto_assignment --project-id 123
    python manage.py trigger_auto_assignment --project-id 123 --sync
"""

from django.core.management.base import BaseCommand, CommandError
from annotators.tasks import trigger_auto_assignment
from projects.models import Project
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Manually trigger automatic task assignment for a project"

    def add_arguments(self, parser):
        parser.add_argument(
            "--project-id",
            type=int,
            required=True,
            help="Project ID to assign annotators to",
        )
        parser.add_argument(
            "--sync",
            action="store_true",
            help="Run synchronously instead of as background job",
        )

    def handle(self, *args, **options):
        project_id = options["project_id"]

        try:
            # Verify project exists
            project = Project.objects.get(id=project_id)

            self.stdout.write(
                self.style.NOTICE(
                    f"Triggering auto-assignment for project {project_id}: {project.title}"
                )
            )

            # Trigger assignment
            if options["sync"]:
                # Run synchronously
                result = trigger_auto_assignment(project_id, async_mode=False)
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Assignment complete: {result}")
                )
            else:
                # Run as background job
                job = trigger_auto_assignment(project_id, async_mode=True)
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Queued assignment job: {job.id}")
                )

        except Project.DoesNotExist:
            raise CommandError(f"Project with id {project_id} does not exist")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error: {e}"))
            logger.exception("Error triggering auto-assignment")
            raise





