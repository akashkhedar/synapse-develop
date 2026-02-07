# Expert Assignment Algorithm - Implementation Complete

## Overview

The Expert Assignment Engine handles assigning consolidated annotation tasks to experts for review. This runs **after** the consolidation algorithm produces a consolidated annotation.

## Flow Sequence

```
Task Created
    ↓
Annotator Assignment (overlap=3)
    ↓
All 3 annotations completed
    ↓
Consolidation Algorithm runs
    ↓
Agreement Check:
    - Agreement >= 70%: Always assign to expert
    - Agreement < 70%: 30% random chance for expert review
    ↓
**Expert Assignment Algorithm**
    ↓
Expert reviews (accept/reject/correct)
    ↓
Task finalized
```

---

## Implementation Summary

### Files Created/Modified

1. **synapse/annotators/expert_assignment_engine.py** - NEW
   - `ExpertAssignmentEngine` class with all core methods

2. **synapse/annotators/models.py** - UPDATED
   - `ExpertProfile` model updated with activity tracking

3. **synapse/annotators/signals.py** - UPDATED
   - Expert signals for review completion and login reactivation

4. **synapse/annotators/migrations/0016_expert_assignment_engine_updates.py** - NEW
   - Migration for model changes

---

## Key Design Decisions

| Requirement | Implementation |
|-------------|----------------|
| No expert levels | Removed `expertise_level` field |
| No expertise areas | Field kept but marked as "ON HOLD" |
| Workload by task count | `max_concurrent_reviews` (not daily) |
| No task priority | Agreement-based + random selection |
| Activity tracking | `is_active_for_assignments`, `inactive_since`, `last_active` |
| Timeout handling | 48h with activity check, 7-day inactivity threshold |
| Reactivation on login | Signal-based reactivation |

---

## Configuration Constants

```python
EXPERT_REVIEW_TIMEOUT_HOURS = 48      # Hours before review is stale
EXPERT_INACTIVITY_THRESHOLD_DAYS = 7  # Days before marking inactive
AGREEMENT_THRESHOLD = 70              # Above this: always to expert
RANDOM_SELECTION_RATE = 30            # % chance for low-agreement tasks
DEFAULT_EXPERT_CAPACITY = 50          # Default max concurrent reviews
```

---

## Core Methods

### ExpertAssignmentEngine

| Method | Purpose |
|--------|---------|
| `get_eligible_experts()` | Get active experts with capacity |
| `check_expert_capacity()` | Check current vs max reviews |
| `should_assign_to_expert()` | Agreement-based decision |
| `assign_task_to_expert()` | Assign single task |
| `batch_assign_pending_tasks()` | Bulk assignment |
| `handle_review_timeout()` | Activity-based timeout logic |
| `check_and_process_timeouts()` | Process all stale reviews |
| `reactivate_expert_on_login()` | Reactivate on login |
| `on_expert_review_complete()` | Handle completion |
| `get_expert_workload_stats()` | Get distribution stats |

---

## Cases Handled

### Case 1: No Experts Available
```python
if not eligible_experts:
    return {
        'status': 'waiting',
        'message': 'No experts available. Task held.',
    }
```

### Case 2: Experts Available
```python
# Select expert with lowest workload
expert = eligible_experts[0]  # Already sorted by workload
assign_task_to_expert(task_consensus, expert)
```

---

## Agreement-Based Assignment

```python
def should_assign_to_expert(agreement_score):
    # High agreement: Always assign
    if agreement_score >= 70:
        return True, 'high_agreement'
    
    # Low agreement: Random selection (30% chance)
    if random.random() * 100 < 30:
        return True, 'random_sample'
    
    return False, 'skipped'
```

---

## Timeout Handling

```python
def handle_review_timeout(review_task):
    expert = review_task.expert
    
    # 1. Expert was active since assignment -> Extend
    if expert.last_active > review_task.assigned_at:
        review_task.assigned_at = now  # Reset timer
        return 'extended'
    
    # 2. Expert inactive > 7 days -> Mark inactive, release all
    if expert.last_active < (now - 7 days):
        mark_expert_inactive()
        release_all_pending_reviews()
        return 'marked_inactive'
    
    # 3. Normal timeout -> Release and reassign
    release_review()
    reassign_to_another_expert()
    return 'released'
```

---

## Signal Handlers

### On Expert Login
```python
def reactivate_expert_on_login(user):
    expert = ExpertProfile.objects.filter(user=user).first()
    if expert:
        ExpertAssignmentEngine.reactivate_expert_on_login(expert)
```

### On Review Completion
```python
@receiver(post_save, sender=ExpertReviewTask)
def on_expert_review_completed(sender, instance, **kwargs):
    if instance.status in ['approved', 'rejected', 'corrected']:
        # Decrement workload
        # Trigger next assignment
```

### After Consolidation
```python
def trigger_expert_assignment_after_consolidation(task_consensus):
    ExpertAssignmentEngine.assign_task_to_expert(task_consensus)
```

---

## Database Changes (Migration 0016)

```python
# Added
ExpertProfile.is_active_for_assignments  # BooleanField, default=True
ExpertProfile.inactive_since             # DateTimeField, null=True

# Renamed
max_reviews_per_day -> max_concurrent_reviews

# Removed
expertise_level  # All experts are equal now
```

---

## Usage Examples

### Assign After Consolidation
```python
from annotators.expert_assignment_engine import ExpertAssignmentEngine

# After consolidation completes
result = ExpertAssignmentEngine.assign_task_to_expert(
    task_consensus=consensus,
    force=False,
)

if result['assigned']:
    print(f"Assigned to {result['expert_email']}")
elif result['reason'] == 'no_experts':
    print("Task held - no experts available")
elif result['reason'] == 'skipped':
    print("Task skipped expert review")
```

### Process Timeouts (Celery Task)
```python
from annotators.expert_assignment_engine import ExpertAssignmentEngine

# Run periodically (every hour)
result = ExpertAssignmentEngine.check_and_process_timeouts()
print(f"Extended: {result['extended']}, Released: {result['released']}")
```

### Get Workload Stats
```python
stats = ExpertAssignmentEngine.get_expert_workload_stats()
print(f"Total capacity: {stats['total_capacity']}")
for expert in stats['experts']:
    print(f"{expert['email']}: {expert['current']}/{expert['maximum']}")
```

---

## Integration Checklist

- [x] ExpertProfile model updated
- [x] ExpertAssignmentEngine class created
- [x] Activity tracking fields added
- [x] Timeout handling implemented
- [x] Login reactivation signal added
- [x] Review completion signal added
- [x] Migration created
- [ ] Connect to consolidation service (call `trigger_expert_assignment_after_consolidation`)
- [ ] Add Celery task for timeout processing
- [ ] Test end-to-end flow

---

## Next Steps

1. **Connect to Consolidation**: Call `trigger_expert_assignment_after_consolidation()` from consensus service
2. **Celery Task**: Add periodic task to call `check_and_process_timeouts()`
3. **Testing**: Test with sample data
