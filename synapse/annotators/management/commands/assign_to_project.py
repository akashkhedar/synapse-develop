"""
Management command to assign annotators to projects (system-driven assignment)
"""
from django.core.management.base import BaseCommand
from annotators.models import AnnotatorProfile, ProjectAssignment
from annotators.assignment_engine import AssignmentEngine
from projects.models import Project
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Assign an annotator to a project and initial batch of tasks'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Annotator email address')
        parser.add_argument('project_id', type=int, help='Project ID to assign annotator to')
        parser.add_argument(
            '--batch-size',
            type=int,
            default=5,
            help='Number of tasks to pre-assign (default: 5)'
        )

    def handle(self, *args, **options):
        email = options['email']
        project_id = options['project_id']
        batch_size = options['batch_size']
        
        self.stdout.write(f'Assigning annotator {email} to project {project_id}...')
        
        # Get annotator
        try:
            profile = AnnotatorProfile.objects.select_related('user').get(user__email=email)
        except AnnotatorProfile.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Annotator with email {email} not found'))
            return
        
        # Check if approved
        if profile.status != 'approved':
            self.stdout.write(self.style.ERROR(
                f'Annotator {email} is not approved (status: {profile.status})'
            ))
            return
        
        # Get project
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Project {project_id} not found'))
            return
        
        # Create project assignment
        project_assignment, created = ProjectAssignment.objects.get_or_create(
            project=project,
            annotator=profile,
            defaults={
                'role': 'annotator',
                'active': True,
                'assigned_by': 'manual_command'
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(
                f'✓ Created project assignment for {email} → Project {project_id}'
            ))
        else:
            self.stdout.write(self.style.WARNING(
                f'Project assignment already exists for {email} → Project {project_id}'
            ))
        
        # Assign initial batch of tasks
        self.stdout.write(f'Assigning {batch_size} tasks...')
        assignments = AssignmentEngine.bulk_assign_tasks(project, profile, batch_size=batch_size)
        
        if assignments:
            self.stdout.write(self.style.SUCCESS(
                f'✓ Assigned {len(assignments)} tasks to {email}'
            ))
            for assignment in assignments:
                self.stdout.write(f'  - Task {assignment.task.id}')
        else:
            self.stdout.write(self.style.WARNING('No tasks were assigned (may be at capacity or no tasks available)'))
        
        # Show summary
        total_assigned = profile.task_assignments.filter(
            task__project=project
        ).count()
        
        self.stdout.write(self.style.SUCCESS(
            f'\nSummary:'
            f'\n  Annotator: {profile.user.email}'
            f'\n  Project: {project.title} (ID: {project.id})'
            f'\n  Total assigned tasks: {total_assigned}'
            f'\n  Project assignment status: {project_assignment.progress}'
        ))





