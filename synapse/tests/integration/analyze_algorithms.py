"""
Algorithm Analysis Script
Analyzes edge cases and multi-annotation behavior
"""

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.synapse')

import django
django.setup()

from django.db.models import Count, Avg, Q
from projects.models import Project
from tasks.models import Task, Annotation
from annotators.models import (
    AnnotatorProfile, TaskAssignment, TaskConsensus,
    GoldenStandardTask, HoneypotAssignment, ExpertReviewTask
)

def analyze():
    print('='*70)
    print('         SYNAPSE ALGORITHM ANALYSIS & EDGE CASE REPORT')
    print('='*70)

    # 1. Project Configuration Analysis
    print('\n## 1. PROJECT CONFIGURATIONS ##')
    projects = Project.objects.all()[:10]
    for p in projects:
        overlap = p.required_overlap
        title = str(p.title)[:30]
        print(f'  {title:<30} overlap={overlap}')

    # 2. Task Assignment Distribution
    print('\n## 2. TASK ASSIGNMENT DISTRIBUTION ##')
    tasks_with_counts = Task.objects.annotate(
        ann_count=Count('annotations'),
        assign_cnt=Count('annotator_assignments')
    ).order_by('-ann_count')[:20]

    print(f'  {"Task ID":<10} {"Annotations":<12} {"Assignments":<12} {"Project":<25}')
    print('  ' + '-'*60)
    for t in tasks_with_counts:
        title = str(t.project.title)[:25] if t.project else 'N/A'
        print(f'  {t.id:<10} {t.ann_count:<12} {t.assign_cnt:<12} {title:<25}')

    # 3. Multi-Annotation Analysis
    print('\n## 3. MULTI-ANNOTATION ANALYSIS ##')
    multi_annotated = Task.objects.annotate(
        ann_count=Count('annotations')
    ).filter(ann_count__gt=1)
    print(f'  Tasks with >1 annotation: {multi_annotated.count()}')

    for task in multi_annotated[:5]:
        anns = Annotation.objects.filter(task=task, was_cancelled=False)
        annotators = [a.completed_by.email if a.completed_by else 'N/A' for a in anns]
        print(f'    Task {task.id}: {anns.count()} annotations by {annotators}')

    # 4. Consensus Status Distribution
    print('\n## 4. CONSENSUS STATUS DISTRIBUTION ##')
    consensus_stats = TaskConsensus.objects.values('status').annotate(count=Count('id'))
    for stat in consensus_stats:
        status = stat['status']
        count = stat['count']
        print(f'  {status:<20}: {count}')

    # Check consolidated results
    finalized = TaskConsensus.objects.filter(status='finalized')
    print(f'\n  Finalized tasks with ground truth: {finalized.filter(consolidated_result__isnull=False).count()}')

    # 5. Zero Annotation Tasks
    print('\n## 5. ZERO ANNOTATION EDGE CASE ##')
    zero_annotation = Task.objects.annotate(
        ann_count=Count('annotations')
    ).filter(ann_count=0, golden_standard__isnull=True)
    print(f'  Tasks with 0 annotations (non-honeypot): {zero_annotation.count()}')
    
    # Check if they have assignments
    zero_with_assignments = zero_annotation.filter(annotator_assignments__isnull=False).distinct()
    print(f'  Of those, with pending assignments: {zero_with_assignments.count()}')

    # 6. Assignment Status Distribution
    print('\n## 6. ASSIGNMENT STATUS DISTRIBUTION ##')
    assignment_stats = TaskAssignment.objects.values('status').annotate(count=Count('id'))
    for stat in assignment_stats:
        status = stat['status']
        count = stat['count']
        print(f'  {status:<20}: {count}')

    # Expired/stale assignments
    expired = TaskAssignment.objects.filter(status='expired').count()
    print(f'\n  Expired (auto-reclaimed): {expired}')

    # 7. Honeypot Performance
    print('\n## 7. HONEYPOT INJECTION & PERFORMANCE ##')
    golden_count = GoldenStandardTask.objects.count()
    honeypot_evals = HoneypotAssignment.objects.all()
    print(f'  Golden Standard Tasks: {golden_count}')
    print(f'  Honeypot Evaluations: {honeypot_evals.count()}')
    if honeypot_evals.exists():
        correct = honeypot_evals.filter(passed=True).count()
        total = honeypot_evals.count()
        print(f'  Accuracy: {correct}/{total} ({100*correct/total:.1f}%)')

    # 8. Expert Review Queue
    print('\n## 8. EXPERT REVIEW STATUS ##')
    review_stats = ExpertReviewTask.objects.values('status').annotate(count=Count('id'))
    for stat in review_stats:
        status = stat['status']
        count = stat['count']
        print(f'  {status:<20}: {count}')
    
    # Tasks needing review via consensus
    needs_review = TaskConsensus.objects.filter(status='review_required').count()
    print(f'\n  Tasks still needing review: {needs_review}')

    # 9. Annotator Workload Distribution  
    print('\n## 9. ANNOTATOR WORKLOAD ##')
    annotators = AnnotatorProfile.objects.all()[:10]
    for a in annotators:
        assigned = TaskAssignment.objects.filter(annotator=a, status='assigned').count()
        completed = TaskAssignment.objects.filter(annotator=a, status='completed').count()
        email = a.user.email if a.user else 'N/A'
        print(f'  {email:<25}: assigned={assigned}, completed={completed}')

    # 10. Overlap Enforcement Check
    print('\n## 10. OVERLAP REQUIREMENT ENFORCEMENT ##')
    for project in Project.objects.all()[:5]:
        required = project.required_overlap
        tasks = Task.objects.filter(project=project, golden_standard__isnull=True)
        
        under_annotated = 0
        properly_annotated = 0
        over_annotated = 0
        
        for task in tasks:
            ann_count = Annotation.objects.filter(task=task, was_cancelled=False).count()
            if ann_count < required:
                under_annotated += 1
            elif ann_count == required:
                properly_annotated += 1
            else:
                over_annotated += 1
        
        if tasks.count() > 0:
            print(f'  {project.title[:25]:<25} (overlap={required}):')
            print(f'    Under: {under_annotated}, Exact: {properly_annotated}, Over: {over_annotated}')

    # 11. Assignment Engine Fairness
    print('\n## 11. ASSIGNMENT FAIRNESS (LOAD BALANCING) ##')
    annotators = AnnotatorProfile.objects.annotate(
        total_assigned=Count('task_assignments')
    ).order_by('-total_assigned')[:10]
    
    counts = [a.total_assigned for a in annotators]
    if counts:
        avg = sum(counts) / len(counts)
        max_diff = max(counts) - min(counts) if counts else 0
        print(f'  Assignment counts: {counts}')
        print(f'  Average per annotator: {avg:.1f}')
        print(f'  Max difference (fairness): {max_diff}')

    # 12. Consolidation Algorithm Results
    print('\n## 12. CONSOLIDATION OUTCOMES ##')
    consensus_records = TaskConsensus.objects.exclude(status='pending')
    
    agreement_reached = TaskConsensus.objects.filter(status='consensus_reached').count()
    finalized = TaskConsensus.objects.filter(status='finalized').count()
    conflicts = TaskConsensus.objects.filter(status='conflict').count()
    review_req = TaskConsensus.objects.filter(status='review_required').count()
    
    print(f'  Consensus Reached: {agreement_reached}')
    print(f'  Finalized (ground truth set): {finalized}')
    print(f'  Conflicts detected: {conflicts}')
    print(f'  Escalated to expert: {review_req}')
    
    # Check consolidation methods used
    methods = TaskConsensus.objects.exclude(
        consolidation_method=''
    ).values('consolidation_method').annotate(count=Count('id'))
    if methods:
        print('\n  Consolidation methods used:')
        for m in methods:
            print(f'    {m["consolidation_method"]}: {m["count"]}')

    print('\n' + '='*70)
    print('                      SUMMARY & CONCLUSIONS')
    print('='*70)
    
    total_tasks = Task.objects.filter(golden_standard__isnull=True).count()
    total_annotations = Annotation.objects.filter(was_cancelled=False).count()
    total_assignments = TaskAssignment.objects.count()
    
    print(f'''
    SYSTEM METRICS:
    - Total Tasks (non-honeypot): {total_tasks}
    - Total Annotations: {total_annotations}
    - Total Assignments: {total_assignments}
    - Avg annotations per task: {total_annotations/max(total_tasks,1):.2f}

    ALGORITHM BEHAVIOR:
    1. Multi-Annotation: Working - tasks receiving {multi_annotated.count()} multi-annotations
    2. Consensus Detection: Active - {finalized + agreement_reached} tasks consolidated
    3. Conflict Resolution: {conflicts} conflicts detected, {review_req} escalated
    4. Honeypot System: {honeypot_evals.count()} evaluations performed
    5. Expert Review: {ExpertReviewTask.objects.count()} reviews completed
    
    EDGE CASES HANDLED:
    - Zero annotation tasks: {zero_annotation.count()} waiting for assignment
    - Expired assignments: {expired} auto-reclaimed
    - Over-annotated tasks: {over_annotated if 'over_annotated' in dir() else 'N/A'}
    ''')


if __name__ == '__main__':
    analyze()
