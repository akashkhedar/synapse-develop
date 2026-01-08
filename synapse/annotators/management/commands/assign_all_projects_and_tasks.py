"""
Assign all projects and all tasks in each project to a given annotator.
"""

from django.core.management.base import BaseCommand
from annotators.models import AnnotatorProfile, ProjectAssignment, TaskAssignment
from projects.models import Project, ProjectMember
from tasks.models import Task
from annotators.assignment_engine import AssignmentEngine


class Command(BaseCommand):
    help = "Assign all projects and all tasks in each project to a given annotator."

    def add_arguments(self, parser):
        parser.add_argument("email", type=str, help="Annotator email address")

    def handle(self, *args, **options):
        email = options["email"]
        try:
            profile = AnnotatorProfile.objects.select_related("user").get(
                user__email=email
            )
        except AnnotatorProfile.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"Annotator with email {email} not found")
            )
            return
        if profile.status != "approved":
            self.stdout.write(
                self.style.ERROR(
                    f"Annotator {email} is not approved (status: {profile.status})"
                )
            )
            return
        projects = Project.objects.all()
        total_projects = 0
        total_tasks = 0
        for project in projects:
            # Add annotator as project member so they can see the project in the UI
            ProjectMember.objects.get_or_create(
                user=profile.user, project=project, defaults={"enabled": True}
            )
            self.stdout.write(
                self.style.SUCCESS(f"Added {email} as member of project {project.id}")
            )

            # Ensure project is published so annotators can see it
            if not project.is_published:
                project.is_published = True
                project.save(update_fields=["is_published"])
                self.stdout.write(self.style.SUCCESS(f"Published project {project.id}"))

            pa, _ = ProjectAssignment.objects.get_or_create(
                project=project,
                annotator=profile,
                defaults={
                    "role": "annotator",
                    "active": True,
                    "assigned_by": "manual_all",
                },
            )
            tasks = Task.objects.filter(project=project)
            num_tasks = tasks.count()
            self.stdout.write(
                self.style.WARNING(f"Project {project.id} has {num_tasks} tasks")
            )
            new_assignments = 0
            for task in tasks:
                ta, created = TaskAssignment.objects.get_or_create(
                    annotator=profile, task=task, defaults={"status": "assigned"}
                )
                if created:
                    new_assignments += 1
                    total_tasks += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Assigned task {task.id} to {profile.user.email}"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Task {task.id} already assigned to {profile.user.email} (status: {ta.status})"
                        )
                    )
            # Update assigned_tasks counter if any new assignments were made
            if new_assignments > 0:
                pa.assigned_tasks += new_assignments
                pa.save(update_fields=["assigned_tasks"])
            total_projects += 1
        self.stdout.write(
            self.style.SUCCESS(
                f"Assigned {total_projects} projects and {total_tasks} tasks to {email}"
            )
        )





