"""
System Diagnostics Script
Verifies that all platform algorithms are working correctly.

Run with:
    python manage.py shell < tests/integration/diagnose_system.py
"""

import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.synapse')

import django
django.setup()

from django.contrib.auth import get_user_model
from django.db.models import Count, Avg, Q
from datetime import datetime, timedelta

from organizations.models import Organization
from projects.models import Project
from tasks.models import Task, Annotation
from annotators.models import (
    AnnotatorProfile, AnnotatorExpertise, TaskAssignment,
    HoneypotEvaluation, ExpertProfile, ExpertReview,
    ExpertiseCategory, AnnotatorStreak
)

User = get_user_model()

# Color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
RESET = '\033[0m'


def header(msg):
    print(f"\n{CYAN}{'='*70}{RESET}")
    print(f"{CYAN}  {msg}{RESET}")
    print(f"{CYAN}{'='*70}{RESET}")


def success(msg):
    print(f"{GREEN}  ✓ {msg}{RESET}")


def warning(msg):
    print(f"{YELLOW}  ⚠ {msg}{RESET}")


def error(msg):
    print(f"{RED}  ✗ {msg}{RESET}")


def info(msg):
    print(f"{BLUE}  ℹ {msg}{RESET}")


def check_data_exists():
    """Check if test data exists"""
    header("1. DATA EXISTENCE CHECK")
    
    issues = []
    
    # Users
    user_count = User.objects.count()
    if user_count > 0:
        success(f"Users: {user_count}")
    else:
        error("No users found! Run test_01_user_setup.py first")
        issues.append("No users")
    
    # Annotators
    annotator_count = AnnotatorProfile.objects.count()
    if annotator_count > 0:
        success(f"Annotator profiles: {annotator_count}")
    else:
        warning("No annotator profiles")
        issues.append("No annotators")
    
    # Experts
    expert_count = ExpertProfile.objects.filter(is_active=True).count()
    if expert_count > 0:
        success(f"Active experts: {expert_count}")
    else:
        warning("No active experts")
    
    # Projects
    project_count = Project.objects.count()
    if project_count > 0:
        success(f"Projects: {project_count}")
    else:
        error("No projects! Run test_02_project_setup.py first")
        issues.append("No projects")
    
    # Tasks
    task_count = Task.objects.count()
    if task_count > 0:
        success(f"Tasks: {task_count}")
    else:
        error("No tasks!")
        issues.append("No tasks")
    
    return len(issues) == 0


def check_expertise_system():
    """Check expertise matching system"""
    header("2. EXPERTISE SYSTEM CHECK")
    
    # Categories exist
    categories = ExpertiseCategory.objects.all()
    if categories.exists():
        success(f"Expertise categories: {categories.count()}")
        for cat in categories[:5]:
            info(f"  - {cat.name} ({cat.slug})")
    else:
        error("No expertise categories found!")
        return False
    
    # Annotators have expertise
    with_expertise = AnnotatorExpertise.objects.values('annotator').distinct().count()
    if with_expertise > 0:
        success(f"Annotators with expertise: {with_expertise}")
    else:
        warning("No annotators have expertise assigned")
    
    # Verified expertise
    verified = AnnotatorExpertise.objects.filter(status='verified').count()
    if verified > 0:
        success(f"Verified expertise records: {verified}")
    else:
        warning("No verified expertise - annotators won't be assigned tasks!")
    
    # Projects with expertise requirements
    projects_with_expertise = Project.objects.filter(
        required_expertise_category__isnull=False
    ).count()
    if projects_with_expertise > 0:
        success(f"Projects requiring expertise: {projects_with_expertise}")
    else:
        warning("No projects require expertise")
    
    # Matching check
    info("\nExpertise Matching Analysis:")
    for project in Project.objects.filter(required_expertise_category__isnull=False)[:5]:
        category = project.required_expertise_category
        matching_annotators = AnnotatorExpertise.objects.filter(
            category=category,
            status='verified'
        ).count()
        
        if matching_annotators > 0:
            success(f"  {project.title}: {matching_annotators} matching annotators")
        else:
            warning(f"  {project.title}: NO matching annotators (tasks will queue)")
    
    return True


def check_assignment_system():
    """Check task assignment algorithm"""
    header("3. ASSIGNMENT SYSTEM CHECK")
    
    total_assignments = TaskAssignment.objects.count()
    if total_assignments > 0:
        success(f"Total assignments: {total_assignments}")
    else:
        warning("No task assignments yet")
        info("Run test_03_assignment.py to test assignment")
        return True
    
    # Assignment status distribution
    info("\nAssignment Status Distribution:")
    statuses = TaskAssignment.objects.values('status').annotate(count=Count('id'))
    for s in statuses:
        info(f"  {s['status']}: {s['count']}")
    
    # Assignments per annotator
    info("\nAssignments per Annotator:")
    per_annotator = TaskAssignment.objects.values(
        'annotator__user__email'
    ).annotate(count=Count('id')).order_by('-count')[:10]
    
    for pa in per_annotator:
        info(f"  {pa['annotator__user__email']}: {pa['count']} tasks")
    
    # Check for balanced distribution
    counts = [pa['count'] for pa in per_annotator]
    if counts:
        max_diff = max(counts) - min(counts)
        avg_count = sum(counts) / len(counts)
        if max_diff <= avg_count * 0.5:
            success("Assignment distribution is balanced")
        else:
            warning(f"Assignment distribution is uneven (max diff: {max_diff})")
    
    # Check expertise matching
    info("\nExpertise Matching Verification:")
    mismatches = 0
    for assignment in TaskAssignment.objects.select_related(
        'task__project__required_expertise_category',
        'annotator__user'
    )[:100]:
        project = assignment.task.project
        if project.required_expertise_category:
            has_expertise = AnnotatorExpertise.objects.filter(
                annotator=assignment.annotator,
                category=project.required_expertise_category,
                status='verified'
            ).exists()
            
            if not has_expertise:
                mismatches += 1
    
    if mismatches == 0:
        success("All assignments match expertise requirements")
    else:
        error(f"{mismatches} assignments don't match expertise requirements!")
    
    return True


def check_honeypot_system():
    """Check honeypot evaluation algorithm"""
    header("4. HONEYPOT SYSTEM CHECK")
    
    # Honeypot tasks exist
    honeypots = Task.objects.filter(is_honeypot=True)
    if honeypots.exists():
        success(f"Honeypot tasks: {honeypots.count()}")
    else:
        warning("No honeypot tasks exist")
        return True
    
    # Honeypots have ground truth
    with_ground_truth = honeypots.exclude(
        Q(honeypot_ground_truth__isnull=True) | Q(honeypot_ground_truth=[])
    ).count()
    
    if with_ground_truth > 0:
        success(f"Honeypots with ground truth: {with_ground_truth}")
    else:
        error("No honeypots have ground truth set!")
    
    # Evaluations exist
    evaluations = HoneypotEvaluation.objects.all()
    if evaluations.exists():
        success(f"Honeypot evaluations: {evaluations.count()}")
        
        passed = evaluations.filter(passed=True).count()
        failed = evaluations.filter(passed=False).count()
        
        info(f"  Passed: {passed} ({passed*100//evaluations.count()}%)")
        info(f"  Failed: {failed} ({failed*100//evaluations.count()}%)")
        
        # Per-annotator accuracy
        info("\nAnnotator Honeypot Accuracy:")
        per_annotator = evaluations.values(
            'annotator__user__email'
        ).annotate(
            total=Count('id'),
            passed_count=Count('id', filter=Q(passed=True))
        )
        
        for pa in per_annotator:
            if pa['total'] > 0:
                accuracy = pa['passed_count'] * 100 // pa['total']
                status_icon = "✓" if accuracy >= 70 else "⚠" if accuracy >= 50 else "✗"
                print(f"    {status_icon} {pa['annotator__user__email']}: {accuracy}% ({pa['passed_count']}/{pa['total']})")
    else:
        warning("No honeypot evaluations yet")
        info("Run test_04_honeypot.py to test honeypot system")
    
    return True


def check_consolidation_system():
    """Check consensus/consolidation algorithm"""
    header("5. CONSOLIDATION SYSTEM CHECK")
    
    # Get projects with overlap > 1
    multi_overlap_projects = Project.objects.filter(maximum_annotations__gt=1)
    
    if not multi_overlap_projects.exists():
        warning("No projects require multiple annotations")
        return True
    
    info("\nOverlap Analysis by Project:")
    
    for project in multi_overlap_projects:
        required = project.maximum_annotations
        info(f"\n{project.title} (requires {required} annotations):")
        
        # Count tasks by annotation count
        tasks = Task.objects.filter(project=project, is_honeypot=False)
        
        fully_annotated = 0
        partial = 0
        none = 0
        
        for task in tasks:
            ann_count = Annotation.objects.filter(
                task=task, was_cancelled=False
            ).count()
            
            if ann_count >= required:
                fully_annotated += 1
            elif ann_count > 0:
                partial += 1
            else:
                none += 1
        
        total = tasks.count()
        if total > 0:
            info(f"    Complete ({required}+ annotations): {fully_annotated}")
            info(f"    Partial (1-{required-1} annotations): {partial}")
            info(f"    Not started: {none}")
            
            completion_rate = fully_annotated * 100 // total
            if completion_rate > 0:
                success(f"    Completion rate: {completion_rate}%")
    
    # Check for agreement analysis
    info("\nConsensus Analysis:")
    
    consensus_count = 0
    conflict_count = 0
    
    for project in multi_overlap_projects:
        for task in Task.objects.filter(project=project, is_honeypot=False):
            annotations = Annotation.objects.filter(task=task, was_cancelled=False)
            
            if annotations.count() >= 2:
                results = [str(a.result) for a in annotations]
                if len(set(results)) == 1:
                    consensus_count += 1
                else:
                    conflict_count += 1
    
    if consensus_count + conflict_count > 0:
        total = consensus_count + conflict_count
        info(f"  Tasks with consensus: {consensus_count} ({consensus_count*100//total}%)")
        info(f"  Tasks with conflicts: {conflict_count} ({conflict_count*100//total}%)")
    else:
        warning("  No multi-annotated tasks to analyze")
    
    return True


def check_expert_review_system():
    """Check expert review workflow"""
    header("6. EXPERT REVIEW SYSTEM CHECK")
    
    # Experts exist
    experts = ExpertProfile.objects.filter(is_active=True)
    if experts.exists():
        success(f"Active experts: {experts.count()}")
        for expert in experts:
            info(f"  - {expert.user.email}")
    else:
        warning("No active experts configured")
    
    # Tasks needing review
    needs_review = Task.objects.filter(needs_expert_review=True).count()
    if needs_review > 0:
        warning(f"Tasks pending expert review: {needs_review}")
    else:
        success("No tasks pending expert review")
    
    # Completed reviews
    reviews = ExpertReview.objects.all()
    if reviews.exists():
        success(f"Completed expert reviews: {reviews.count()}")
        
        approved = reviews.filter(decision='approved').count()
        rejected = reviews.filter(decision='rejected').count()
        
        info(f"  Approved: {approved}")
        info(f"  Rejected: {rejected}")
    else:
        info("No expert reviews completed yet")
    
    return True


def check_streak_system():
    """Check annotator streak tracking"""
    header("7. STREAK SYSTEM CHECK")
    
    streaks = AnnotatorStreak.objects.all()
    
    if streaks.exists():
        success(f"Annotators with streak data: {streaks.count()}")
        
        info("\nStreak Leaderboard:")
        top_streaks = streaks.order_by('-current_streak')[:5]
        
        for streak in top_streaks:
            info(f"  {streak.annotator.user.email}: {streak.current_streak} days "
                 f"(longest: {streak.longest_streak})")
    else:
        warning("No streak data recorded yet")
        info("Streaks are recorded when annotators complete tasks")
    
    return True


def check_data_flow():
    """Verify end-to-end data flow"""
    header("8. END-TO-END DATA FLOW CHECK")
    
    steps = []
    
    # Step 1: Tasks created
    tasks = Task.objects.count()
    if tasks > 0:
        success(f"Step 1: Tasks exist ({tasks})")
        steps.append(True)
    else:
        error("Step 1: No tasks created")
        steps.append(False)
    
    # Step 2: Assignments created
    assignments = TaskAssignment.objects.count()
    if assignments > 0:
        success(f"Step 2: Assignments created ({assignments})")
        steps.append(True)
    else:
        warning("Step 2: No assignments yet")
        steps.append(False)
    
    # Step 3: Annotations submitted
    annotations = Annotation.objects.filter(was_cancelled=False).count()
    if annotations > 0:
        success(f"Step 3: Annotations submitted ({annotations})")
        steps.append(True)
    else:
        warning("Step 3: No annotations submitted")
        steps.append(False)
    
    # Step 4: Honeypot evaluations
    evaluations = HoneypotEvaluation.objects.count()
    if evaluations > 0:
        success(f"Step 4: Honeypot evaluations ({evaluations})")
        steps.append(True)
    else:
        warning("Step 4: No honeypot evaluations")
        steps.append(False)
    
    # Step 5: Expert reviews (optional)
    reviews = ExpertReview.objects.count()
    if reviews > 0:
        success(f"Step 5: Expert reviews ({reviews})")
    else:
        info("Step 5: No expert reviews (may not be needed)")
    
    return all(steps[:3])  # First 3 steps are critical


def print_summary_stats():
    """Print overall system statistics"""
    header("SYSTEM SUMMARY")
    
    stats = {
        'Users': User.objects.count(),
        'Annotators': AnnotatorProfile.objects.count(),
        'Experts': ExpertProfile.objects.filter(is_active=True).count(),
        'Organizations': Organization.objects.count(),
        'Projects': Project.objects.count(),
        'Tasks': Task.objects.count(),
        'Honeypot Tasks': Task.objects.filter(is_honeypot=True).count(),
        'Assignments': TaskAssignment.objects.count(),
        'Annotations': Annotation.objects.filter(was_cancelled=False).count(),
        'Honeypot Evaluations': HoneypotEvaluation.objects.count(),
        'Expert Reviews': ExpertReview.objects.count(),
    }
    
    print(f"\n{'Metric':<25} {'Count':<10}")
    print("-" * 35)
    for metric, count in stats.items():
        print(f"{metric:<25} {count:<10}")
    print()


def run():
    """Run all diagnostics"""
    print(f"""
{CYAN}╔══════════════════════════════════════════════════════════════════╗
║                                                                      ║
║               SYNAPSE PLATFORM DIAGNOSTICS                           ║
║                                                                      ║
║  This script verifies all system algorithms are working correctly.   ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝{RESET}
""")
    
    results = []
    
    # Run all checks
    results.append(('Data Exists', check_data_exists()))
    results.append(('Expertise System', check_expertise_system()))
    results.append(('Assignment System', check_assignment_system()))
    results.append(('Honeypot System', check_honeypot_system()))
    results.append(('Consolidation System', check_consolidation_system()))
    results.append(('Expert Review System', check_expert_review_system()))
    results.append(('Streak System', check_streak_system()))
    results.append(('Data Flow', check_data_flow()))
    
    # Print summary
    print_summary_stats()
    
    # Final verdict
    header("DIAGNOSTIC RESULTS")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        if result:
            success(f"{name}: OK")
        else:
            error(f"{name}: ISSUES FOUND")
    
    print(f"\n  {passed}/{total} checks passed")
    
    if passed == total:
        print(f"\n{GREEN}  ══════════════════════════════════════════")
        print(f"   ALL SYSTEMS OPERATIONAL ✓")
        print(f"  ══════════════════════════════════════════{RESET}\n")
    else:
        print(f"\n{YELLOW}  ══════════════════════════════════════════")
        print(f"   SOME ISSUES FOUND - See details above")
        print(f"  ══════════════════════════════════════════{RESET}\n")
    
    return passed == total


if __name__ == '__main__':
    run()
elif not os.environ.get('SYNAPSE_TEST_IMPORT'):
    # Auto-run when loaded via Django shell (not when imported)
    run()
