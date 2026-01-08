"""
Remove all project and task assignments for a given annotator, then reassign all projects and tasks.
"""
from django.core.management.base import BaseCommand
from annotators.models import AnnotatorProfile, ProjectAssignment, TaskAssignment
from projects.models import Project
from tasks.models import Task

class Command(BaseCommand):
    help = 'Remove all assignments for an annotator, then reassign all projects and tasks.'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Annotator email address')

    def handle(self, *args, **options):
        email = options['email']
        try:
            profile = AnnotatorProfile.objects.select_related('user').get(user__email=email)
        except AnnotatorProfile.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Annotator with email {email} not found'))
            return
        # Remove all assignments
        num_task_assignments = TaskAssignment.objects.filter(annotator=profile).delete()[0]
        num_project_assignments = ProjectAssignment.objects.filter(annotator=profile).delete()[0]
        self.stdout.write(self.style.WARNING(f'Removed {num_task_assignments} task assignments and {num_project_assignments} project assignments for {email}'))
        # Reassign all projects and tasks
        projects = Project.objects.all()
        total_projects = 0
        total_tasks = 0
        for project in projects:
            pa, _ = ProjectAssignment.objects.get_or_create(
                project=project,
                annotator=profile,
                defaults={'role': 'annotator', 'active': True, 'assigned_by': 'reset_reassign'}
            )
            tasks = Task.objects.filter(project=project)
            new_assignments = 0
            for task in tasks:
                ta, created = TaskAssignment.objects.get_or_create(
                    annotator=profile,
                    task=task,
                    defaults={'status': 'assigned'}
                )
                if created:
                    new_assignments += 1
                    total_tasks += 1
            if new_assignments > 0:
                pa.assigned_tasks += new_assignments
                pa.save(update_fields=["assigned_tasks"])
            total_projects += 1
        self.stdout.write(self.style.SUCCESS(f'Reassigned {total_projects} projects and {total_tasks} tasks to {email}'))





