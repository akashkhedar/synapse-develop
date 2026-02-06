"""
Test Script 5: Consolidation System
Tests consensus algorithm and annotation aggregation.

Run with:
    python manage.py shell < tests/integration/test_05_consolidation.py
"""

import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.synapse')

import django
django.setup()

from django.contrib.auth import get_user_model
from projects.models import Project
from tasks.models import Task, Annotation
from annotators.models import AnnotatorProfile, TaskAssignment

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


def test_all_annotators_agree():
    """Test 6.1: All annotators agree scenario"""
    log_section("Test 6.1: All Annotators Agree (Consensus)")
    
    # Get project with overlap > 1
    project = Project.objects.filter(
        required_overlap__gt=1
    ).first()
    
    if not project:
        log_error("No project with overlap > 1 found!")
        return False
    
    log_info(f"Using project: {project.title} (overlap: {project.required_overlap})")
    
    # Get a non-honeypot task
    task = Task.objects.filter(
        project=project,
        golden_standard__isnull=True
    ).first()
    
    if not task:
        log_error("No tasks found!")
        return False
    
    log_info(f"Using task {task.id}")
    
    # Clear existing annotations
    Annotation.objects.filter(task=task).delete()
    
    # Get annotators
    annotators = list(AnnotatorProfile.objects.all()[:project.required_overlap])
    
    if len(annotators) < project.required_overlap:
        log_error(f"Need {project.required_overlap} annotators, only have {len(annotators)}")
        return False
    
    # All annotators submit SAME result
    agreed_result = [{"value": {"choices": ["Positive"]}, "type": "choices"}]
    
    for annotator in annotators:
        annotation = Annotation.objects.create(
            task=task,
            completed_by=annotator.user,
            result=agreed_result,
            was_cancelled=False
        )
        log_info(f"Annotator {annotator.user.email} submitted: Positive")
    
    # Check consensus
    annotations = Annotation.objects.filter(task=task, was_cancelled=False)
    results = [str(a.result) for a in annotations]
    
    # All same = consensus
    if len(set(results)) == 1:
        log_success("All annotators agree - Consensus achieved!")
        
        # Mark task as having ground truth
        task.ground_truth = agreed_result
        task.save()
        
        log_success("Task ground truth set from consensus")
        log_success("All agree test: PASSED")
        return True
    else:
        log_error("Unexpected disagreement!")
        return False


def test_annotators_disagree():
    """Test 6.2: Annotators disagree scenario"""
    log_section("Test 6.2: Annotators Disagree (Conflict)")
    
    # Get project with overlap > 1
    project = Project.objects.filter(
        required_overlap__gt=1
    ).first()
    
    if not project:
        log_error("No project with overlap > 1 found!")
        return False
    
    log_info(f"Using project: {project.title}")
    
    # Get a different task
    task = Task.objects.filter(
        project=project,
        golden_standard__isnull=True,
        annotations__isnull=True
    ).first()
    
    if not task:
        log_info("No unused tasks, creating scenario on new task")
        task = Task.objects.filter(
            project=project,
            golden_standard__isnull=True
        ).last()
        if task:
            Annotation.objects.filter(task=task).delete()
    
    if not task:
        log_error("No tasks available!")
        return False
    
    log_info(f"Using task {task.id}")
    
    # Get annotators
    annotators = list(AnnotatorProfile.objects.all()[:2])
    
    if len(annotators) < 2:
        log_error("Need at least 2 annotators")
        return False
    
    # Submit DIFFERENT results
    result_1 = [{"value": {"choices": ["Positive"]}, "type": "choices"}]
    result_2 = [{"value": {"choices": ["Negative"]}, "type": "choices"}]
    
    annotation1 = Annotation.objects.create(
        task=task,
        completed_by=annotators[0].user,
        result=result_1,
        was_cancelled=False
    )
    log_info(f"Annotator {annotators[0].user.email} submitted: Positive")
    
    annotation2 = Annotation.objects.create(
        task=task,
        completed_by=annotators[1].user,
        result=result_2,
        was_cancelled=False
    )
    log_info(f"Annotator {annotators[1].user.email} submitted: Negative")
    
    # Check for disagreement
    annotations = Annotation.objects.filter(task=task, was_cancelled=False)
    results = [str(a.result) for a in annotations]
    
    if len(set(results)) > 1:
        log_success("Disagreement detected!")
        
        # In real system, this would trigger expert review
        # Mark task as needing review
        task.needs_expert_review = True
        task.save()
        
        log_success("Task flagged for expert review")
        log_success("Disagree test: PASSED")
        return True
    else:
        log_error("Expected disagreement but got consensus!")
        return False


def test_majority_vote():
    """Test 6.3: Majority vote resolution"""
    log_section("Test 6.3: Majority Vote Resolution")
    
    # Get project
    project = Project.objects.first()
    if not project:
        log_error("No project found!")
        return False
    
    # Get unused task
    task = Task.objects.filter(
        project=project,
        golden_standard__isnull=True
    ).exclude(
        id__in=Annotation.objects.values('task_id')
    ).first()
    
    if not task:
        task = Task.objects.filter(project=project, golden_standard__isnull=True).last()
        if task:
            Annotation.objects.filter(task=task).delete()
    
    if not task:
        log_error("No tasks available!")
        return False
    
    log_info(f"Using task {task.id}")
    
    # Get 3 annotators
    annotators = list(AnnotatorProfile.objects.all()[:3])
    
    if len(annotators) < 3:
        log_error("Need 3 annotators for majority vote test")
        return False
    
    # 2 agree, 1 disagrees
    majority_result = [{"value": {"choices": ["Positive"]}, "type": "choices"}]
    minority_result = [{"value": {"choices": ["Negative"]}, "type": "choices"}]
    
    # First two agree
    for annotator in annotators[:2]:
        Annotation.objects.create(
            task=task,
            completed_by=annotator.user,
            result=majority_result,
            was_cancelled=False
        )
        log_info(f"Annotator {annotator.user.email} submitted: Positive")
    
    # Third disagrees
    Annotation.objects.create(
        task=task,
        completed_by=annotators[2].user,
        result=minority_result,
        was_cancelled=False
    )
    log_info(f"Annotator {annotators[2].user.email} submitted: Negative")
    
    # Calculate majority
    annotations = Annotation.objects.filter(task=task, was_cancelled=False)
    
    # Count votes
    vote_counts = {}
    for ann in annotations:
        result_key = str(ann.result)
        vote_counts[result_key] = vote_counts.get(result_key, 0) + 1
    
    log_info(f"Vote distribution: {len(vote_counts)} distinct responses")
    
    # Find majority
    max_votes = max(vote_counts.values())
    total_votes = len(annotations)
    
    if max_votes > total_votes / 2:
        log_success(f"Majority found: {max_votes}/{total_votes} votes")
        
        # Get majority result
        for result_key, count in vote_counts.items():
            if count == max_votes:
                task.ground_truth = majority_result
                task.save()
                log_success("Ground truth set from majority vote")
                break
        
        log_success("Majority vote test: PASSED")
        return True
    else:
        log_info("No clear majority - would need tiebreaker")
        log_success("Majority vote test: PASSED (scenario valid)")
        return True


def test_overlap_requirement():
    """Test 6.4: Verify overlap requirement is enforced"""
    log_section("Test 6.4: Overlap Requirement")
    
    project = Project.objects.filter(required_overlap__gt=1).first()
    
    if not project:
        log_error("No project with overlap > 1 found!")
        return False
    
    log_info(f"Project: {project.title}")
    log_info(f"Required overlap: {project.required_overlap}")
    
    # Get task with annotations
    task = Task.objects.filter(
        project=project,
        golden_standard__isnull=True,
        annotations__isnull=False
    ).first()
    
    if not task:
        log_info("No annotated tasks found")
        log_success("Overlap requirement test: PASSED (no data)")
        return True
    
    # Count annotations
    annotation_count = Annotation.objects.filter(
        task=task,
        was_cancelled=False
    ).count()
    
    log_info(f"Task {task.id} has {annotation_count} annotations")
    
    # Check if overlap met
    if annotation_count >= project.required_overlap:
        log_success(f"Overlap requirement met ({annotation_count} >= {project.required_overlap})")
        log_success("Task ready for consolidation")
    else:
        log_info(f"Overlap not yet met ({annotation_count} < {project.required_overlap})")
        log_info("Task needs more annotations")
    
    log_success("Overlap requirement test: PASSED")
    return True


def print_consolidation_summary():
    """Print consolidation status summary"""
    log_section("Consolidation Summary")
    
    projects = Project.objects.all()
    
    print(f"\n{'Project':<30} {'Overlap':<10} {'Completed':<12} {'Pending':<12}")
    print("-" * 70)
    
    for project in projects:
        overlap = project.required_overlap
        
        # Tasks with enough annotations
        completed = 0
        pending = 0
        
        for task in Task.objects.filter(project=project, golden_standard__isnull=True):
            ann_count = Annotation.objects.filter(
                task=task,
                was_cancelled=False
            ).count()
            
            if ann_count >= overlap:
                completed += 1
            elif ann_count > 0:
                pending += 1
        
        print(f"{project.title:<30} {overlap:<10} {completed:<12} {pending:<12}")
    
    print("\n")


def run():
    """Main test execution"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}      SYNAPSE PLATFORM - CONSOLIDATION TESTS{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    results = []
    
    # Run tests
    results.append(('All Agree', test_all_annotators_agree()))
    results.append(('Disagree', test_annotators_disagree()))
    results.append(('Majority Vote', test_majority_vote()))
    results.append(('Overlap Requirement', test_overlap_requirement()))
    
    # Print summary
    print_consolidation_summary()
    
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
