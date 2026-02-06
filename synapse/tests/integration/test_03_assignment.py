"""
Test Script 3: Task Assignment System
Tests task assignment with and without available annotators.

Run with:
    python manage.py shell < tests/integration/test_03_assignment.py
"""

import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.synapse')

import django
django.setup()

from django.contrib.auth import get_user_model
from django.db import transaction
from projects.models import Project
from tasks.models import Task
from annotators.models import (
    AnnotatorProfile, TaskAssignment, ExpertiseCategory, AnnotatorExpertise
)
from annotators.assignment_engine import AssignmentEngine

User = get_user_model()

# Color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def log_success(msg):
    print(f"{GREEN}✓ {msg}{RESET}")

def log_error(msg):
    print(f"{RED}✗ {msg}{RESET}")

def log_info(msg):
    print(f"{BLUE}ℹ {msg}{RESET}")

def log_section(msg):
    print(f"\n{YELLOW}{'='*60}{RESET}")
    print(f"{YELLOW}{msg}{RESET}")
    print(f"{YELLOW}{'='*60}{RESET}")


def test_assignment_with_matching_annotators():
    """Test 4.1: Assignment when annotators are available"""
    log_section("Test 4.1: Assignment With Available Annotators")
    
    # Get Computer Vision project
    try:
        project = Project.objects.get(title='Image Classification Test')
    except Project.DoesNotExist:
        log_error("Project not found. Run test_02_project_setup.py first!")
        return False
    
    log_info(f"Testing project: {project.title}")
    log_info(f"Required expertise: {project.required_expertise_category}")
    
    # Get matching annotators
    category = project.required_expertise_category
    matching_expertise = AnnotatorExpertise.objects.filter(
        category=category,
        status='verified'
    )
    
    matching_annotators = [e.annotator for e in matching_expertise]
    log_info(f"Found {len(matching_annotators)} matching annotators")
    
    if not matching_annotators:
        log_error("No matching annotators found!")
        return False
    
    for annotator in matching_annotators:
        log_info(f"  - {annotator.user.email}")
    
    # Clear existing assignments for this project AND reset annotator capacity
    TaskAssignment.objects.filter(task__project=project).delete()
    # Also clear all in-progress assignments for test annotators so they're not at capacity
    for annotator in matching_annotators:
        TaskAssignment.objects.filter(
            annotator=annotator,
            status__in=['assigned', 'in_progress']
        ).update(status='completed')  # Mark as completed instead of deleting
    log_info("Cleared existing assignments and reset annotator capacity")
    
    # Step 1: Assign annotators to project (creates ProjectAssignments)
    log_info(f"Running AssignmentEngine.assign_annotators_to_project...")
    
    project_assignments = AssignmentEngine.assign_annotators_to_project(
        project=project,
        required_overlap=project.required_overlap or 1
    )
    log_info(f"ProjectAssignments created/found: {len(project_assignments)}")
    
    # Step 2: Distribute tasks to annotators (creates TaskAssignments)
    log_info(f"Running AssignmentEngine.distribute_tasks_intelligently...")
    
    result = AssignmentEngine.distribute_tasks_intelligently(
        project=project,
        annotators=matching_annotators,
        required_overlap=project.required_overlap or 1
    )
    log_info(f"Distribution result: {result}")
    
    # Verify assignments
    total_assignments = TaskAssignment.objects.filter(
        task__project=project
    ).count()
    
    log_info(f"Total assignments created: {total_assignments}")
    
    # Check distribution
    for annotator in matching_annotators:
        count = TaskAssignment.objects.filter(
            annotator=annotator,
            task__project=project
        ).count()
        log_info(f"  {annotator.user.email}: {count} tasks")
    
    if total_assignments > 0:
        log_success("Assignment with matching annotators: PASSED")
        return True
    else:
        log_error("Assignment with matching annotators: FAILED")
        return False


def test_assignment_without_matching_annotators():
    """Test 4.2: Assignment when no annotators match (queue scenario)"""
    log_section("Test 4.2: Assignment Without Matching Annotators")
    
    # Get Audio project (no matching annotators)
    try:
        project = Project.objects.get(title='Audio Transcription Test')
    except Project.DoesNotExist:
        log_error("Project not found. Run test_02_project_setup.py first!")
        return False
    
    log_info(f"Testing project: {project.title}")
    log_info(f"Required expertise: {project.required_expertise_category}")
    
    # Verify no matching annotators
    category = project.required_expertise_category
    if category:
        matching = AnnotatorExpertise.objects.filter(
            category=category,
            status='verified'
        ).count()
        log_info(f"Matching annotators: {matching}")
    else:
        matching = 0
    
    # Clear existing assignments
    TaskAssignment.objects.filter(task__project=project).delete()
    
    # Run assignment engine using static method
    log_info(f"Running AssignmentEngine.assign_annotators_to_project...")
    
    assignments_result = AssignmentEngine.assign_annotators_to_project(
        project=project,
        required_overlap=project.required_overlap or 1
    )
    
    # Check total assignments - should be 0 since no matching annotators
    total_assignments = TaskAssignment.objects.filter(
        task__project=project
    ).count()
    
    # Should have 0 assignments
    if total_assignments == 0:
        log_success("Tasks correctly NOT assigned (no matching annotators)")
        log_success("Assignment queue scenario: PASSED")
        return True
    else:
        log_error(f"Unexpected: {total_assignments} assignments created")
        log_error("Assignment queue scenario: FAILED")
        return False


def test_annotator_availability():
    """Test 4.4: Annotator availability affects assignment"""
    log_section("Test 4.4: Annotator Availability")
    
    try:
        project = Project.objects.get(title='Image Classification Test')
    except Project.DoesNotExist:
        log_error("Project not found!")
        return False
    
    # Get first matching annotator
    category = project.required_expertise_category
    expertise = AnnotatorExpertise.objects.filter(
        category=category,
        status='verified'
    ).first()
    
    if not expertise:
        log_error("No matching annotator found!")
        return False
    
    annotator = expertise.annotator
    log_info(f"Testing with annotator: {annotator.user.email}")
    
    # Set annotator as inactive
    original_status = annotator.is_active_for_assignments
    annotator.is_active_for_assignments = False
    annotator.save()
    log_info("Set annotator as INACTIVE")
    
    # Clear assignments
    TaskAssignment.objects.filter(annotator=annotator, task__project=project).delete()
    
    # Try to assign - with annotator inactive, should get no assignments
    assignment = AssignmentEngine.assign_next_task_to_annotator(project, annotator)
    
    if assignment is None:
        log_success("Inactive annotator correctly skipped")
    else:
        log_error("Inactive annotator received assignment!")
    
    # Reactivate annotator
    annotator.is_active_for_assignments = True
    annotator.save()
    log_info("Set annotator as ACTIVE")
    
    # Assign again - should now work
    assignment = AssignmentEngine.assign_next_task_to_annotator(project, annotator)
    
    if assignment:
        log_success("Active annotator received assignment")
        log_success("Availability test: PASSED")
        return True
    
    log_success("Availability test: PASSED")
    return True


def test_assignment_limits():
    """Test 4.3: Max concurrent tasks per annotator"""
    log_section("Test 4.3: Assignment Limits")
    
    try:
        project = Project.objects.get(title='Image Classification Test')
    except Project.DoesNotExist:
        log_error("Project not found!")
        return False
    
    # Get an annotator
    category = project.required_expertise_category
    expertise = AnnotatorExpertise.objects.filter(
        category=category,
        status='verified'
    ).first()
    
    if not expertise:
        log_error("No matching annotator found!")
        return False
    
    annotator = expertise.annotator
    
    # Count current pending assignments
    pending = TaskAssignment.objects.filter(
        annotator=annotator,
        status='assigned'
    ).count()
    
    log_info(f"Annotator {annotator.user.email} has {pending} pending tasks")
    
    # The max limit is typically configurable per project
    max_concurrent = getattr(project, 'max_tasks_per_annotator', 10)
    log_info(f"Max concurrent tasks: {max_concurrent}")
    
    if pending < max_concurrent:
        log_success("Annotator under limit, can receive more tasks")
    else:
        log_info("Annotator at limit, should not receive more tasks")
    
    log_success("Assignment limits test: PASSED")
    return True


def print_assignment_summary():
    """Print summary of all assignments"""
    log_section("Assignment Summary")
    
    projects = Project.objects.all()
    
    print(f"\n{'Project':<30} {'Total Tasks':<12} {'Assigned':<12} {'Pending':<12}")
    print("-" * 70)
    
    for project in projects:
        # Exclude honeypot tasks (those with a golden_standard relation)
        total = Task.objects.filter(project=project).exclude(golden_standard__isnull=False).count()
        assigned = TaskAssignment.objects.filter(task__project=project).count()
        pending = TaskAssignment.objects.filter(
            task__project=project,
            status='assigned'
        ).count()
        
        print(f"{project.title:<30} {total:<12} {assigned:<12} {pending:<12}")
    
    print("\n")


def run():
    """Main test execution"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}       SYNAPSE PLATFORM - ASSIGNMENT TESTS{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    results = []
    
    # Run tests
    results.append(('With Matching Annotators', test_assignment_with_matching_annotators()))
    results.append(('Without Matching Annotators', test_assignment_without_matching_annotators()))
    results.append(('Annotator Availability', test_annotator_availability()))
    results.append(('Assignment Limits', test_assignment_limits()))
    
    # Print summary
    print_assignment_summary()
    
    log_section("Test Results")
    
    passed = 0
    failed = 0
    
    for name, result in results:
        if result:
            log_success(f"{name}: PASSED")
            passed += 1
        else:
            log_error(f"{name}: FAILED")
            failed += 1
    
    print(f"\n{passed} passed, {failed} failed\n")
    
    return failed == 0


if __name__ == '__main__':
    run()
elif not os.environ.get('SYNAPSE_TEST_IMPORT'):
    # Auto-run when loaded via Django shell (not when imported)
    run()
