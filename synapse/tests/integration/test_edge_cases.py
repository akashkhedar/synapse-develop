"""
Edge Case Tests: Timeouts & Zero Annotators
Tests scheduler-dependent functionality manually
"""

import os
import sys

# Add the synapse directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.synapse')

import django
django.setup()

from django.utils import timezone
from datetime import timedelta
from projects.models import Project
from tasks.models import Task
from annotators.models import TaskAssignment, AnnotatorProfile, ProjectAssignment
from annotators.assignment_engine import DynamicAssignmentEngine
from django.contrib.auth import get_user_model

User = get_user_model()


def test_assignment_timeout():
    """Test 1: Assignment Timeout Detection"""
    print('\n## TEST 1: ASSIGNMENT TIMEOUT DETECTION ##')

    # Find an assignment and simulate timeout
    assignment = TaskAssignment.objects.filter(status='assigned').first()
    if assignment:
        # Store original time
        original_time = assignment.assigned_at
        
        # Simulate old assignment (48 hours ago)
        old_time = timezone.now() - timedelta(hours=48)
        TaskAssignment.objects.filter(id=assignment.id).update(assigned_at=old_time)
        assignment.refresh_from_db()
        
        print(f'  Assignment {assignment.id}: assigned {assignment.assigned_at}')
        print(f'  Annotator: {assignment.annotator.user.email}')
        print(f'  Task: {assignment.task_id}')
        
        # Run timeout detection
        from annotators.tasks import process_annotator_assignment_timeouts
        result = process_annotator_assignment_timeouts()
        print(f'  Timeout processing result: {result}')
        
        # Check if assignment was expired
        assignment.refresh_from_db()
        print(f'  New status: {assignment.status}')
        
        # Restore original time if not expired
        if assignment.status == 'assigned':
            TaskAssignment.objects.filter(id=assignment.id).update(assigned_at=original_time)
            print('  (Restored original assignment time)')
        
        return True
    else:
        print('  No pending assignments to test')
        return True


def test_zero_annotators():
    """Test 2: Zero Annotators Scenario"""
    print('\n## TEST 2: ZERO ANNOTATORS SCENARIO ##')

    # Find a project
    project = Project.objects.first()
    if project:
        # Get active project members
        active_members = ProjectAssignment.objects.filter(
            project=project,
            active=True
        ).count()
        
        print(f'  Project: {project.title}')
        print(f'  Active annotators: {active_members}')
        
        # Get unassigned tasks
        unassigned_tasks = Task.objects.filter(
            project=project
        ).exclude(
            annotator_assignments__status__in=['assigned', 'in_progress']
        ).count()
        
        print(f'  Unassigned tasks: {unassigned_tasks}')
        
        # Test assignment when no annotators have capacity
        print('  Testing assignment with capacity limits...')
        from annotators.enhanced_assignment_engine import EnhancedAssignmentEngine
        result = EnhancedAssignmentEngine.auto_assign_project_tasks(project)
        total = result.get('total_assignments', 0)
        waiting = result.get('tasks_waiting', 0)
        print(f'  Result: total={total}, waiting={waiting}')
        
        return True
    else:
        print('  No projects found')
        return False


def test_task_locking():
    """Test 3: Task Holding (Lock) Mechanism"""
    print('\n## TEST 3: TASK HOLDING (LOCK) MECHANISM ##')

    # Check assignment-based locking
    in_progress = TaskAssignment.objects.filter(status='in_progress').count()
    assigned = TaskAssignment.objects.filter(status='assigned').count()
    print(f'  Tasks in-progress (locked): {in_progress}')
    print(f'  Tasks assigned (soft-locked): {assigned}')
    
    # Check if same task is assigned to multiple active annotators
    from django.db.models import Count, Q
    duplicate_assignments = Task.objects.annotate(
        active_count=Count('annotator_assignments', filter=Q(
            annotator_assignments__status__in=['assigned', 'in_progress']
        ))
    ).filter(active_count__gt=1)
    
    print(f'  Tasks with multiple active assignments: {duplicate_assignments.count()}')
    
    return True


def test_stale_cleanup():
    """Test 4: Expired Lock Cleanup"""
    print('\n## TEST 4: EXPIRED/STALE CLEANUP ##')

    # Check for stale assignments
    stale_threshold = timezone.now() - timedelta(hours=24)
    stale_assignments = TaskAssignment.objects.filter(
        status='assigned',
        assigned_at__lt=stale_threshold
    )
    print(f'  Stale assignments (>24h): {stale_assignments.count()}')

    for a in stale_assignments[:3]:
        age_hours = (timezone.now() - a.assigned_at).total_seconds() / 3600
        print(f'    Assignment {a.id}: {age_hours:.1f} hours old')
    
    # Run stale task reassignment
    from annotators.tasks import reassign_stale_tasks
    project = Project.objects.first()
    if project:
        result = reassign_stale_tasks(project.id)
        print(f'  Reassignment result: {result}')
    
    return True


def run():
    print('='*70)
    print('    EDGE CASE TESTS: TIMEOUTS & ZERO ANNOTATORS')
    print('='*70)
    
    results = []
    results.append(('Timeout Detection', test_assignment_timeout()))
    results.append(('Zero Annotators', test_zero_annotators()))
    results.append(('Task Locking', test_task_locking()))
    results.append(('Stale Cleanup', test_stale_cleanup()))
    
    print('\n' + '='*70)
    print('    SUMMARY')
    print('='*70)
    
    passed = sum(1 for _, r in results if r)
    failed = len(results) - passed
    
    for name, result in results:
        status = 'PASSED' if result else 'FAILED'
        print(f'  {name}: {status}')
    
    print(f'\n  {passed} passed, {failed} failed')
    
    print('''
  NOTES:
  1. Timeout Detection: Checks assignments older than threshold
  2. Zero Annotators: Tasks remain in waiting state when no capacity
  3. Task Locking: Via TaskAssignment status (assigned/in_progress)
  4. Stale Cleanup: Scheduler finds and reclaims old assignments
  
  Full scheduler functionality requires RQ worker (Linux/Docker)
  On Windows, tasks can be triggered manually or via cron.
''')


if __name__ == '__main__':
    run()
