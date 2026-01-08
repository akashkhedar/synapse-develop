"""Management command to assign all tasks to a specific annotator"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from tasks.models import Task
from annotators.models import AnnotatorProfile, TaskAssignment

User = get_user_model()


class Command(BaseCommand):
    help = 'Assign all existing tasks to a specific annotator'

    def add_arguments(self, parser):
        parser.add_argument(
            'email',
            type=str,
            help='Email address of the annotator'
        )

    def handle(self, *args, **options):
        email = options['email']
        
        try:
            # Get the user and annotator profile
            user = User.objects.get(email=email)
            profile = AnnotatorProfile.objects.get(user=user)
            
            self.stdout.write(f'Found annotator: {user.get_full_name()} ({email})')
            
            # Get all tasks
            all_tasks = Task.objects.all()
            total_tasks = all_tasks.count()
            
            if total_tasks == 0:
                self.stdout.write(self.style.WARNING('No tasks found in the database'))
                return
            
            self.stdout.write(f'Found {total_tasks} tasks to assign')
            
            # Assign all tasks to this annotator
            assigned_count = 0
            skipped_count = 0
            
            for task in all_tasks:
                # Check if already assigned
                existing = TaskAssignment.objects.filter(
                    annotator=profile,
                    task=task
                ).exists()
                
                if existing:
                    skipped_count += 1
                    continue
                
                # Create assignment
                TaskAssignment.objects.create(
                    annotator=profile,
                    task=task,
                    status='assigned'
                )
                assigned_count += 1
            
            self.stdout.write(self.style.SUCCESS(
                f'\n✓ Successfully assigned {assigned_count} tasks to {email}'
            ))
            
            if skipped_count > 0:
                self.stdout.write(self.style.WARNING(
                    f'⊘ Skipped {skipped_count} tasks (already assigned)'
                ))
            
            self.stdout.write(self.style.SUCCESS(
                f'\nTotal assignments for this annotator: {TaskAssignment.objects.filter(annotator=profile).count()}'
            ))
            
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                f'✗ User with email {email} not found'
            ))
        except AnnotatorProfile.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                f'✗ User {email} is not registered as an annotator'
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'✗ Error: {str(e)}'
            ))





