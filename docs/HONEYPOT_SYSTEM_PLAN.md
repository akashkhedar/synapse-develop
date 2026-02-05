# Honeypot System Plan

## Executive Summary

The honeypot system for annotator quality control is **already implemented** in the Synapse platform. This document outlines the existing architecture, how it works, and potential enhancements.

---

## Current Implementation Status ✅

### Models (Implemented)

| Model | Location | Purpose |
|-------|----------|---------|
| `HoneypotTask` | `annotators/models.py:615` | Stores ground truth and evaluates annotations |
| `TrustLevel` | `annotators/models.py:496` | Tracks honeypot pass rate, accuracy, level progression |
| `AnnotatorProfile.accuracy_score` | `annotators/models.py:65` | Cached accuracy metric |
| `TaskAssignment.is_honeypot` | `annotators/models.py` | Flags honeypot assignments |
| `TaskAssignment.honeypot_passed` | `annotators/models.py` | Records honeypot result |

### Services (Implemented)

| Service | Location | Purpose |
|---------|----------|---------|
| `HoneypotService` | `annotators/honeypot_service.py` | Core honeypot logic |
| `AccuracyService` | `annotators/accuracy_service.py` | Ground truth comparison |
| `PaymentService` | `annotators/payment_service.py` | Payment integration |

### API Endpoints (Implemented)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/annotators/honeypots/project/{id}` | GET/POST | List/Create honeypots |
| `/api/annotators/honeypots/project/{id}/{honeypot_id}` | GET/PUT/DELETE | CRUD operations |
| `/api/annotators/honeypots/project/{id}/stats` | GET | Honeypot statistics |
| `/api/annotators/honeypots/project/{id}/config` | GET/PUT | Configuration |
| `/api/annotators/honeypots/project/{id}/bulk` | POST | Bulk create |

---

## System Architecture

### 1. Honeypot Task Creation

```
Project Manager
     │
     ▼
┌─────────────────────────────────────────────────────────┐
│  POST /api/annotators/honeypots/project/{id}            │
│                                                         │
│  {                                                      │
│    "task_id": 123,                                      │
│    "ground_truth": [{"type": "labels", ...}],           │
│    "tolerance": 0.8  // 80% agreement required          │
│  }                                                      │
└─────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────┐
│  HoneypotTask Model                                     │
│  - task: FK to Task                                     │
│  - ground_truth: JSON (expected annotation)             │
│  - tolerance: 0.0-1.0 (agreement threshold)             │
│  - times_shown, times_passed, times_failed              │
└─────────────────────────────────────────────────────────┘
```

### 2. Honeypot Injection Flow

```
Annotator requests next task
     │
     ▼
┌─────────────────────────────────────────────────────────┐
│  projects/functions/next_task.py                        │
│                                                         │
│  1. Check if should inject honeypot:                    │
│     HoneypotService.should_inject_honeypot(annotator)   │
│                                                         │
│  2. If yes, get honeypot:                               │
│     HoneypotService.get_honeypot_task(annotator)        │
│                                                         │
│  3. Return honeypot task (looks like regular task)      │
└─────────────────────────────────────────────────────────┘
```

**Injection Logic** (`HoneypotService.should_inject_honeypot`):
1. Check if project has `honeypot_enabled = True`
2. Check if project has active honeypots
3. Check if annotator is due for honeypot (based on `honeypot_injection_rate`)
4. Check minimum interval since last honeypot (`honeypot_min_interval`)
5. Check if annotator has unseen honeypots available

### 3. Honeypot Evaluation Flow

```
Annotator submits annotation
     │
     ▼
┌─────────────────────────────────────────────────────────┐
│  PaymentService.process_annotation_completion()         │
│  (annotators/payment_service.py:328)                    │
│                                                         │
│  1. Check if task has honeypot_config                   │
│  2. If yes:                                             │
│     - honeypot.evaluate_annotation(result)              │
│     - Returns: (passed: bool, score: float)             │
│                                                         │
│  3. Update TaskAssignment:                              │
│     - is_honeypot = True                                │
│     - honeypot_passed = passed                          │
│                                                         │
│  4. If failed:                                          │
│     - Flag for review                                   │
│     - No payment                                        │
│     - Update TrustLevel                                 │
└─────────────────────────────────────────────────────────┘
```

### 4. Accuracy Calculation

**HoneypotTask.evaluate_annotation():**
```python
def evaluate_annotation(self, annotation_result):
    score = PaymentService.calculate_annotation_agreement(
        annotation_result, self.ground_truth
    )
    passed = score >= float(self.tolerance)
    
    # Update statistics
    self.times_shown += 1
    if passed:
        self.times_passed += 1
    else:
        self.times_failed += 1
    self.save()
    
    return passed, score
```

### 5. Profile Update Flow

```
Honeypot Result
     │
     ▼
┌─────────────────────────────────────────────────────────┐
│  HoneypotService.update_annotator_accuracy()            │
│                                                         │
│  1. Get TrustLevel for annotator                        │
│  2. Query last 100 honeypot assignments                 │
│  3. Calculate pass rate:                                │
│     pass_rate = (passed / total) * 100                  │
│  4. Update honeypot_pass_rate                           │
│  5. Update AnnotatorProfile.accuracy_score              │
│  6. check_level_upgrade() for trust level promotion     │
└─────────────────────────────────────────────────────────┘
```

---

## Trust Level Progression

The `TrustLevel` model tracks annotator progression based on:

| Level | Tasks Required | Accuracy Required | Honeypot Pass Rate |
|-------|----------------|-------------------|-------------------|
| New | 0 | 0% | 0% |
| Junior | 50 | 70% | 80% |
| Regular | 200 | 80% | 90% |
| Senior | 500 | 90% | 95% |
| Expert | 1000 | 95% | 98% |

**Pay Multipliers by Level:**
- New: 0.8x
- Junior: 1.0x
- Regular: 1.1x
- Senior: 1.3x
- Expert: 1.5x

---

## Project Configuration

Projects have these honeypot settings:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `honeypot_enabled` | bool | False | Enable honeypot system |
| `honeypot_injection_rate` | float | 0.05 | 5% of tasks are honeypots |
| `honeypot_min_interval` | int | 20 | Minimum tasks between honeypots |
| `honeypot_failure_threshold` | int | 3 | Consecutive failures before action |

---

## Consecutive Failure Detection

`HoneypotService._check_consecutive_failures()`:

1. Get last N honeypot assignments (N = threshold)
2. Check if all are failures
3. If threshold exceeded:
   - Add fraud flag to TrustLevel
   - If 3+ fraud flags → suspend annotator
   - Send notification (TODO)

---

## Key Files Reference

```
synapse/annotators/
├── honeypot_service.py      # Core honeypot logic
├── honeypot_api.py          # REST API endpoints
├── accuracy_service.py      # Ground truth comparison
├── payment_service.py       # Payment integration
├── models.py                # HoneypotTask, TrustLevel models
├── serializers.py           # API serializers
└── tests.py                 # Unit tests

synapse/projects/
├── models.py                # Project honeypot config fields
└── functions/next_task.py   # Honeypot injection point
```

---

## Potential Enhancements

### 1. Real-time Dashboard (Enhancement)
- Add WebSocket updates for honeypot results
- Live accuracy charts in admin panel

### 2. Difficulty-Based Honeypots (Enhancement)
Current: All honeypots treated equally
Proposed: 
- Add `difficulty` field to HoneypotTask (easy/medium/hard)
- Weight accuracy by difficulty
- Show easier honeypots to new annotators

### 3. Automated Honeypot Generation (Enhancement)
Current: Manual creation by project manager
Proposed:
- Auto-generate from expert-approved tasks
- ML-based ground truth inference

### 4. Annotator Feedback (Enhancement)
Current: No feedback to annotators on honeypot performance
Proposed:
- Optional "accuracy report" after X tasks
- Learning resources for common mistakes

### 5. Sync AnnotatorProfile.accuracy_score (Minor Fix)
Current: `TrustLevel.accuracy_score` and `AnnotatorProfile.accuracy_score` may diverge
Proposed:
- Add background task to sync these values
- Or remove `AnnotatorProfile.accuracy_score` and always use TrustLevel

### 6. Multi-Annotator Ground Truth Comparison (Enhancement)
Current: Binary pass/fail against single ground truth
Proposed:
- Calculate IOU/overlap for bounding boxes
- Per-label accuracy breakdown
- Visual diff for failed honeypots

---

## Usage Guide

### Creating a Honeypot

```python
from annotators.honeypot_service import HoneypotService

# Create honeypot from an existing task
honeypot = HoneypotService.create_honeypot(
    task=task,
    ground_truth=[
        {"type": "labels", "value": {"labels": ["cat"]}}
    ],
    tolerance=0.8,  # 80% agreement required
    created_by=admin_user
)
```

### Checking Honeypot Stats

```python
stats = HoneypotService.get_honeypot_stats(project)
# {
#     "total_honeypots": 10,
#     "active_honeypots": 8,
#     "total_evaluations": 150,
#     "overall_pass_rate": 87.3,
#     "average_pass_rate": 85.5
# }
```

### Getting Annotator Accuracy

```python
from annotators.accuracy_service import AccuracyService

summary = AccuracyService.get_annotator_accuracy_summary(annotator_profile)
# {
#     "accuracy_score": 89.5,
#     "ground_truth_evaluations": 45,
#     "accuracy_trend": "improving",
#     "level": "regular"
# }
```

---

## Conclusion

The honeypot system is **fully implemented** with:
- ✅ Automatic honeypot injection during task retrieval
- ✅ Ground truth comparison and scoring
- ✅ Accuracy tracking in TrustLevel
- ✅ Level progression based on honeypot performance
- ✅ Consecutive failure detection and suspension
- ✅ REST API for management
- ✅ Project-level configuration

No core implementation is needed. Consider the enhancements above for future improvements.
