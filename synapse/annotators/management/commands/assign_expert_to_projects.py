"""
Management command to assign an expert to all projects.
Usage: python manage.py assign_expert_to_projects --email expert@gmail.com
"""

from django.core.management.base import BaseCommand
from users.models import User
from projects.models import Project
from annotators.models import ExpertProfile, ExpertProjectAssignment


class Command(BaseCommand):
    help = "Assign an expert to all projects"

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            type=str,
            required=True,
            help="Email of the expert user",
        )
        parser.add_argument(
            "--project-id",
            type=int,
            help="Specific project ID to assign (optional, assigns to all if not provided)",
        )

    def handle(self, *args, **options):
        email = options["email"]
        project_id = options.get("project_id")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"User with email {email} not found"))
            return

        if not user.is_expert:
            self.stderr.write(self.style.ERROR(f"User {email} is not an expert"))
            return

        try:
            expert_profile = user.expert_profile
        except ExpertProfile.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"Expert profile not found for {email}"))
            return

        # Get projects to assign
        if project_id:
            projects = Project.objects.filter(id=project_id)
            if not projects.exists():
                self.stderr.write(
                    self.style.ERROR(f"Project with ID {project_id} not found")
                )
                return
        else:
            projects = Project.objects.all()

        assigned_count = 0
        for project in projects:
            assignment, created = ExpertProjectAssignment.objects.get_or_create(
                expert=expert_profile,
                project=project,
                defaults={
                    "is_active": True,
                    "review_all_tasks": True,
                },
            )

            if created:
                assigned_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Assigned expert {email} to project: {project.title}"
                    )
                )
            else:
                if not assignment.is_active:
                    assignment.is_active = True
                    assignment.save(update_fields=["is_active"])
                    assigned_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Reactivated assignment for project: {project.title}"
                        )
                    )
                else:
                    self.stdout.write(
                        f"Expert already assigned to project: {project.title}"
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone! Assigned {assigned_count} projects to expert {email}"
            )
        )
        self.stdout.write(
            f"Total projects assigned: {ExpertProjectAssignment.objects.filter(expert=expert_profile, is_active=True).count()}"
        )





