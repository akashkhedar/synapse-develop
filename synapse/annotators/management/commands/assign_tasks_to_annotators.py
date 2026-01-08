"""
Management command to assign tasks to annotators for testing
Usage: python manage.py assign_tasks_to_annotators <annotator_email> <task_id1> <task_id2> ...
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from tasks.models import Task
from annotators.models import AnnotatorProfile, TaskAssignment

User = get_user_model()


class Command(BaseCommand):
    help = 'Assign tasks to an annotator'
    
    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Annotator email address')
        parser.add_argument('task_ids', nargs='+', type=int, help='Task IDs to assign')
    
    def handle(self, *args, **options):
        email = options['email']
        task_ids = options['task_ids']
        
        # Get annotator
        try:
            user = User.objects.get(email=email)
            profile = AnnotatorProfile.objects.get(user=user)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User with email {email} not found'))
            return
        except AnnotatorProfile.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Annotator profile not found for {email}'))
            return
        
        # Assign tasks
        created_count = 0
        already_assigned = 0
        not_found = []
        
        for task_id in task_ids:
            try:
                task = Task.objects.get(id=task_id)
                assignment, created = TaskAssignment.objects.get_or_create(
                    annotator=profile,
                    task=task,
                    defaults={'status': 'assigned'}
                )
                
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Task {task_id} assigned to {email}')
                    )
                    created_count += 1
                else:
                    self.stdout.write(
                        self.style.WARNING(f'⚠ Task {task_id} already assigned to {email}')
                    )
                    already_assigned += 1
            except Task.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'✗ Task {task_id} not found'))
                not_found.append(task_id)
        
        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write(f'Assignment Summary for {email}:')
        self.stdout.write(f'  New assignments: {created_count}')
        self.stdout.write(f'  Already assigned: {already_assigned}')
        if not_found:
            self.stdout.write(f'  Not found: {", ".join(map(str, not_found))}')
        self.stdout.write('='*50)





