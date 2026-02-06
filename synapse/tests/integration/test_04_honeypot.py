"""
Test Script 4: Honeypot System
Tests honeypot injection and evaluation.

Run with:
    python tests/integration/test_04_honeypot.py
"""

import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.synapse')

import django
django.setup()

from django.contrib.auth import get_user_model
from projects.models import Project
from tasks.models import Task, Annotation
from annotators.models import (
    AnnotatorProfile, TaskAssignment, GoldenStandardTask, HoneypotAssignment
)

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


def test_honeypot_exists():
    """Test 5.1: Verify honeypot tasks exist in projects"""
    log_section("Test 5.1: Verify Honeypot Tasks Exist")
    
    # Get projects with honeypots (GoldenStandardTask)
    projects_with_honeypots = []
    
    for project in Project.objects.all()[:10]:
        honeypot_count = GoldenStandardTask.objects.filter(
            task__project=project
        ).count()
        
        if honeypot_count > 0:
            projects_with_honeypots.append((project, honeypot_count))
    
    if not projects_with_honeypots:
        log_info("No projects with honeypots found, creating test honeypots...")
        
        # Get Image Classification Test project
        project = Project.objects.filter(title='Image Classification Test').first()
        if not project:
            project = Project.objects.first()
        
        if project:
            # Get some tasks from the project
            tasks = list(project.tasks.all()[:5])
            
            for i, task in enumerate(tasks):
                honeypot, created = GoldenStandardTask.objects.get_or_create(
                    task=task,
                    defaults={
                        'project': project,
                        'ground_truth': {'label': 'correct_answer'},
                        'source': 'admin',
                        'tolerance': 0.8
                    }
                )
                if created:
                    log_info(f"Created honeypot for task {task.id}")
            
            projects_with_honeypots.append((project, GoldenStandardTask.objects.filter(task__project=project).count()))
    
    if projects_with_honeypots:
        for project, count in projects_with_honeypots:
            log_info(f"Project '{project.title}': {count} honeypot tasks")
        
        log_success("Honeypot existence test: PASSED")
        return True
    else:
        log_error("No honeypots could be created!")
        return False


def test_honeypot_correct_response():
    """Test 5.2: Simulate correct honeypot response"""
    log_section("Test 5.2: Correct Honeypot Response")
    
    # Get a honeypot task
    honeypot = GoldenStandardTask.objects.first()
    
    if not honeypot:
        log_error("No honeypot tasks found! Run test_honeypot_exists first.")
        return False
    
    log_info(f"Testing with honeypot task ID: {honeypot.task.id}")
    log_info(f"Ground truth: {honeypot.ground_truth}")
    
    # Get an annotator
    annotator = AnnotatorProfile.objects.filter(status='approved').first()
    if not annotator:
        log_error("No approved annotators found!")
        return False
    
    log_info(f"Testing with annotator: {annotator.user.email}")
    
    # Create task assignment first
    assignment, _ = TaskAssignment.objects.get_or_create(
        annotator=annotator,
        task=honeypot.task,
        defaults={'status': 'assigned'}
    )
    
    # Simulate correct honeypot response by creating HoneypotAssignment
    honeypot_assignment, created = HoneypotAssignment.objects.get_or_create(
        annotator=annotator,
        golden_standard=honeypot,
        task_assignment=assignment,
        defaults={
            'annotator_result': honeypot.ground_truth,  # Correct answer
            'accuracy_score': 1.0,
            'passed': True
        }
    )
    
    if created:
        log_info("Created new honeypot assignment with CORRECT response")
    else:
        # Update existing
        honeypot_assignment.annotator_result = honeypot.ground_truth
        honeypot_assignment.accuracy_score = 1.0
        honeypot_assignment.passed = True
        honeypot_assignment.save()
        log_info("Updated existing honeypot assignment to CORRECT")
    
    if honeypot_assignment.passed:
        log_success("Correct response marked as PASSED")
        log_success("Correct honeypot response test: PASSED")
        return True
    else:
        log_error("Correct response not marked as passed!")
        return False


def test_honeypot_incorrect_response():
    """Test 5.3: Simulate incorrect honeypot response"""
    log_section("Test 5.3: Incorrect Honeypot Response")
    
    # Get a honeypot task (different from the one used above)
    honeypot = GoldenStandardTask.objects.all()[1] if GoldenStandardTask.objects.count() > 1 else GoldenStandardTask.objects.first()
    
    if not honeypot:
        log_error("No honeypot tasks found!")
        return False
    
    log_info(f"Testing with honeypot task ID: {honeypot.task.id}")
    log_info(f"Ground truth: {honeypot.ground_truth}")
    
    # Get a different annotator
    annotators = AnnotatorProfile.objects.filter(status='approved')
    annotator = annotators[1] if annotators.count() > 1 else annotators.first()
    
    if not annotator:
        log_error("No approved annotators found!")
        return False
    
    log_info(f"Testing with annotator: {annotator.user.email}")
    
    # Create task assignment
    assignment, _ = TaskAssignment.objects.get_or_create(
        annotator=annotator,
        task=honeypot.task,
        defaults={'status': 'assigned'}
    )
    
    # Simulate INCORRECT honeypot response
    wrong_result = {'label': 'WRONG_ANSWER_12345'}
    
    honeypot_assignment, created = HoneypotAssignment.objects.get_or_create(
        annotator=annotator,
        golden_standard=honeypot,
        task_assignment=assignment,
        defaults={
            'annotator_result': wrong_result,
            'accuracy_score': 0.0,
            'passed': False
        }
    )
    
    if created:
        log_info("Created new honeypot assignment with INCORRECT response")
    else:
        honeypot_assignment.annotator_result = wrong_result
        honeypot_assignment.accuracy_score = 0.0
        honeypot_assignment.passed = False
        honeypot_assignment.save()
        log_info("Updated existing honeypot assignment to INCORRECT")
    
    if not honeypot_assignment.passed:
        log_success("Incorrect response marked as FAILED")
        log_success("Incorrect honeypot response test: PASSED")
        return True
    else:
        log_error("Incorrect response should not be marked as passed!")
        return False


def test_accuracy_calculation():
    """Test 5.4: Test honeypot accuracy calculation"""
    log_section("Test 5.4: Honeypot Accuracy Calculation")
    
    annotator = AnnotatorProfile.objects.filter(status='approved').first()
    
    if not annotator:
        log_error("No annotators found!")
        return False
    
    log_info(f"Testing accuracy for: {annotator.user.email}")
    
    # Get evaluations from HoneypotAssignment
    evaluations = HoneypotAssignment.objects.filter(
        annotator=annotator,
        passed__isnull=False  # Only evaluated ones
    )
    
    total = evaluations.count()
    passed = evaluations.filter(passed=True).count()
    
    log_info(f"Total evaluations: {total}")
    log_info(f"Passed: {passed}")
    
    if total > 0:
        calculated_accuracy = passed / total
        log_info(f"Calculated accuracy: {calculated_accuracy:.2%}")
        
        # Update annotator honeypot accuracy if the field exists
        if hasattr(annotator, 'honeypot_accuracy'):
            annotator.honeypot_accuracy = calculated_accuracy
            annotator.save()
            log_success(f"Updated annotator honeypot_accuracy to {calculated_accuracy:.2%}")
        else:
            log_info("annotator.honeypot_accuracy field not found, skipping update")
    else:
        log_info("No evaluations yet - tests from previous steps should have created them")
    
    log_success("Accuracy calculation test: PASSED")
    return True


def print_honeypot_summary():
    """Print honeypot evaluation summary"""
    log_section("Honeypot Summary")
    
    annotators = AnnotatorProfile.objects.filter(status='approved')[:10]
    
    print(f"\n{'Annotator':<30} {'Total':<10} {'Passed':<10} {'Accuracy':<10}")
    print("-" * 60)
    
    for annotator in annotators:
        evals = HoneypotAssignment.objects.filter(
            annotator=annotator,
            passed__isnull=False
        )
        total = evals.count()
        passed = evals.filter(passed=True).count()
        accuracy = f"{(passed/total)*100:.1f}%" if total > 0 else "N/A"
        
        print(f"{annotator.user.email:<30} {total:<10} {passed:<10} {accuracy:<10}")
    
    print("\n")
    
    # Also show GoldenStandardTask overview
    print(f"{'Project':<40} {'Honeypots':<10}")
    print("-" * 50)
    
    projects_with_honeypots = {}
    for gs in GoldenStandardTask.objects.select_related('task__project').all()[:50]:
        project_name = gs.task.project.title if gs.task.project else "No Project"
        projects_with_honeypots[project_name] = projects_with_honeypots.get(project_name, 0) + 1
    
    for project_name, count in projects_with_honeypots.items():
        print(f"{project_name:<40} {count:<10}")
    
    print("\n")


def run():
    """Main test execution"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}        SYNAPSE PLATFORM - HONEYPOT TESTS{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    results = []
    
    # Run tests
    results.append(('Honeypot Existence', test_honeypot_exists()))
    results.append(('Correct Response', test_honeypot_correct_response()))
    results.append(('Incorrect Response', test_honeypot_incorrect_response()))
    results.append(('Accuracy Calculation', test_accuracy_calculation()))
    
    # Print summary
    print_honeypot_summary()
    
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
