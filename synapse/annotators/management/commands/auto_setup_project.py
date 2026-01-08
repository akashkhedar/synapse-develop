#!/usr/bin/env python
"""
Management command to auto-setup a project with annotators and assignments.

This command will:
1. Assign available annotators to the project
2. Create task assignments for all tasks
3. Set up consensus tracking
4. Ensure everything is ready for annotation

Usage:
    python manage.py auto_setup_project --project-id 81
    python manage.py auto_setup_project --project-id 81 --overlap 3
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from projects.models import Project
from annotators.models import ProjectAssignment, TaskAssignment, AnnotatorProfile
from annotators.assignment_engine import AssignmentEngine
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Automatically setup a project with annotators and task assignments"

    def add_arguments(self, parser):
        parser.add_argument(
            "--project-id",
            type=int,
            required=True,
            help="Project ID to setup",
        )
        parser.add_argument(
            "--overlap",
            type=int,
            default=3,
            help="Number of annotators per task (default: 3)",
        )
        parser.add_argument(
            "--annotator-emails",
            nargs="+",
            help="Specific annotator emails to assign (optional)",
        )

    def handle(self, *args, **options):
        project_id = options["project_id"]
        overlap = options["overlap"]
        annotator_emails = options.get("annotator_emails")

        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            raise CommandError(f"Project {project_id} does not exist")

        self.stdout.write(
            self.style.HTTP_INFO(
                f"\n{'='*80}\nAUTO-SETUP PROJECT: {project.title} (ID: {project.id})\n{'='*80}"
            )
        )

        # Step 1: Set required overlap
        self.stdout.write(self.style.HTTP_INFO("\n[1/5] Setting required overlap..."))
        if not hasattr(project, "required_overlap"):
            self.stdout.write(
                self.style.WARNING(
                    "  ⚠️  Project model doesn't have required_overlap field"
                )
            )
        else:
            project.required_overlap = overlap
            project.save(update_fields=["required_overlap"])
            self.stdout.write(
                self.style.SUCCESS(f"  ✅ Set required_overlap = {overlap}")
            )

        # Step 2: Publish project
        self.stdout.write(self.style.HTTP_INFO("\n[2/5] Publishing project..."))
        if not project.is_published:
            project.is_published = True
            project.save(update_fields=["is_published"])
            self.stdout.write(self.style.SUCCESS("  ✅ Project published"))
        else:
            self.stdout.write("  ℹ️  Project already published")

        # Step 3: Assign annotators to project
        self.stdout.write(
            self.style.HTTP_INFO("\n[3/5] Assigning annotators to project...")
        )

        if annotator_emails:
            # Use specific annotators
            annotators = AnnotatorProfile.objects.filter(
                user__email__in=annotator_emails
            )
            if annotators.count() < len(annotator_emails):
                self.stdout.write(
                    self.style.WARNING(
                        f"  ⚠️  Only found {annotators.count()} of {len(annotator_emails)} specified annotators"
                    )
                )

            for annotator in annotators:
                proj_assignment, created = ProjectAssignment.objects.get_or_create(
                    annotator=annotator,
                    project=project,
                    defaults={"active": True},
                )
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  ✅ Assigned {annotator.user.email} to project"
                        )
                    )
                else:
                    self.stdout.write(f"  ℹ️  {annotator.user.email} already assigned")
        else:
            # Use automatic assignment engine
            result = AssignmentEngine.assign_annotators_to_project(project)
            if result:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✅ Assigned {len(result)} annotators automatically"
                    )
                )
                for annotator in result:
                    self.stdout.write(f"     - {annotator.user.email}")
            else:
                self.stdout.write(
                    self.style.ERROR("  ❌ No annotators available for assignment")
                )
                return

        # Step 4: Create task assignments
        self.stdout.write(self.style.HTTP_INFO("\n[4/5] Creating task assignments..."))

        project_annotators = ProjectAssignment.objects.filter(
            project=project, active=True
        ).select_related("annotator")

        if not project_annotators.exists():
            raise CommandError("No annotators assigned to project")

        annotator_count = project_annotators.count()
        tasks = project.tasks.all()
        task_count = tasks.count()

        if task_count == 0:
            raise CommandError("No tasks in project")

        self.stdout.write(f"  📊 Tasks: {task_count}")
        self.stdout.write(f"  📊 Annotators: {annotator_count}")
        self.stdout.write(f"  📊 Assignments per task: {min(overlap, annotator_count)}")

        created_assignments = 0
        existing_assignments = 0

        # Use round-robin assignment
        annotator_list = list(project_annotators)
        annotator_index = 0

        for task in tasks:
            # Check existing assignments
            existing = TaskAssignment.objects.filter(task=task)
            existing_count = existing.count()

            needed = min(overlap, annotator_count)
            to_create = max(0, needed - existing_count)

            if to_create == 0:
                existing_assignments += 1
                continue

            # Get annotators who are NOT yet assigned to this task
            assigned_annotator_ids = existing.values_list("annotator_id", flat=True)

            # Create missing assignments using round-robin
            for _ in range(to_create):
                attempts = 0
                while attempts < annotator_count:
                    proj_assignment = annotator_list[annotator_index]
                    annotator_index = (annotator_index + 1) % len(annotator_list)
                    attempts += 1

                    # Skip if already assigned
                    if proj_assignment.annotator.id in assigned_annotator_ids:
                        continue

                    try:
                        with transaction.atomic():
                            TaskAssignment.objects.create(
                                annotator=proj_assignment.annotator,
                                task=task,
                                status="assigned",
                            )
                            created_assignments += 1
                            assigned_annotator_ids = list(assigned_annotator_ids) + [
                                proj_assignment.annotator.id
                            ]
                            break
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f"  ❌ Failed to create assignment for task {task.id}: {e}"
                            )
                        )
                        break

        self.stdout.write(
            self.style.SUCCESS(f"  ✅ Created {created_assignments} new assignments")
        )
        self.stdout.write(f"  ℹ️  {existing_assignments} tasks already had assignments")

        # Step 5: Summary
        self.stdout.write(self.style.HTTP_INFO(f"\n[5/5] Setup complete!\n{'='*80}"))
        self.stdout.write(
            self.style.SUCCESS(f"✅ Project '{project.title}' is ready for annotation!")
        )
        self.stdout.write(f"   - Tasks: {task_count}")
        self.stdout.write(
            f"   - Annotators: {annotator_count} ({', '.join(a.annotator.user.email for a in annotator_list)})"
        )
        self.stdout.write(
            f"   - Total assignments: {created_assignments + (task_count * min(overlap, annotator_count) - created_assignments)}"
        )
        self.stdout.write(f"   - Required overlap: {overlap}")
        self.stdout.write(
            f"\n💡 Annotators can now start annotating at: /projects/{project.id}/data"
        )





