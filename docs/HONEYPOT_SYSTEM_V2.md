# Honeypot System v2.0 - Complete Rewrite

## ✅ IMPLEMENTATION STATUS: COMPLETE

All core components have been implemented:
- ✅ Constants & Configuration ([honeypot_constants.py](../synapse/annotators/honeypot_constants.py))
- ✅ Database Models (GoldenStandardTask, HoneypotAssignment, AccuracyHistory, AnnotatorWarning)
- ✅ Honeypot Injector Service ([honeypot_injector.py](../synapse/annotators/honeypot_injector.py))
- ✅ Honeypot Evaluator Service ([honeypot_evaluator.py](../synapse/annotators/honeypot_evaluator.py))
- ✅ Accuracy Tracker Service ([accuracy_tracker.py](../synapse/annotators/accuracy_tracker.py))
- ✅ Warning System Service ([warning_system.py](../synapse/annotators/warning_system.py))
- ✅ Honeypot Handler Integration ([honeypot_handler.py](../synapse/annotators/honeypot_handler.py))
- ✅ Assignment Flow Integration (assignment_engine.py)
- ✅ Submission Flow Integration (annotation_workflow.py)
- ✅ Database Migration (0018_honeypot_system_v2.py)

**Run migration:** `python manage.py migrate annotators`

---

## Executive Summary

A complete rewrite of the honeypot quality control system with **system-controlled injection** (no client configuration), **automatic insertion during task assignment**, and **comprehensive accuracy monitoring** with tiered warning system.

---

## Design Principles

1. **System-Controlled** - No client/project configuration for honeypot rates
2. **Invisible to Annotators** - Honeypots are indistinguishable from regular tasks
3. **Assignment-Time Injection** - Insert honeypots when tasks are assigned, not at retrieval
4. **Separate Pipeline** - Honeypots bypass consolidation entirely
5. **Continuous Monitoring** - Real-time accuracy tracking with automated interventions
6. **Dual Accuracy Metrics** - Lifetime accuracy on profile (fair long-term view) + Rolling window for warnings (catch recent drops)

---

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          HONEYPOT SYSTEM v2.0                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────────┐    ┌──────────────────────────┐    │
│  │  Golden     │    │   Assignment    │    │   Annotation             │    │
│  │  Standard   │───▶│   Service       │───▶│   Submission             │    │
│  │  Pool       │    │   (Inject HP)   │    │   (Evaluate)             │    │
│  └─────────────┘    └─────────────────┘    └──────────────────────────┘    │
│        │                    │                         │                     │
│        │                    │                         ▼                     │
│        │                    │              ┌──────────────────────────┐    │
│        │                    │              │   Accuracy Calculator    │    │
│        │                    │              │   (Compare to Golden)    │    │
│        │                    │              └──────────────────────────┘    │
│        │                    │                         │                     │
│        │                    │                         ▼                     │
│        │                    │              ┌──────────────────────────┐    │
│        │                    │              │   Profile Updater        │    │
│        │                    │              │   (Update accuracy_score)│    │
│        │                    │              └──────────────────────────┘    │
│        │                    │                         │                     │
│        │                    │                         ▼                     │
│        │                    │              ┌──────────────────────────┐    │
│        │                    │              │   Warning System         │    │
│        │                    │              │   (Email/Flag/Suspend)   │    │
│        │                    │              └──────────────────────────┘    │
│        │                    │                                               │
└────────┴────────────────────┴───────────────────────────────────────────────┘
```

---

## Workflow Summary

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         END-TO-END WORKFLOW                                │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  1. SETUP: Admin creates Golden Standard tasks with verified annotations   │
│     └─▶ GoldenStandardTask records created                                 │
│                                                                            │
│  2. ASSIGNMENT: System assigns tasks to annotator                          │
│     └─▶ HoneypotInjector automatically inserts honeypots in queue          │
│     └─▶ Annotator receives mixed queue (doesn't know which are honeypots)  │
│                                                                            │
│  3. ANNOTATION: Annotator works on tasks normally                          │
│     └─▶ No visual difference between regular tasks and honeypots           │
│                                                                            │
│  4. SUBMISSION: Annotator submits annotation                               │
│     └─▶ System checks: Is this a honeypot? (via HoneypotAssignment table)  │
│                                                                            │
│  5a. IF REGULAR TASK:                                                      │
│      └─▶ Continue normal flow → Consolidation → Expert Review              │
│                                                                            │
│  5b. IF HONEYPOT:                                                          │
│      └─▶ INTERCEPT: Do NOT send to consolidation                           │
│      └─▶ EVALUATE: Compare to golden standard annotation                   │
│      └─▶ CALCULATE: Score accuracy (0-100%)                                │
│      └─▶ UPDATE: Update annotator's accuracy_score in profile              │
│      └─▶ CHECK: If below threshold → Issue warning/email                   │
│                                                                            │
│  6. MONITORING: Admin dashboard shows accuracy trends and warnings         │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Golden Standard Pool

### 1.1 What is a Golden Standard Task?

A golden standard task is a **pre-annotated task with verified ground truth** that serves as a benchmark for measuring annotator accuracy. The annotator doesn't know this is a test - it looks exactly like a regular task.

### 1.2 Sources of Golden Standard Tasks

| Source | Description | How Created |
|--------|-------------|-------------|
| Expert Annotated | Tasks annotated by verified experts | Expert submits, admin marks as golden |
| Client Provided | Ground truth provided by client during project setup | Client uploads with data |
| Admin Curated | Manually verified by admin from consensus tasks | Admin selects high-agreement tasks |

### 1.3 Golden Standard Model

```python
class GoldenStandardTask(models.Model):
    """Pre-annotated tasks with verified ground truth for quality control"""
    
    # Link to original task
    task = models.OneToOneField(
        Task, 
        on_delete=models.CASCADE, 
        related_name='golden_standard'
    )
    project = models.ForeignKey(
        Project, 
        on_delete=models.CASCADE, 
        related_name='golden_standards'
    )
    
    # The verified correct annotation (what we compare against)
    ground_truth = models.JSONField(
        help_text="Verified correct annotation result"
    )
    
    # Source tracking
    SOURCE_CHOICES = [
        ('expert', 'Expert Annotated'),
        ('client', 'Client Provided'),
        ('admin', 'Admin Curated'),
    ]
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    source_annotation = models.ForeignKey(
        Annotation, 
        null=True, 
        on_delete=models.SET_NULL,
        help_text="Original annotation this was created from"
    )
    
    # Tolerance for matching (0.0 = exact match, 1.0 = any answer passes)
    # Default 0.85 = 85% match required to pass
    tolerance = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        default=0.85
    )
    
    # Usage statistics
    times_shown = models.IntegerField(default=0)
    times_passed = models.IntegerField(default=0)
    times_failed = models.IntegerField(default=0)
    average_score = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True
    )
    
    # Retirement (stop showing after too many uses to prevent memorization)
    max_uses = models.IntegerField(default=100)
    is_retired = models.BooleanField(default=False)
    retired_at = models.DateTimeField(null=True)
    
    class Meta:
        db_table = 'golden_standard_task'
        
    def retire_if_needed(self):
        """Retire golden standard if used too many times"""
        if self.times_shown >= self.max_uses and not self.is_retired:
            self.is_retired = True
            self.retired_at = timezone.now()
            self.is_active = False
            self.save()
```

### 1.4 System Constants (NOT Client-Configurable)

```python
# synapse/annotators/constants.py

HONEYPOT_CONFIG = {
    # Pool requirements
    'MIN_GOLDEN_STANDARDS_PER_PROJECT': 10,      # Minimum to enable honeypots
    'RECOMMENDED_GOLDEN_STANDARDS': 50,           # Recommended for variety
    'MAX_USES_BEFORE_RETIREMENT': 100,            # Retire after 100 uses
    
    # Injection rates (system-controlled, NO client override)
    'INJECTION_RATE': 0.05,                       # 5% = 1 honeypot per 20 tasks
    'MIN_INTERVAL_TASKS': 10,                     # Minimum 10 tasks between honeypots
    'MAX_INTERVAL_TASKS': 30,                     # Maximum 30 tasks between honeypots
    
    # Evaluation
    'DEFAULT_TOLERANCE': 0.85,                    # 85% match required to pass
    'ROLLING_WINDOW_SIZE': 50,                    # Accuracy based on last 50 honeypots
    
    # Warning thresholds
    'THRESHOLD_HEALTHY': 80,                      # 80%+ = good
    'THRESHOLD_SOFT_WARNING': 70,                 # 70-79% = soft warning
    'THRESHOLD_FORMAL_WARNING': 60,               # 60-69% = formal warning  
    'THRESHOLD_FINAL_WARNING': 50,                # 50-59% = final warning
    'THRESHOLD_SUSPENSION': 40,                   # <40% = suspension
    
    # Warning cooldowns (don't spam warnings)
    'COOLDOWN_SOFT_WARNING_DAYS': 7,
    'COOLDOWN_FORMAL_WARNING_DAYS': 14,
    'COOLDOWN_FINAL_WARNING_DAYS': 7,
    
    # Recovery
    'RECOVERY_THRESHOLD': 80,                     # Must reach 80% to clear warnings
    'RECOVERY_WINDOW': 20,                        # Based on 20 honeypots after warning
}
```

---

## Phase 2: Assignment-Time Injection

### 2.1 When Injection Happens

Honeypots are injected when tasks are **assigned** to annotators, not when retrieved. This ensures:
- Honeypots are pre-planned, not random at retrieval time
- We can track exactly which tasks are honeypots
- Position in queue is controlled

### 2.2 Injection Flow

```
AssignmentService.assign_tasks(annotator, project, count=20)
     │
     ▼
┌─────────────────────────────────────────────────────────┐
│  1. Get 20 regular tasks for assignment                 │
│                                                         │
│  2. HoneypotInjector.inject_honeypots():                │
│     ├─ Calculate injection points (e.g., position 12)  │
│     ├─ Get unused golden standards for this annotator  │
│     └─ Insert honeypot at calculated positions         │
│                                                         │
│  3. Create TaskAssignment records for ALL tasks         │
│     (regular tasks + honeypots mixed together)          │
│                                                         │
│  4. Create HoneypotAssignment records (internal only)   │
│     for honeypot tasks                                  │
│                                                         │
│  5. Return assignments to annotator                     │
│     (Annotator sees uniform list - can't tell which     │
│      are honeypots)                                     │
└─────────────────────────────────────────────────────────┘
```

### 2.3 Injection Algorithm

```python
class HoneypotInjector:
    """
    Injects honeypot tasks into assignment queues.
    
    SYSTEM-CONTROLLED - No client configuration allowed.
    """
    
    @classmethod
    def inject_honeypots(cls, annotator, project, task_list):
        """
        Inject honeypot tasks into a task assignment list.
        
        Args:
            annotator: AnnotatorProfile
            project: Project
            task_list: List of Task objects to be assigned
            
        Returns:
            List of (Task, is_honeypot, golden_standard) tuples
        """
        from .constants import HONEYPOT_CONFIG
        
        if len(task_list) == 0:
            return []
        
        # Check if project has enough golden standards
        available_golden = cls._get_available_golden_standards(annotator, project)
        
        if len(available_golden) < 3:
            logger.warning(
                f"Project {project.id} has insufficient golden standards "
                f"({len(available_golden)} available, need at least 3)"
            )
            # Return tasks without honeypots
            return [(task, False, None) for task in task_list]
        
        # Calculate where to inject honeypots
        injection_points = cls._calculate_injection_points(
            task_count=len(task_list),
            annotator=annotator,
            project=project
        )
        
        # Build mixed queue
        result = []
        task_idx = 0
        honeypot_idx = 0
        position = 0
        
        while task_idx < len(task_list) or honeypot_idx < len(injection_points):
            if position in injection_points and honeypot_idx < len(available_golden):
                # Insert honeypot at this position
                golden = available_golden[honeypot_idx]
                result.append((golden.task, True, golden))
                honeypot_idx += 1
            elif task_idx < len(task_list):
                # Insert regular task
                result.append((task_list[task_idx], False, None))
                task_idx += 1
            position += 1
            
        return result
    
    @classmethod
    def _calculate_injection_points(cls, task_count, annotator, project):
        """
        Calculate positions where honeypots should be inserted.
        
        Uses randomized intervals within bounds to prevent pattern detection.
        """
        from .constants import HONEYPOT_CONFIG
        import random
        
        min_interval = HONEYPOT_CONFIG['MIN_INTERVAL_TASKS']
        max_interval = HONEYPOT_CONFIG['MAX_INTERVAL_TASKS']
        
        # Get how many tasks since annotator's last honeypot
        tasks_since_last = cls._get_tasks_since_last_honeypot(annotator, project)
        
        # First injection point accounts for previous tasks
        first_injection = max(0, min_interval - tasks_since_last)
        
        injection_points = []
        current_pos = first_injection
        
        while current_pos < task_count:
            injection_points.append(current_pos)
            # Random interval for next honeypot (prevents predictability)
            next_interval = random.randint(min_interval, max_interval)
            current_pos += next_interval
            
        return injection_points
    
    @classmethod
    def _get_available_golden_standards(cls, annotator, project):
        """Get golden standards this annotator hasn't seen yet."""
        # Get IDs of golden standards already shown to this annotator
        seen_ids = HoneypotAssignment.objects.filter(
            annotator=annotator,
            golden_standard__project=project
        ).values_list('golden_standard_id', flat=True)
        
        # Get active, non-retired golden standards not yet seen
        return list(
            GoldenStandardTask.objects.filter(
                project=project,
                is_active=True,
                is_retired=False
            ).exclude(
                id__in=seen_ids
            ).order_by('?')[:10]  # Random selection, get up to 10
        )
    
    @classmethod
    def _get_tasks_since_last_honeypot(cls, annotator, project):
        """Count regular tasks completed since last honeypot."""
        last_honeypot = HoneypotAssignment.objects.filter(
            annotator=annotator,
            golden_standard__project=project,
            status='evaluated'
        ).order_by('-submitted_at').first()
        
        if not last_honeypot:
            return 999  # No previous honeypot, inject soon
        
        # Count completed assignments since last honeypot
        return TaskAssignment.objects.filter(
            annotator=annotator,
            project=project,
            status='completed',
            completed_at__gt=last_honeypot.submitted_at
        ).count()
```

### 2.4 Honeypot Assignment Record (Internal Only)

```python
class HoneypotAssignment(models.Model):
    """
    Tracks honeypot assignments to annotators.
    
    THIS TABLE IS INTERNAL ONLY - Never exposed to annotator APIs.
    Annotators cannot query this table or know which tasks are honeypots.
    """
    
    annotator = models.ForeignKey(
        AnnotatorProfile, 
        on_delete=models.CASCADE,
        related_name='honeypot_assignments'
    )
    golden_standard = models.ForeignKey(
        GoldenStandardTask, 
        on_delete=models.CASCADE
    )
    task_assignment = models.OneToOneField(
        TaskAssignment, 
        on_delete=models.CASCADE,
        related_name='honeypot_info'  # Internal only
    )
    
    # Position in the assignment queue (for analysis)
    position_in_queue = models.IntegerField()
    
    # Timing
    assigned_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    
    # Evaluation results (filled after submission)
    annotator_result = models.JSONField(null=True, blank=True)
    accuracy_score = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    passed = models.BooleanField(null=True)
    evaluation_details = models.JSONField(
        null=True, 
        blank=True,
        help_text="Detailed comparison breakdown"
    )
    
    # Status
    STATUS_CHOICES = [
        ('pending', 'Pending'),         # Assigned, not yet submitted
        ('submitted', 'Submitted'),     # Submitted, awaiting evaluation
        ('evaluated', 'Evaluated'),     # Evaluation complete
        ('skipped', 'Skipped'),         # Annotator skipped or timed out
    ]
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending'
    )
    
    class Meta:
        db_table = 'honeypot_assignment'
        indexes = [
            models.Index(fields=['annotator', 'status']),
            models.Index(fields=['golden_standard', 'status']),
        ]
```

---

## Phase 3: Submission & Evaluation

### 3.1 Submission Interception

When annotator submits, we check if it's a honeypot and route accordingly:

```python
class AnnotationSubmissionHandler:
    """
    Handles annotation submissions with honeypot detection.
    """
    
    @classmethod
    @transaction.atomic
    def handle_submission(cls, task, annotator, annotation_result):
        """
        Process an annotation submission.
        
        1. Save annotation
        2. Check if honeypot
        3. Route appropriately
        """
        # Save the annotation first
        annotation = cls._save_annotation(task, annotator, annotation_result)
        
        # Get task assignment
        task_assignment = TaskAssignment.objects.filter(
            task=task,
            annotator=annotator
        ).first()
        
        if not task_assignment:
            raise ValueError("No assignment found for this task/annotator")
        
        # Check if this is a honeypot
        try:
            honeypot_assignment = task_assignment.honeypot_info
            # This IS a honeypot - handle separately
            return cls._handle_honeypot_submission(
                honeypot_assignment,
                annotation_result,
                annotation
            )
        except HoneypotAssignment.DoesNotExist:
            # Regular task - continue normal flow
            return cls._handle_regular_submission(
                task,
                task_assignment,
                annotation
            )
    
    @classmethod
    def _handle_honeypot_submission(cls, honeypot_assignment, result, annotation):
        """
        Process honeypot submission:
        - Evaluate against golden standard
        - Update annotator accuracy
        - Do NOT send to consolidation
        """
        # Evaluate
        evaluation = HoneypotEvaluator.evaluate(
            honeypot_assignment,
            result
        )
        
        # Update honeypot assignment
        honeypot_assignment.annotator_result = result
        honeypot_assignment.accuracy_score = evaluation['accuracy_score']
        honeypot_assignment.passed = evaluation['passed']
        honeypot_assignment.evaluation_details = evaluation['details']
        honeypot_assignment.submitted_at = timezone.now()
        honeypot_assignment.status = 'evaluated'
        honeypot_assignment.save()
        
        # Update golden standard statistics
        golden = honeypot_assignment.golden_standard
        golden.times_shown += 1
        if evaluation['passed']:
            golden.times_passed += 1
        else:
            golden.times_failed += 1
        # Update average score
        total_scores = (golden.average_score * (golden.times_shown - 1) + 
                       evaluation['accuracy_score'])
        golden.average_score = total_scores / golden.times_shown
        golden.save()
        golden.retire_if_needed()
        
        # Update annotator accuracy
        AnnotatorAccuracyTracker.update_accuracy(
            honeypot_assignment.annotator,
            evaluation
        )
        
        # Mark task assignment complete (but it won't go to consolidation)
        task_assignment = honeypot_assignment.task_assignment
        task_assignment.status = 'completed'
        task_assignment.completed_at = timezone.now()
        task_assignment.annotation = annotation
        task_assignment.is_honeypot = True
        task_assignment.honeypot_passed = evaluation['passed']
        task_assignment.save()
        
        return {
            'type': 'honeypot',
            'passed': evaluation['passed'],
            'score': evaluation['accuracy_score'],
            # Don't reveal this is a honeypot to annotator!
            'message': 'Annotation submitted successfully'
        }
    
    @classmethod
    def _handle_regular_submission(cls, task, task_assignment, annotation):
        """
        Process regular task submission:
        - Update task assignment
        - Check if ready for consolidation
        - Trigger consolidation if needed
        """
        task_assignment.status = 'completed'
        task_assignment.completed_at = timezone.now()
        task_assignment.annotation = annotation
        task_assignment.save()
        
        # Check overlap completion
        cls._check_consolidation_ready(task)
        
        return {
            'type': 'regular',
            'message': 'Annotation submitted successfully'
        }
```

### 3.2 Evaluation Engine

```python
class HoneypotEvaluator:
    """
    Evaluates annotator submissions against golden standard.
    
    Supports multiple annotation types with type-specific comparison.
    """
    
    @classmethod
    def evaluate(cls, honeypot_assignment, annotator_result):
        """
        Evaluate annotator's result against golden standard.
        
        Returns:
            {
                'passed': bool,
                'accuracy_score': float (0-100),
                'details': {...}
            }
        """
        golden = honeypot_assignment.golden_standard
        ground_truth = golden.ground_truth
        tolerance = float(golden.tolerance)
        
        # Detect annotation type from ground truth structure
        annotation_type = cls._detect_annotation_type(ground_truth)
        
        # Get appropriate comparison strategy
        comparator = cls._get_comparator(annotation_type)
        
        # Calculate accuracy
        comparison_result = comparator.compare(annotator_result, ground_truth)
        overall_score = comparison_result.get('overall_score', 0)
        
        # Determine pass/fail based on tolerance
        passed = overall_score >= (tolerance * 100)
        
        return {
            'passed': passed,
            'accuracy_score': overall_score,
            'details': {
                'annotation_type': annotation_type,
                'tolerance_required': tolerance * 100,
                'score_achieved': overall_score,
                **comparison_result
            }
        }
    
    @classmethod
    def _detect_annotation_type(cls, result):
        """Detect annotation type from result structure."""
        if not result:
            return 'unknown'
            
        # Handle list of annotations
        first_item = result[0] if isinstance(result, list) else result
        
        if 'type' in first_item:
            type_mapping = {
                'labels': 'classification',
                'choices': 'classification',
                'rectanglelabels': 'bounding_box',
                'polygonlabels': 'polygon',
                'brushlabels': 'segmentation',
                'labels': 'ner',
                'textarea': 'text',
            }
            return type_mapping.get(first_item['type'].lower(), 'generic')
        
        return 'generic'
    
    @classmethod
    def _get_comparator(cls, annotation_type):
        """Get the appropriate comparator for annotation type."""
        comparators = {
            'classification': ClassificationComparator(),
            'bounding_box': BoundingBoxComparator(),
            'polygon': PolygonComparator(),
            'segmentation': SegmentationComparator(),
            'ner': NERComparator(),
            'text': TextComparator(),
            'generic': GenericComparator(),
        }
        return comparators.get(annotation_type, GenericComparator())


class ClassificationComparator:
    """Compare classification/labeling annotations."""
    
    def compare(self, annotator_result, ground_truth):
        # Extract labels
        annotator_labels = set(self._extract_labels(annotator_result))
        ground_truth_labels = set(self._extract_labels(ground_truth))
        
        if not ground_truth_labels:
            return {'overall_score': 100, 'match': True}
        
        # Calculate Jaccard similarity for multi-label
        intersection = annotator_labels & ground_truth_labels
        union = annotator_labels | ground_truth_labels
        
        if not union:
            score = 100
        else:
            score = (len(intersection) / len(union)) * 100
        
        return {
            'overall_score': score,
            'annotator_labels': list(annotator_labels),
            'expected_labels': list(ground_truth_labels),
            'matches': list(intersection),
            'missing': list(ground_truth_labels - annotator_labels),
            'extra': list(annotator_labels - ground_truth_labels),
        }
    
    def _extract_labels(self, result):
        labels = []
        items = result if isinstance(result, list) else [result]
        for item in items:
            if 'value' in item:
                value = item['value']
                if 'choices' in value:
                    labels.extend(value['choices'])
                elif 'labels' in value:
                    labels.extend(value['labels'])
        return labels


class BoundingBoxComparator:
    """Compare bounding box annotations using IoU."""
    
    def compare(self, annotator_result, ground_truth):
        annotator_boxes = self._extract_boxes(annotator_result)
        ground_truth_boxes = self._extract_boxes(ground_truth)
        
        if not ground_truth_boxes:
            return {'overall_score': 100 if not annotator_boxes else 0}
        
        # Match boxes and calculate IoU
        total_iou = 0
        matched = 0
        
        for gt_box in ground_truth_boxes:
            best_iou = 0
            for ann_box in annotator_boxes:
                if ann_box.get('label') == gt_box.get('label'):
                    iou = self._calculate_iou(ann_box, gt_box)
                    best_iou = max(best_iou, iou)
            total_iou += best_iou
            if best_iou > 0.5:  # Threshold for "matched"
                matched += 1
        
        overall_score = (total_iou / len(ground_truth_boxes)) * 100
        
        return {
            'overall_score': overall_score,
            'boxes_expected': len(ground_truth_boxes),
            'boxes_matched': matched,
            'average_iou': total_iou / len(ground_truth_boxes) if ground_truth_boxes else 0,
        }
    
    def _extract_boxes(self, result):
        boxes = []
        items = result if isinstance(result, list) else [result]
        for item in items:
            if item.get('type') in ['rectanglelabels', 'rectangle']:
                value = item.get('value', {})
                boxes.append({
                    'x': value.get('x', 0),
                    'y': value.get('y', 0),
                    'width': value.get('width', 0),
                    'height': value.get('height', 0),
                    'label': value.get('rectanglelabels', [''])[0] if value.get('rectanglelabels') else '',
                })
        return boxes
    
    def _calculate_iou(self, box1, box2):
        """Calculate Intersection over Union for two boxes."""
        x1 = max(box1['x'], box2['x'])
        y1 = max(box1['y'], box2['y'])
        x2 = min(box1['x'] + box1['width'], box2['x'] + box2['width'])
        y2 = min(box1['y'] + box1['height'], box2['y'] + box2['height'])
        
        intersection = max(0, x2 - x1) * max(0, y2 - y1)
        
        area1 = box1['width'] * box1['height']
        area2 = box2['width'] * box2['height']
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0


class GenericComparator:
    """Fallback comparator for unknown annotation types."""
    
    def compare(self, annotator_result, ground_truth):
        # Simple JSON equality check
        if annotator_result == ground_truth:
            return {'overall_score': 100, 'match': True}
        
        # Partial match scoring could be implemented here
        return {'overall_score': 0, 'match': False}
```

---

## Phase 4: Accuracy Tracking

### 4.1 Dual Accuracy System

We use **two accuracy metrics** for different purposes:

| Metric | Storage | Calculation | Purpose |
|--------|---------|-------------|----------|
| **Lifetime Accuracy** | `AnnotatorProfile.accuracy_score` | All-time average | Long-term performance view, fair assessment |
| **Rolling Accuracy** | `TrustLevel.rolling_accuracy` | Last 50 honeypots | Warning system, detect recent drops |

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      DUAL ACCURACY SYSTEM                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Honeypot Evaluation                                                        │
│        │                                                                    │
│        ▼                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    ACCURACY TRACKER                                  │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │                                                                      │   │
│  │  ┌─────────────────────────┐    ┌─────────────────────────┐        │   │
│  │  │   LIFETIME ACCURACY     │    │   ROLLING ACCURACY      │        │   │
│  │  ├─────────────────────────┤    ├─────────────────────────┤        │   │
│  │  │ All honeypots ever      │    │ Last 50 honeypots only  │        │   │
│  │  │ Stored on:              │    │ Stored on:              │        │   │
│  │  │ AnnotatorProfile        │    │ TrustLevel              │        │   │
│  │  │   .accuracy_score       │    │   .rolling_accuracy     │        │   │
│  │  └───────────┬─────────────┘    └───────────┬─────────────┘        │   │
│  │              │                              │                       │   │
│  │              ▼                              ▼                       │   │
│  │  ┌─────────────────────────┐    ┌─────────────────────────┐        │   │
│  │  │ USED FOR:               │    │ USED FOR:               │        │   │
│  │  │ • Profile display       │    │ • Warning decisions     │        │   │
│  │  │ • Client view           │    │ • Suspension triggers   │        │   │
│  │  │ • Long-term trends      │    │ • Recovery checks       │        │   │
│  │  │ • Fair assessment       │    │ • Quick issue detection │        │   │
│  │  └─────────────────────────┘    └─────────────────────────┘        │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Why Lifetime Accuracy on Profile?**
- Shows if annotator maintains quality over time
- Fairer for annotators with temporary dips
- Clients can see overall reliability
- Allows tracking of performance degradation trends

**Why Rolling Window for Warnings?**
- Catches recent quality issues quickly
- Allows recovery from early mistakes
- Prevents penalizing someone forever for past errors

```python
class AnnotatorAccuracyTracker:
    """
    Tracks annotator accuracy with dual metrics:
    - Lifetime accuracy on AnnotatorProfile (overall performance)
    - Rolling window accuracy for warning decisions (recent performance)
    """
    
    @classmethod
    def update_accuracy(cls, annotator, evaluation_result):
        """
        Update annotator's accuracy after honeypot evaluation.
        
        Updates:
        1. AnnotatorProfile.accuracy_score (LIFETIME average)
        2. TrustLevel metrics
        3. Checks warning thresholds using ROLLING window
        """
        from .constants import HONEYPOT_CONFIG
        
        new_score = float(evaluation_result['accuracy_score'])
        
        # ============================================
        # 1. UPDATE LIFETIME ACCURACY (on profile)
        # ============================================
        # Get total honeypot count for this annotator
        total_honeypots = HoneypotAssignment.objects.filter(
            annotator=annotator,
            status='evaluated',
            accuracy_score__isnull=False
        ).count()
        
        if total_honeypots == 1:
            # First honeypot - use raw score
            lifetime_accuracy = new_score
        else:
            # Calculate new lifetime average
            # Formula: new_avg = old_avg + (new_score - old_avg) / n
            old_accuracy = float(annotator.accuracy_score or 0)
            lifetime_accuracy = old_accuracy + (new_score - old_accuracy) / total_honeypots
        
        # Update AnnotatorProfile with LIFETIME accuracy
        annotator.accuracy_score = Decimal(str(round(lifetime_accuracy, 2)))
        annotator.total_honeypots_evaluated = total_honeypots
        annotator.save(update_fields=['accuracy_score', 'total_honeypots_evaluated'])
        
        # ============================================
        # 2. CALCULATE ROLLING ACCURACY (for warnings)
        # ============================================
        window_size = HONEYPOT_CONFIG['ROLLING_WINDOW_SIZE']
        
        recent_results = HoneypotAssignment.objects.filter(
            annotator=annotator,
            status='evaluated',
            accuracy_score__isnull=False
        ).order_by('-submitted_at')[:window_size]
        
        recent_scores = [float(r.accuracy_score) for r in recent_results]
        rolling_accuracy = sum(recent_scores) / len(recent_scores) if recent_scores else 0
        
        # ============================================
        # 3. UPDATE TRUST LEVEL METRICS
        # ============================================
        cls._update_trust_level(annotator, total_honeypots, rolling_accuracy)
        
        # ============================================
        # 4. CHECK WARNING THRESHOLDS (using ROLLING)
        # ============================================
        # Warnings are based on recent performance, not lifetime
        WarningSystem.check_and_warn(annotator, rolling_accuracy)
        
        logger.info(
            f"Updated accuracy for {annotator.user.email}: "
            f"Lifetime={lifetime_accuracy:.1f}% (n={total_honeypots}), "
            f"Rolling={rolling_accuracy:.1f}% (last {len(recent_scores)})"
        )
        
        return {
            'lifetime_accuracy': lifetime_accuracy,
            'rolling_accuracy': rolling_accuracy,
            'total_honeypots': total_honeypots
        }
    
    @classmethod
    def _update_trust_level(cls, annotator, total_honeypots, rolling_accuracy):
        """Update TrustLevel honeypot metrics."""
        from .models import TrustLevel
        
        try:
            trust_level = annotator.trust_level
        except TrustLevel.DoesNotExist:
            trust_level = TrustLevel.objects.create(annotator=annotator)
        
        # Get pass count from all evaluated honeypots
        passed_count = HoneypotAssignment.objects.filter(
            annotator=annotator,
            status='evaluated',
            passed=True
        ).count()
        
        trust_level.total_honeypots = total_honeypots
        trust_level.passed_honeypots = passed_count
        trust_level.honeypot_pass_rate = Decimal(str(
            (passed_count / total_honeypots * 100) if total_honeypots > 0 else 0
        ))
        # Store rolling accuracy for quick access
        trust_level.rolling_accuracy = Decimal(str(round(rolling_accuracy, 2)))
        trust_level.last_accuracy_update = timezone.now()
        trust_level.save()
        
        # Check for level upgrade/downgrade
        trust_level.check_level_upgrade()
```

### 4.2 Accuracy History for Trending

Track both lifetime and rolling accuracy daily for trend analysis:

```python
class AccuracyHistory(models.Model):
    """
    Daily accuracy snapshots for trend analysis.
    
    Stores both lifetime and rolling metrics for comparison.
    """
    
    annotator = models.ForeignKey(
        AnnotatorProfile, 
        on_delete=models.CASCADE,
        related_name='accuracy_history'
    )
    date = models.DateField()
    
    # Daily metrics
    honeypots_evaluated = models.IntegerField(default=0)
    honeypots_passed = models.IntegerField(default=0)
    daily_average_score = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        null=True
    )
    
    # Cumulative metrics (at end of day)
    total_honeypots_lifetime = models.IntegerField(default=0)
    lifetime_accuracy = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        help_text="All-time accuracy at end of this day"
    )
    rolling_accuracy = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        help_text="Rolling window accuracy at end of this day"
    )
    
    class Meta:
        db_table = 'accuracy_history'
        unique_together = ['annotator', 'date']
        indexes = [
            models.Index(fields=['annotator', 'date']),
        ]
    
    @classmethod
    def record_daily_snapshot(cls, annotator):
        """Record end-of-day accuracy snapshot."""
        today = timezone.now().date()
        
        # Get today's honeypots
        todays_honeypots = HoneypotAssignment.objects.filter(
            annotator=annotator,
            status='evaluated',
            submitted_at__date=today
        )
        
        if not todays_honeypots.exists():
            return None
        
        daily_scores = [float(h.accuracy_score) for h in todays_honeypots if h.accuracy_score]
        
        cls.objects.update_or_create(
            annotator=annotator,
            date=today,
            defaults={
                'honeypots_evaluated': todays_honeypots.count(),
                'honeypots_passed': todays_honeypots.filter(passed=True).count(),
                'daily_average_score': sum(daily_scores) / len(daily_scores) if daily_scores else None,
                'total_honeypots_lifetime': annotator.total_honeypots_evaluated or 0,
                'lifetime_accuracy': annotator.accuracy_score or 0,
                'rolling_accuracy': annotator.trust_level.rolling_accuracy if hasattr(annotator, 'trust_level') else 0,
            }
        )
```

---

## Phase 5: Warning & Intervention System

### 5.1 Warning Levels

| Level | Accuracy Range | Action | Email | Assignment Impact |
|-------|---------------|--------|-------|-------------------|
| Healthy | ≥ 80% | None | - | Normal |
| Soft Warning | 70-79% | Log + Email | "Improvement needed" | Normal |
| Formal Warning | 60-69% | Log + Email | "Official warning" | Normal |
| Final Warning | 50-59% | Log + Email + Flag | "Last chance" | Reduced assignments |
| Suspension | < 50% | Suspend | "Account suspended" | No assignments |

### 5.2 Warning Implementation

```python
class WarningSystem:
    """
    Manages annotator warnings based on honeypot performance.
    """
    
    @classmethod
    def check_and_warn(cls, annotator, accuracy):
        """
        Check accuracy thresholds and issue appropriate warnings.
        """
        from .constants import HONEYPOT_CONFIG
        
        thresholds = {
            'healthy': HONEYPOT_CONFIG['THRESHOLD_HEALTHY'],
            'soft_warning': HONEYPOT_CONFIG['THRESHOLD_SOFT_WARNING'],
            'formal_warning': HONEYPOT_CONFIG['THRESHOLD_FORMAL_WARNING'],
            'final_warning': HONEYPOT_CONFIG['THRESHOLD_FINAL_WARNING'],
            'suspension': HONEYPOT_CONFIG['THRESHOLD_SUSPENSION'],
        }
        
        if accuracy >= thresholds['healthy']:
            # Good performance - check if recovered from warnings
            cls._check_recovery(annotator, accuracy)
            return
        
        # Determine warning level
        if accuracy >= thresholds['soft_warning']:
            cls._issue_warning(annotator, 'soft_warning', accuracy)
        elif accuracy >= thresholds['formal_warning']:
            cls._issue_warning(annotator, 'formal_warning', accuracy)
        elif accuracy >= thresholds['final_warning']:
            cls._issue_warning(annotator, 'final_warning', accuracy)
        else:
            cls._suspend(annotator, accuracy)
    
    @classmethod
    def _issue_warning(cls, annotator, warning_type, accuracy):
        """Issue warning if not in cooldown period."""
        from .constants import HONEYPOT_CONFIG
        from .models import AnnotatorWarning
        
        # Check cooldown
        cooldown_key = f'COOLDOWN_{warning_type.upper()}_DAYS'
        cooldown_days = HONEYPOT_CONFIG.get(cooldown_key, 7)
        
        recent_warning = AnnotatorWarning.objects.filter(
            annotator=annotator,
            warning_type=warning_type,
            created_at__gte=timezone.now() - timedelta(days=cooldown_days)
        ).exists()
        
        if recent_warning:
            logger.info(
                f"Skipping {warning_type} for {annotator.user.email} - "
                f"in {cooldown_days}-day cooldown"
            )
            return
        
        # Create warning record
        message = cls._get_warning_message(warning_type, accuracy)
        warning = AnnotatorWarning.objects.create(
            annotator=annotator,
            warning_type=warning_type,
            accuracy_at_warning=Decimal(str(accuracy)),
            message=message
        )
        
        # Send email notification
        cls._send_warning_email(annotator, warning)
        
        # Apply restrictions for final warning
        if warning_type == 'final_warning':
            annotator.is_active_for_assignments = False
            annotator.save(update_fields=['is_active_for_assignments'])
            logger.warning(
                f"Disabled assignments for {annotator.user.email} due to final warning"
            )
        
        logger.info(
            f"Issued {warning_type} to {annotator.user.email} "
            f"(accuracy: {accuracy:.1f}%)"
        )
    
    @classmethod
    def _suspend(cls, annotator, accuracy):
        """Suspend annotator for critically poor performance."""
        from .models import AnnotatorWarning, TrustLevel
        
        # Update TrustLevel
        try:
            trust_level = annotator.trust_level
            trust_level.is_suspended = True
            trust_level.suspension_reason = (
                f"Honeypot accuracy {accuracy:.1f}% below minimum threshold"
            )
            trust_level.save()
        except TrustLevel.DoesNotExist:
            pass
        
        # Disable assignments
        annotator.is_active_for_assignments = False
        annotator.save(update_fields=['is_active_for_assignments'])
        
        # Create suspension record
        AnnotatorWarning.objects.create(
            annotator=annotator,
            warning_type='suspension',
            accuracy_at_warning=Decimal(str(accuracy)),
            message=(
                f"Your account has been suspended due to annotation accuracy "
                f"of {accuracy:.1f}%, which is below our minimum quality standard "
                f"of 50%. Please contact support for reinstatement process."
            )
        )
        
        # Send suspension email
        cls._send_suspension_email(annotator, accuracy)
        
        logger.warning(
            f"SUSPENDED annotator {annotator.user.email} - "
            f"accuracy {accuracy:.1f}% below threshold"
        )
    
    @classmethod
    def _check_recovery(cls, annotator, accuracy):
        """Check if annotator has recovered from previous warnings."""
        from .models import AnnotatorWarning, TrustLevel
        from .constants import HONEYPOT_CONFIG
        
        # Check if there are active restrictions
        if not annotator.is_active_for_assignments:
            # Get last warning
            last_warning = AnnotatorWarning.objects.filter(
                annotator=annotator,
                warning_type__in=['final_warning', 'suspension']
            ).order_by('-created_at').first()
            
            if not last_warning:
                return
            
            # Count honeypots since warning
            honeypots_since = HoneypotAssignment.objects.filter(
                annotator=annotator,
                status='evaluated',
                submitted_at__gt=last_warning.created_at
            ).count()
            
            recovery_window = HONEYPOT_CONFIG['RECOVERY_WINDOW']
            recovery_threshold = HONEYPOT_CONFIG['RECOVERY_THRESHOLD']
            
            if honeypots_since >= recovery_window and accuracy >= recovery_threshold:
                cls._grant_recovery(annotator, accuracy)
    
    @classmethod
    def _grant_recovery(cls, annotator, accuracy):
        """Restore annotator to good standing."""
        from .models import AnnotatorWarning, TrustLevel
        
        # Re-enable assignments
        annotator.is_active_for_assignments = True
        annotator.save(update_fields=['is_active_for_assignments'])
        
        # Clear suspension
        try:
            trust_level = annotator.trust_level
            if trust_level.is_suspended:
                trust_level.is_suspended = False
                trust_level.suspension_reason = ""
                trust_level.save()
        except TrustLevel.DoesNotExist:
            pass
        
        # Create recovery record
        AnnotatorWarning.objects.create(
            annotator=annotator,
            warning_type='recovery',
            accuracy_at_warning=Decimal(str(accuracy)),
            message=(
                f"Congratulations! Your accuracy has improved to {accuracy:.1f}%. "
                f"Your account is now in good standing and you will receive "
                f"normal task assignments."
            )
        )
        
        # Send recovery email
        cls._send_recovery_email(annotator, accuracy)
        
        logger.info(
            f"RECOVERED: {annotator.user.email} restored to good standing "
            f"(accuracy: {accuracy:.1f}%)"
        )
    
    @classmethod
    def _get_warning_message(cls, warning_type, accuracy):
        """Get appropriate warning message."""
        messages = {
            'soft_warning': (
                f"Your annotation accuracy has dropped to {accuracy:.1f}%. "
                f"Please review the annotation guidelines carefully to ensure "
                f"your work meets our quality standards."
            ),
            'formal_warning': (
                f"OFFICIAL WARNING: Your annotation accuracy is {accuracy:.1f}%, "
                f"which is below our quality standards. This is an official warning. "
                f"Continued poor performance may result in reduced task assignments "
                f"or account suspension."
            ),
            'final_warning': (
                f"FINAL WARNING: Your annotation accuracy of {accuracy:.1f}% is "
                f"critically low. Your task assignments have been paused until you "
                f"demonstrate improved quality. Complete the assigned tasks carefully "
                f"to restore your account. Failure to improve will result in "
                f"permanent suspension."
            ),
        }
        return messages.get(warning_type, "Quality warning issued.")
    
    @classmethod
    def _send_warning_email(cls, annotator, warning):
        """Send warning email to annotator."""
        from django.core.mail import send_mail
        
        subject_prefix = {
            'soft_warning': '📊 Quality Notice',
            'formal_warning': '⚠️ Official Warning',
            'final_warning': '🚨 FINAL WARNING',
        }
        
        try:
            send_mail(
                subject=f"{subject_prefix.get(warning.warning_type, 'Notice')}: "
                       f"Your Annotation Quality",
                message=warning.message,
                from_email='noreply@synapse-platform.com',
                recipient_list=[annotator.user.email],
                fail_silently=True
            )
            warning.email_sent = True
            warning.email_sent_at = timezone.now()
            warning.save(update_fields=['email_sent', 'email_sent_at'])
        except Exception as e:
            logger.error(f"Failed to send warning email: {e}")
    
    @classmethod
    def _send_suspension_email(cls, annotator, accuracy):
        """Send suspension notification email."""
        from django.core.mail import send_mail
        
        try:
            send_mail(
                subject='🛑 Account Suspended - Action Required',
                message=(
                    f"Your annotator account has been suspended due to an "
                    f"accuracy score of {accuracy:.1f}%, which is below our "
                    f"minimum threshold.\n\n"
                    f"To request reinstatement, please contact support at "
                    f"support@synapse-platform.com with:\n"
                    f"- Your username: {annotator.user.email}\n"
                    f"- A brief explanation\n"
                    f"- Your commitment to quality improvement\n\n"
                    f"Thank you for your understanding."
                ),
                from_email='noreply@synapse-platform.com',
                recipient_list=[annotator.user.email],
                fail_silently=True
            )
        except Exception as e:
            logger.error(f"Failed to send suspension email: {e}")
    
    @classmethod
    def _send_recovery_email(cls, annotator, accuracy):
        """Send recovery notification email."""
        from django.core.mail import send_mail
        
        try:
            send_mail(
                subject='✅ Account Restored - Great Job!',
                message=(
                    f"Congratulations! Your annotation accuracy has improved to "
                    f"{accuracy:.1f}%.\n\n"
                    f"Your account is now in good standing and you will receive "
                    f"task assignments as normal.\n\n"
                    f"Keep up the great work!\n\n"
                    f"- The Synapse Team"
                ),
                from_email='noreply@synapse-platform.com',
                recipient_list=[annotator.user.email],
                fail_silently=True
            )
        except Exception as e:
            logger.error(f"Failed to send recovery email: {e}")
```

### 5.3 Warning Model

```python
class AnnotatorWarning(models.Model):
    """
    Track warnings issued to annotators.
    """
    
    WARNING_TYPES = [
        ('soft_warning', 'Soft Warning'),
        ('formal_warning', 'Formal Warning'),
        ('final_warning', 'Final Warning'),
        ('suspension', 'Suspension'),
        ('recovery', 'Recovery'),
    ]
    
    annotator = models.ForeignKey(
        AnnotatorProfile, 
        on_delete=models.CASCADE, 
        related_name='warnings'
    )
    warning_type = models.CharField(max_length=20, choices=WARNING_TYPES)
    accuracy_at_warning = models.DecimalField(max_digits=5, decimal_places=2)
    message = models.TextField()
    
    # Email tracking
    email_sent = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    
    # Acknowledgment (optional - for compliance tracking)
    acknowledged = models.BooleanField(default=False)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'annotator_warning'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['annotator', 'warning_type']),
            models.Index(fields=['created_at']),
        ]
```

---

## Phase 6: Admin Dashboard API

### 6.1 Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/admin/honeypots/overview` | GET | System-wide stats |
| `/api/admin/honeypots/project/{id}/stats` | GET | Project stats |
| `/api/admin/honeypots/project/{id}/golden-standards` | GET/POST | Manage golden standards |
| `/api/admin/honeypots/annotator/{id}/history` | GET | Annotator honeypot history |
| `/api/admin/honeypots/warnings` | GET | Active warnings list |
| `/api/admin/honeypots/flagged` | GET | Flagged annotators |

### 6.2 Dashboard Overview Response

```json
{
    "system_stats": {
        "total_honeypot_evaluations": 15234,
        "evaluations_today": 342,
        "system_average_accuracy": 87.3,
        "pass_rate": 91.2
    },
    "annotator_distribution": {
        "healthy": {"count": 847, "percentage": 78},
        "soft_warning": {"count": 156, "percentage": 14},
        "formal_warning": {"count": 65, "percentage": 6},
        "final_warning": {"count": 18, "percentage": 2},
        "suspended": {"count": 4, "percentage": 0}
    },
    "recent_warnings": [
        {
            "time": "2026-02-06T12:45:00Z",
            "type": "soft_warning",
            "annotator_email": "user123@example.com",
            "accuracy": 72.3
        }
    ],
    "projects_needing_golden_standards": [
        {"project_id": 123, "name": "Image Classification", "golden_count": 3}
    ]
}
```

---

## Implementation Checklist

### New Models

- [ ] `GoldenStandardTask` - Store verified ground truth
- [ ] `HoneypotAssignment` - Track honeypot assignments (internal)
- [ ] `AccuracyHistory` - Daily accuracy snapshots (lifetime + rolling)
- [ ] `AnnotatorWarning` - Warning records

### Existing Model Updates

- [ ] `AnnotatorProfile` - Add `total_honeypots_evaluated` field
- [ ] `TrustLevel` - Add `rolling_accuracy` field

### New Services

- [ ] `HoneypotInjector` - Inject during assignment
- [ ] `HoneypotEvaluator` - Compare to ground truth
- [ ] `AnnotatorAccuracyTracker` - Dual accuracy calculation (lifetime + rolling)
- [ ] `WarningSystem` - Issue warnings and handle recovery

### Integration Points

- [ ] `AssignmentService.assign_tasks()` - Call HoneypotInjector
- [ ] Annotation submission handler - Route honeypots to evaluator
- [ ] Remove client-configurable honeypot settings from UI/API
- [ ] Daily cron job for AccuracyHistory snapshots

### Migrations

- [ ] Add new models
- [ ] Add new fields to existing models
- [ ] Migrate existing `HoneypotTask` data to `GoldenStandardTask`
- [ ] Remove deprecated project honeypot config fields

### Tests

- [ ] Unit tests for HoneypotInjector
- [ ] Unit tests for HoneypotEvaluator (all annotation types)
- [ ] Unit tests for WarningSystem thresholds
- [ ] Unit tests for dual accuracy calculation
- [ ] Integration tests for full flow

---

## Key Differences from v1

| Aspect | v1 (Old) | v2 (New) |
|--------|----------|----------|
| Injection timing | At task retrieval | At task assignment |
| Client control | Yes (injection rate, etc.) | No (system-controlled) |
| Injection method | Random check each request | Pre-planned positions |
| Tracking | Via TaskAssignment flags | Dedicated HoneypotAssignment table |
| Consolidation | Honeypots went through | Honeypots intercepted, skipped |
| Warnings | Basic fraud flags | Tiered email warning system |
| Profile accuracy | Rolling window | **Lifetime average** (fair long-term view) |
| Warning accuracy | Rolling window | Rolling window (catches recent drops) |
| Recovery | Manual | Automatic with threshold |

---

## Security & Anti-Gaming

1. **Internal-only tables** - `HoneypotAssignment` never exposed to annotator API
2. **No visual indicators** - Honeypot tasks look identical to regular tasks
3. **Randomized intervals** - Positions vary within min/max bounds
4. **Retirement system** - Golden standards retired after N uses to prevent memorization
5. **Audit logging** - All evaluations logged for review

---

## Success Metrics

| Metric | Target |
|--------|--------|
| System-wide accuracy | ≥ 85% |
| False positive rate | < 2% |
| Detection time (poor performer) | < 20 honeypots |
| Warning email open rate | > 70% |
| Recovery rate after warning | > 60% |
| Honeypot pool coverage | ≥ 10 per project |

---

## Next Steps

1. Review and approve this plan
2. Create database migrations
3. Implement core services
4. Integrate with assignment flow
5. Integrate with submission flow  
6. Build admin dashboard
7. Create email templates
8. Write tests
9. Deploy to staging
10. Monitor and iterate
