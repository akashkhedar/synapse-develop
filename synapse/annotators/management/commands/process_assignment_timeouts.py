"""
Management command to process assignment timeouts.

Processes both annotator assignment timeouts and expert review timeouts.
Should be run periodically (e.g., every hour via cron).

Usage:
    python manage.py process_assignment_timeouts
    python manage.py process_assignment_timeouts --project-id=123
    python manage.py process_assignment_timeouts --annotators-only
    python manage.py process_assignment_timeouts --experts-only
"""

from django.core.management.base import BaseCommand, CommandError
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Process timed out annotator assignments and expert reviews'

    def add_arguments(self, parser):
        parser.add_argument(
            '--project-id',
            type=int,
            help='Only process timeouts for a specific project',
        )
        parser.add_argument(
            '--annotators-only',
            action='store_true',
            help='Only process annotator assignment timeouts',
        )
        parser.add_argument(
            '--experts-only',
            action='store_true',
            help='Only process expert review timeouts',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without making changes',
        )

    def handle(self, *args, **options):
        project_id = options.get('project_id')
        annotators_only = options.get('annotators_only')
        experts_only = options.get('experts_only')
        dry_run = options.get('dry_run')
        
        project = None
        if project_id:
            from projects.models import Project
            try:
                project = Project.objects.get(id=project_id)
                self.stdout.write(f"Processing timeouts for project: {project.title}")
            except Project.DoesNotExist:
                raise CommandError(f"Project {project_id} not found")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - No changes will be made"))
            self._show_pending_timeouts(project, annotators_only, experts_only)
            return
        
        results = {}
        
        # Process annotator timeouts
        if not experts_only:
            self.stdout.write("Processing annotator assignment timeouts...")
            results['annotators'] = self._process_annotator_timeouts(project)
        
        # Process expert timeouts
        if not annotators_only:
            self.stdout.write("Processing expert review timeouts...")
            results['experts'] = self._process_expert_timeouts(project)
        
        # Summary
        self.stdout.write(self.style.SUCCESS("\n=== Timeout Processing Complete ==="))
        
        if 'annotators' in results:
            r = results['annotators']
            self.stdout.write(f"Annotators: processed (check logs for details)")
        
        if 'experts' in results:
            r = results['experts']
            self.stdout.write(
                f"Experts: {r.get('extended', 0)} extended, "
                f"{r.get('released', 0)} released, "
                f"{r.get('marked_inactive', 0)} marked inactive"
            )
    
    def _process_annotator_timeouts(self, project):
        """Process annotator assignment timeouts"""
        from annotators.assignment_engine import DynamicAssignmentEngine
        
        try:
            DynamicAssignmentEngine.check_and_process_timeouts(project=project)
            return {'success': True}
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error: {e}"))
            return {'success': False, 'error': str(e)}
    
    def _process_expert_timeouts(self, project):
        """Process expert review timeouts"""
        from annotators.expert_assignment_engine import ExpertAssignmentEngine
        
        try:
            result = ExpertAssignmentEngine.check_and_process_timeouts(project=project)
            return result
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error: {e}"))
            return {'success': False, 'error': str(e)}
    
    def _show_pending_timeouts(self, project, annotators_only, experts_only):
        """Show pending timeouts without processing"""
        from datetime import timedelta
        from django.utils import timezone
        from annotators.models import TaskAssignment, ExpertReviewTask
        from annotators.assignment_engine import ASSIGNMENT_TIMEOUT_HOURS
        from annotators.expert_assignment_engine import EXPERT_REVIEW_TIMEOUT_HOURS
        
        annotator_cutoff = timezone.now() - timedelta(hours=ASSIGNMENT_TIMEOUT_HOURS)
        expert_cutoff = timezone.now() - timedelta(hours=EXPERT_REVIEW_TIMEOUT_HOURS)
        
        if not experts_only:
            # Count annotator timeouts
            query = TaskAssignment.objects.filter(
                status='assigned',
                assigned_at__lt=annotator_cutoff,
            )
            if project:
                query = query.filter(task__project=project)
            
            count = query.count()
            self.stdout.write(f"Annotator assignments pending timeout: {count}")
        
        if not annotators_only:
            # Count expert timeouts
            query = ExpertReviewTask.objects.filter(
                status__in=['pending', 'in_review'],
                assigned_at__lt=expert_cutoff,
            )
            if project:
                query = query.filter(task__project=project)
            
            count = query.count()
            self.stdout.write(f"Expert reviews pending timeout: {count}")
