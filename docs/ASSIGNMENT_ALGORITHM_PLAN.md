# Annotator Task Assignment Algorithm - Implementation Plan

> **Version**: 2.0  
> **Date**: February 5, 2026  
> **Status**: Ready for Implementation

---

## Executive Summary

This document outlines a comprehensive real-time task assignment algorithm that dynamically adjusts overlap based on annotator availability while maintaining quality constraints.

### Core Constraints
- **Overlap Range**: 1 ≤ overlap ≤ 3 (HARD LIMIT)
- **No Duplicate Annotations**: A single annotator CANNOT annotate the same task twice
- **Real-time Responsiveness**: System reacts to annotator eligibility changes
- **Quality First**: Better to hold tasks than compromise on quality

---

## Three Main Cases

### Case 1: No Eligible Annotators (0 Annotators)
**Situation**: No approved annotators are available for the project  
**Action**: HOLD all tasks in pending state  
**Resolution**: Periodic check for new eligible annotators

```
Tasks State: PENDING_ASSIGNMENT
Overlap: Not Set (waiting)
Trigger: Background job checks every X minutes
```

### Case 2: Limited Annotators (1-2 Annotators)
**Situation**: Fewer annotators than desired overlap (3)  
**Action**: ADJUST overlap to match available annotator count  
**Constraint**: Overlap = min(available_annotators, 3), minimum 1

```
1 Annotator  → Overlap = 1 (single annotation per task)
2 Annotators → Overlap = 2 (dual annotation per task)
```

### Case 3: Sufficient Annotators (3+ Annotators)
**Situation**: Enough annotators for full consensus  
**Action**: ASSIGN with overlap = 3, distribute by workload  
**Strategy**: Round-robin or performance-based rotation

```
3+ Annotators → Overlap = 3 (full consensus)
Distribution: Fair workload balancing across all eligible
```

---

## Detailed Algorithm Design

### Phase 1: Eligibility Check

```python
def get_eligible_annotators(project):
    """
    Get all annotators eligible for this project
    
    Eligibility Criteria:
    1. Status = 'approved'
    2. User is active
    3. Not suspended (fraud_flags < 3)
    4. Has available capacity (not at max concurrent tasks)
    5. NOT already assigned to all project tasks
    6. Recently active (not marked inactive due to prolonged absence)
    
    Note: Trust level is NOT checked against project settings
    (clients cannot configure min_trust_level)
    """
    
    eligible = AnnotatorProfile.objects.filter(
        status='approved',
        user__is_active=True,
    ).select_related('user', 'trust_level')
    
    # Exclude suspended
    eligible = eligible.filter(
        Q(trust_level__isnull=True) | 
        Q(trust_level__fraud_flags__lt=3, trust_level__is_suspended=False)
    )
    
    # Filter by capacity
    eligible = [a for a in eligible if has_available_capacity(a)]
    
    return eligible
```

### Phase 2: Overlap Calculation

```python
def calculate_effective_overlap(project, eligible_count):
    """
    Calculate the effective overlap for this project
    
    Rules:
    - If eligible_count == 0: Return None (hold tasks)
    - If eligible_count < 3: Return eligible_count
    - If eligible_count >= 3: Return 3 (max overlap)
    
    Note: Never exceed 3, never go below 1 (if annotators exist)
    """
    
    if eligible_count == 0:
        return None  # Signal to hold tasks
    
    # Effective overlap = min(available, max_overlap)
    max_overlap = 3  # HARD LIMIT
    return min(eligible_count, max_overlap)
```

### Phase 3: Task Assignment Logic

```python
def assign_tasks_with_dynamic_overlap(project):
    """
    Main assignment algorithm
    
    Steps:
    1. Get eligible annotators
    2. Calculate effective overlap
    3. Handle the three cases
    4. Update task target_assignment_count
    5. Distribute tasks fairly
    """
    
    eligible = get_eligible_annotators(project)
    eligible_count = len(eligible)
    
    # CASE 1: No eligible annotators
    if eligible_count == 0:
        hold_all_pending_tasks(project)
        schedule_recheck(project, delay_minutes=5)
        return {
            'status': 'waiting',
            'message': 'No eligible annotators, tasks on hold',
            'assigned': 0
        }
    
    effective_overlap = calculate_effective_overlap(project, eligible_count)
    
    # CASE 2: Limited annotators (1-2)
    if eligible_count < 3:
        update_task_overlaps(project, effective_overlap)
        assignments = assign_all_to_all(project, eligible, effective_overlap)
        # Also schedule check for when more annotators become available
        schedule_recheck(project, delay_minutes=10)
        return {
            'status': 'partial',
            'overlap': effective_overlap,
            'assigned': len(assignments)
        }
    
    # CASE 3: Sufficient annotators (3+)
    update_task_overlaps(project, 3)
    assignments = distribute_with_rotation(project, eligible)
    return {
        'status': 'complete',
        'overlap': 3,
        'assigned': len(assignments)
    }
```

---

## Edge Cases & Solutions

### Edge Case 1: Annotator Becomes Ineligible Mid-Assignment
**Scenario**: Annotator is suspended or deactivated while having assigned tasks  
**Solution**: 
- Mark their pending assignments as `reassign_needed`
- Trigger reassignment of those tasks to other eligible annotators
- Do NOT delete existing completed annotations

```python
def handle_annotator_ineligible(annotator):
    # Get their incomplete assignments
    pending = TaskAssignment.objects.filter(
        annotator=annotator,
        status__in=['assigned', 'in_progress']
    )
    
    for assignment in pending:
        assignment.status = 'reassigned'
        assignment.save()
        
        # Trigger reassignment for this task
        trigger_task_reassignment(assignment.task)
```

### Edge Case 2: New Annotator Becomes Eligible
**Scenario**: A new annotator gets approved or an existing one meets criteria  
**Solution**: 
- Check all projects with held or under-covered tasks
- Potentially upgrade overlap (1→2, 2→3)
- Assign tasks to new annotator following rotation

```python
def on_annotator_eligible(annotator):
    # Find projects that need more annotators
    understaffed_projects = Project.objects.filter(
        is_published=True,
        tasks__annotator_assignments__count__lt=F('required_overlap')
    ).distinct()
    
    for project in understaffed_projects:
        eligible = get_eligible_annotators(project)
        if annotator in eligible:
            reevaluate_and_assign(project)
```

### Edge Case 3: Task Already Has Partial Annotations
**Scenario**: Task has 1 annotation but overlap was increased to 3  
**Solution**: 
- Respect existing annotations
- Assign only (new_overlap - current_count) more annotators
- Never reassign to someone who already annotated

```python
def assign_to_partially_complete_task(task, eligible_annotators, target_overlap):
    current_assignments = task.annotator_assignments.filter(
        status__in=['assigned', 'in_progress', 'completed']
    )
    current_count = current_assignments.count()
    already_assigned_ids = set(current_assignments.values_list('annotator_id', flat=True))
    
    needed = target_overlap - current_count
    if needed <= 0:
        return []  # Task is fully covered
    
    # Filter out already assigned annotators
    available = [a for a in eligible_annotators if a.id not in already_assigned_ids]
    
    # Assign to first `needed` available annotators
    assignments = []
    for annotator in available[:needed]:
        assignment = create_task_assignment(annotator, task)
        assignments.append(assignment)
    
    return assignments
```

### Edge Case 4: Overlap Downgrade Scenario
**Scenario**: Project had overlap=3 but 2 annotators became ineligible  
**Solution**: 
- DO NOT remove existing annotations
- Accept that some tasks may have more than current overlap
- New tasks get assigned with new lower overlap

```python
def downgrade_overlap(project, new_overlap):
    # Update project setting
    project.required_overlap = new_overlap
    project.save()
    
    # Update only UNASSIGNED tasks
    Task.objects.filter(
        project=project,
        annotator_assignments__isnull=True
    ).update(target_assignment_count=new_overlap)
    
    # Partially assigned tasks: 
    # Keep current target, just stop assigning more if they meet new_overlap
    # This prevents wasted work
```

### Edge Case 5: Annotator Capacity Limit Reached
**Scenario**: All eligible annotators are at capacity  
**Solution**: 
- Hold remaining tasks
- Schedule recheck for when capacity frees up
- All tasks are treated equally (no prioritization)

```python
def handle_all_at_capacity(project, pending_tasks):
    for task in pending_tasks:
        task.assignment_status = 'waiting_capacity'
        task.save()
    
    # Schedule recheck - annotators complete tasks over time
    # All tasks treated equally, no priority ordering
    schedule_recheck(project, delay_minutes=15)
```

### Edge Case 6: Annotator Skips/Expires Assignment
**Scenario**: Annotator skips a task or assignment times out (48-72 hours)  
**Solution**: 
- Check annotator's recent activity before releasing
- If active (working on other tasks): Extend/restart timer
- If inactive recently: Release task for reassignment
- If inactive for extended period: Mark annotator as inactive, stop future assignments

**Activity-Based Timeout Logic**:
```
Timeout Window: 48-72 hours (configurable)

IF assignment_age > timeout_threshold:
    IF annotator.last_active > assignment.assigned_at:
        # Annotator is active, just hasn't reached this task yet
        → Extend timer / Reset timeout
    ELIF annotator.last_active < (now - 7 days):
        # Annotator hasn't been active for a week
        → Mark annotator as inactive
        → Release ALL their pending assignments
        → Stop assigning new tasks until they login
    ELSE:
        # Annotator was active but not recently
        → Release this assignment only
        → Reassign to another annotator
```

```python
ASSIGNMENT_TIMEOUT_HOURS = 48  # Configurable
INACTIVITY_THRESHOLD_DAYS = 7  # Mark inactive after this

def handle_assignment_timeout(assignment):
    annotator = assignment.annotator
    now = timezone.now()
    
    # Check if annotator has been active since assignment
    if annotator.last_active and annotator.last_active > assignment.assigned_at:
        # Annotator is active, working on other tasks
        # Reset the timer by updating assigned_at
        assignment.assigned_at = now
        assignment.save(update_fields=['assigned_at'])
        logger.info(f"Extended timeout for active annotator {annotator.id}")
        return
    
    # Check for prolonged inactivity
    inactivity_cutoff = now - timedelta(days=INACTIVITY_THRESHOLD_DAYS)
    if not annotator.last_active or annotator.last_active < inactivity_cutoff:
        # Annotator hasn't been active for too long
        mark_annotator_inactive(annotator)
        release_all_pending_assignments(annotator)
        return
    
    # Normal timeout - release just this assignment
    assignment.status = 'expired'
    assignment.save()
    
    # Decrement counters
    assignment.task.assignment_count = F('assignment_count') - 1
    assignment.task.save()
    
    # Reassign to another eligible annotator
    trigger_task_reassignment(assignment.task)

def mark_annotator_inactive(annotator):
    """Mark annotator as inactive - they won't receive new tasks until login"""
    annotator.is_active_for_assignments = False
    annotator.inactive_since = timezone.now()
    annotator.save(update_fields=['is_active_for_assignments', 'inactive_since'])
    logger.info(f"Marked annotator {annotator.id} as inactive due to prolonged absence")

def on_annotator_login(annotator):
    """Reactivate annotator when they login"""
    if not annotator.is_active_for_assignments:
        annotator.is_active_for_assignments = True
        annotator.inactive_since = None
        annotator.last_active = timezone.now()
        annotator.save()
        
        # Check for available work
        trigger_assignment_check_for_annotator(annotator)
```

### Edge Case 7: All Tasks Completed But Overlap Changed
**Scenario**: Project completed with overlap=2, now has 3 annotators  
**Solution**: 
- DO NOT retroactively add annotations
- Keep completed tasks as-is
- Only apply new overlap to new/imported tasks

### Edge Case 8: Concurrent Assignment Race Condition
**Scenario**: Two processes try to assign the same task simultaneously  
**Solution**: 
- Use database-level locking (select_for_update)
- Unique constraint on (task, annotator)
- Transaction rollback on conflict

```python
def safe_create_assignment(annotator, task):
    with transaction.atomic():
        # Lock the task row
        task = Task.objects.select_for_update().get(id=task.id)
        
        # Check if assignment already exists
        if TaskAssignment.objects.filter(task=task, annotator=annotator).exists():
            raise AlreadyAssignedError()
        
        # Check if task is fully covered
        current = task.annotator_assignments.filter(
            status__in=['assigned', 'in_progress', 'completed']
        ).count()
        
        if current >= task.target_assignment_count:
            raise TaskFullyCoveredError()
        
        return TaskAssignment.objects.create(
            annotator=annotator,
            task=task,
            status='assigned'
        )
```

---

## Real-Time Responsiveness

### Trigger Points

| Event | Action |
|-------|--------|
| Annotator approved | Check understaffed projects, assign if eligible |
| Annotator suspended | Reassign their pending tasks |
| Annotator completes task | Check capacity, assign next task |
| New project published | Run initial assignment |
| Task imported | Assign to available annotators |
| Assignment timeout | Reassign to another annotator |

### Signal-Based Architecture

```python
# signals.py

@receiver(post_save, sender=AnnotatorProfile)
def on_annotator_status_change(sender, instance, **kwargs):
    if instance.status == 'approved':
        # Newly approved - check for work
        trigger_assignment_check_for_new_annotator(instance)
    elif instance.status in ['suspended', 'rejected']:
        # Became ineligible - reassign their work
        reassign_pending_work(instance)

@receiver(post_save, sender=TaskAssignment)
def on_assignment_complete(sender, instance, **kwargs):
    if instance.status == 'completed':
        # Free up capacity - check if more tasks available
        assign_next_task_to_annotator(instance.task.project, instance.annotator)
        
        # Check if task reached target overlap for consensus
        check_task_consensus(instance.task)

@receiver(post_save, sender=Task)
def on_task_created(sender, instance, created, **kwargs):
    if created and instance.project.is_published:
        # New task - assign to available annotators
        trigger_task_assignment(instance)
```

---

## Quality Safeguards

### Minimum Quality Thresholds

1. **Never go below overlap = 1**: If even 1 annotator exists, they annotate
2. **Hold rather than compromise**: If no annotators, hold tasks
3. **Respect existing work**: Never delete or replace valid annotations
4. **Consensus priority**: When overlap ≥ 2, use consensus for quality check

### Anti-Gaming Measures

1. **Unique constraint**: (task_id, annotator_id) ensures no duplicate work
2. **Completed check**: Cannot re-annotate a task even if assignment was deleted
3. **Annotation history**: Track all annotations even if assignments change

```python
# Additional check before assignment
def can_annotator_work_on_task(annotator, task):
    # Check if they already have ANY annotation on this task
    existing_annotation = Annotation.objects.filter(
        task=task,
        completed_by=annotator.user
    ).exists()
    
    if existing_annotation:
        return False, "Annotator already has annotation on this task"
    
    # Check if they had a previous assignment (even if cancelled)
    previous_assignment = TaskAssignment.objects.filter(
        task=task,
        annotator=annotator,
        status='completed'
    ).exists()
    
    if previous_assignment:
        return False, "Annotator already completed this task"
    
    return True, None
```

---

## Data Model Requirements

### Task Model Updates
```python
class Task:
    # Existing fields
    assignment_count = models.IntegerField(default=0)
    target_assignment_count = models.IntegerField(default=3)
    
    # New fields
    assignment_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending Assignment'),
            ('partial', 'Partially Assigned'),
            ('full', 'Fully Assigned'),
            ('waiting_capacity', 'Waiting for Capacity'),
        ],
        default='pending'
    )
    
    @property
    def needs_more_assignments(self):
        active = self.annotator_assignments.filter(
            status__in=['assigned', 'in_progress', 'completed']
        ).count()
        return active < self.target_assignment_count
```

### Project Model Updates
```python
class Project:
    # Existing fields
    required_overlap = models.IntegerField(default=3)
    
    # New fields
    effective_overlap = models.IntegerField(
        default=3,
        help_text="Current effective overlap based on available annotators"
    )
    assignment_status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Active Assignment'),
            ('waiting', 'Waiting for Annotators'),
            ('complete', 'All Tasks Assigned'),
        ],
        default='waiting'
    )
```

---

## API Endpoints

### 1. Trigger Assignment Check
```
POST /api/annotators/assignments/trigger-check/
{
    "project_id": 123
}

Response:
{
    "status": "complete|partial|waiting",
    "eligible_annotators": 5,
    "effective_overlap": 3,
    "tasks_assigned": 150,
    "tasks_pending": 0
}
```

### 2. Get Assignment Status
```
GET /api/annotators/assignments/status/?project_id=123

Response:
{
    "project_id": 123,
    "effective_overlap": 3,
    "eligible_annotators": [
        {"id": 1, "email": "...", "capacity": {"current": 5, "max": 50}},
        ...
    ],
    "task_stats": {
        "total": 300,
        "fully_assigned": 280,
        "partially_assigned": 15,
        "pending": 5
    }
}
```

### 3. Force Reassignment
```
POST /api/annotators/assignments/reassign/
{
    "project_id": 123,
    "task_ids": [1, 2, 3]  // Optional - reassign specific tasks
}
```

---

## Background Jobs

### 1. Periodic Eligibility Check
```python
# Run every 5 minutes
@celery_app.task
def check_understaffed_projects():
    """Find projects waiting for annotators and check if any became eligible"""
    
    waiting_projects = Project.objects.filter(
        is_published=True,
        assignment_status='waiting'
    )
    
    for project in waiting_projects:
        eligible = get_eligible_annotators(project)
        if eligible:
            assign_tasks_with_dynamic_overlap(project)
```

### 2. Capacity Freed Check
```python
# Run every 15 minutes
@celery_app.task
def check_capacity_freed():
    """Find annotators with freed capacity and assign more work"""
    
    annotators = AnnotatorProfile.objects.filter(status='approved')
    
    for annotator in annotators:
        if has_available_capacity(annotator):
            projects = get_active_projects_for_annotator(annotator)
            for project in projects:
                if has_pending_tasks(project, annotator):
                    assign_next_task_to_annotator(project, annotator)
```

### 3. Assignment Timeout Check
```python
# Run every 10 minutes
@celery_app.task
def check_assignment_timeouts():
    """Find expired assignments and reassign"""
    
    timeout_hours = 24
    cutoff = timezone.now() - timedelta(hours=timeout_hours)
    
    expired = TaskAssignment.objects.filter(
        status='assigned',
        assigned_at__lt=cutoff
    )
    
    for assignment in expired:
        handle_assignment_skip_or_timeout(assignment)
```

---

## Implementation Checklist

### Phase 1: Core Algorithm
- [ ] Implement `get_eligible_annotators()` with all filters
- [ ] Implement `calculate_effective_overlap()`
- [ ] Implement `assign_tasks_with_dynamic_overlap()`
- [ ] Add database locking for concurrent safety

### Phase 2: Edge Case Handlers
- [ ] Implement annotator eligibility change handler
- [ ] Implement partial assignment handler
- [ ] Implement overlap upgrade/downgrade logic
- [ ] Implement capacity limit handling
- [ ] Implement skip/timeout handling

### Phase 3: Real-Time Signals
- [ ] Add signal for annotator approval
- [ ] Add signal for annotator suspension
- [ ] Add signal for task completion
- [ ] Add signal for new task creation

### Phase 4: Background Jobs
- [ ] Implement periodic eligibility check
- [ ] Implement capacity freed check
- [ ] Implement timeout check
- [ ] Configure Celery beat schedules

### Phase 5: API & Monitoring
- [ ] Create assignment status API
- [ ] Create trigger check API
- [ ] Add logging for all assignment decisions
- [ ] Create admin dashboard for monitoring

---

## Testing Scenarios

### Scenario 1: Fresh Project, No Annotators
1. Create project with 10 tasks
2. Publish project
3. Verify: All tasks status = 'pending', no assignments

### Scenario 2: One Annotator Becomes Available
1. From Scenario 1
2. Approve one annotator matching project criteria
3. Verify: effective_overlap = 1, all 10 tasks assigned to that annotator

### Scenario 3: Second Annotator Joins
1. From Scenario 2
2. Approve second annotator
3. Verify: effective_overlap = 2, second annotator gets assignments
4. Verify: Same annotator doesn't get same task twice

### Scenario 4: Third Annotator (Full Overlap)
1. From Scenario 3
2. Approve third annotator
3. Verify: effective_overlap = 3, all tasks now have 3 assignments
4. Verify: Each task has exactly 3 different annotators

### Scenario 5: Annotator Suspended Mid-Work
1. Full project with 3 annotators
2. Suspend one annotator with pending tasks
3. Verify: Their pending tasks reassigned to others
4. Verify: Their completed work preserved

### Scenario 6: All Annotators at Capacity
1. 3 annotators, each at max capacity
2. Import new tasks to project
3. Verify: New tasks status = 'waiting_capacity'
4. One annotator completes a task
5. Verify: New task assigned to them

---

## Performance Considerations

### Indexing
```sql
CREATE INDEX idx_task_assignment_status ON task_assignment(task_id, status);
CREATE INDEX idx_task_target_count ON task(project_id, target_assignment_count);
CREATE INDEX idx_annotator_status ON annotator_profile(status);
```

### Query Optimization
- Use `select_related` for annotator + trust_level
- Use `prefetch_related` for task assignments
- Batch updates for target_assignment_count changes
- Use `select_for_update(skip_locked=True)` for concurrent safety without blocking

### Caching
- Cache eligible annotator count per project (invalidate on changes)
- Cache capacity info per annotator (TTL: 5 minutes)

---

## Summary

This algorithm ensures:
1. **Quality**: Overlap between 1-3, never 0 when annotators exist
2. **Fairness**: Workload distributed across available annotators
3. **Integrity**: No duplicate annotations by same annotator
4. **Responsiveness**: Real-time reaction to eligibility changes
5. **Resilience**: Graceful handling of all edge cases
