#!/usr/bin/env python
"""
Management command to ensure all tasks in a project have proper assignments.

Usage:
    python manage.py ensure_task_assignments --project-id 81
    python manage.py ensure_task_assignments --all
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from projects.models import Project
from annotators.models import ProjectAssignment, TaskAssignment
from tasks.models import Task
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Ensure all tasks have proper assignments for annotators"

    def add_arguments(self, parser):
        parser.add_argument(
            "--project-id",
            type=int,
            help="Specific project ID to process",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Process all projects",
        )
        parser.add_argument(
            "--fix",
            action="store_true",
            help="Actually create missing assignments (default is dry-run)",
        )

    def handle(self, *args, **options):
        project_id = options.get("project_id")
        process_all = options.get("all")
        fix_mode = options.get("fix")

        if not project_id and not process_all:
            raise CommandError("You must specify either --project-id or --all")

        # Get projects to process
        if project_id:
            try:
                projects = [Project.objects.get(id=project_id)]
            except Project.DoesNotExist:
                raise CommandError(f"Project {project_id} does not exist")
        else:
            projects = Project.objects.all()

        self.stdout.write(
            self.style.WARNING(
                f"{'DRY RUN' if not fix_mode else 'FIX MODE'} - Processing {len(projects)} project(s)..."
            )
        )

        total_missing = 0
        total_created = 0

        for project in projects:
            self.stdout.write(
                self.style.HTTP_INFO(
                    f"\n{'='*80}\nProject: {project.title} (ID: {project.id})\n{'='*80}"
                )
            )

            # Get project annotators
            project_annotators = ProjectAssignment.objects.filter(
                project=project, active=True
            ).select_related("annotator")

            if not project_annotators.exists():
                self.stdout.write(
                    self.style.WARNING(
                        f"  ⚠️  No annotators assigned to project {project.id}"
                    )
                )
                continue

            annotator_count = project_annotators.count()
            required_overlap = getattr(project, "required_overlap", 3)

            self.stdout.write(f"  Annotators assigned: {annotator_count}")
            self.stdout.write(f"  Required overlap: {required_overlap}")

            # Get all tasks
            tasks = project.tasks.all()
            task_count = tasks.count()

            if task_count == 0:
                self.stdout.write(self.style.WARNING("  No tasks in this project"))
                continue

            self.stdout.write(f"  Total tasks: {task_count}")

            # Check each task
            missing_count = 0
            created_count = 0

            for task in tasks:
                # Get existing assignments
                existing = TaskAssignment.objects.filter(task=task).count()
                needed = min(required_overlap, annotator_count)
                missing = max(0, needed - existing)

                if missing > 0:
                    missing_count += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"    Task {task.id}: {existing}/{needed} assignments "
                            f"(missing {missing})"
                        )
                    )

                    if fix_mode:
                        # Create missing assignments
                        # Get annotators who are NOT yet assigned to this task
                        assigned_annotators = TaskAssignment.objects.filter(
                            task=task
                        ).values_list("annotator_id", flat=True)

                        available_annotators = project_annotators.exclude(
                            annotator_id__in=assigned_annotators
                        )[:missing]

                        for proj_assignment in available_annotators:
                            try:
                                with transaction.atomic():
                                    TaskAssignment.objects.create(
                                        annotator=proj_assignment.annotator,
                                        task=task,
                                        status="assigned",
                                    )
                                    created_count += 1
                                    self.stdout.write(
                                        self.style.SUCCESS(
                                            f"      ✅ Created assignment for "
                                            f"{proj_assignment.annotator.user.email}"
                                        )
                                    )
                            except Exception as e:
                                self.stdout.write(
                                    self.style.ERROR(
                                        f"      ❌ Failed to create assignment: {e}"
                                    )
                                )

            total_missing += missing_count
            total_created += created_count

            self.stdout.write(
                self.style.SUCCESS(
                    f"  ✅ Summary: {missing_count} tasks with missing assignments"
                )
            )
            if fix_mode:
                self.stdout.write(
                    self.style.SUCCESS(f"  ✅ Created {created_count} assignments")
                )

        # Final summary
        self.stdout.write(self.style.SUCCESS(f"\n{'='*80}\nFINAL SUMMARY\n{'='*80}"))
        self.stdout.write(f"Total tasks with missing assignments: {total_missing}")
        if fix_mode:
            self.stdout.write(f"Total assignments created: {total_created}")
        else:
            self.stdout.write(
                self.style.WARNING(
                    "\nThis was a DRY RUN. Use --fix to actually create assignments."
                )
            )





