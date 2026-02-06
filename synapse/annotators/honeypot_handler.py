"""
Honeypot Handler Service v2.0

Main integration point for the honeypot system.
Ties together injection, evaluation, and accuracy tracking.

This service intercepts annotation submissions to:
1. Detect if the task is a honeypot
2. Evaluate accuracy against golden standard
3. Update annotator metrics (lifetime + rolling accuracy)
4. Trigger warning system if needed
"""

import logging
from decimal import Decimal
from typing import Optional, Dict, Any, Tuple

from django.db import transaction
from django.utils import timezone

from .models import (
    AnnotatorProfile,
    TrustLevel,
    HoneypotAssignment,
    GoldenStandardTask,
)
from .honeypot_evaluator import HoneypotEvaluator
from .accuracy_tracker import AccuracyTracker

logger = logging.getLogger(__name__)


class HoneypotHandler:
    """
    Handles honeypot evaluation and integration with annotation workflow.
    
    Called from AnnotationWorkflowService.on_annotation_created() to:
    - Detect if annotation is for a honeypot task
    - Evaluate and update accuracy metrics
    - Determine if normal workflow should continue
    """
    
    @classmethod
    def is_honeypot_task(cls, task) -> bool:
        """
        Check if a task is a honeypot (injected test task).
        
        Honeypot tasks are tracked via HoneypotAssignment records.
        """
        return HoneypotAssignment.objects.filter(
            shadow_task=task,
            evaluated=False
        ).exists()
    
    @classmethod
    def get_honeypot_assignment(
        cls,
        task,
        profile: AnnotatorProfile
    ) -> Optional[HoneypotAssignment]:
        """
        Get the honeypot assignment for this task+annotator.
        
        Returns None if not a honeypot or wrong annotator.
        """
        return HoneypotAssignment.objects.filter(
            task_assignment__task=task,
            annotator=profile,
            status='pending'
        ).first()
    
    @classmethod
    @transaction.atomic
    def handle_annotation_submission(
        cls,
        annotation,
        user
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Handle annotation submission - check if honeypot and evaluate.
        
        Args:
            annotation: The submitted annotation
            user: The user who submitted it
            
        Returns:
            (is_honeypot, result_dict)
            - is_honeypot: True if this was a honeypot task
            - result_dict: Contains evaluation results if honeypot
        """
        task = annotation.task
        
        # Check if user is an annotator
        try:
            profile = user.annotator_profile
        except AnnotatorProfile.DoesNotExist:
            return False, {}
        
        # Check if this is a honeypot task
        honeypot_assignment = cls.get_honeypot_assignment(task, profile)
        
        if not honeypot_assignment:
            # Not a honeypot - continue normal workflow
            return False, {}
        
        logger.info(
            f"Honeypot submission detected: task={task.id}, "
            f"annotator={user.email}"
        )
        
        # Get the annotation result
        annotation_result = annotation.result or []
        
        # Evaluate against golden standard
        evaluation = HoneypotEvaluator.evaluate(
            honeypot_assignment=honeypot_assignment,
            annotator_result=annotation_result
        )
        
        # Update honeypot assignment with results
        honeypot_assignment.annotator_result = annotation_result
        honeypot_assignment.accuracy_score = Decimal(
            str(round(evaluation['accuracy_score'], 2))
        )
        honeypot_assignment.passed = evaluation['passed']
        honeypot_assignment.evaluation_details = evaluation['details']
        honeypot_assignment.status = 'evaluated'
        honeypot_assignment.submitted_at = timezone.now()
        honeypot_assignment.save()
        
        logger.info(
            f"Honeypot evaluated: score={evaluation['accuracy_score']:.1f}%, "
            f"passed={evaluation['passed']}"
        )
        
        # Get trust level for this annotator
        try:
            trust_level = profile.trust_level
        except TrustLevel.DoesNotExist:
            # Create default trust level
            trust_level = TrustLevel.objects.create(
                annotator=profile,
                level='new',
            )
        
        # Update accuracy metrics (both lifetime and rolling)
        accuracy_result = AccuracyTracker.record_evaluation(
            profile=profile,
            trust_level=trust_level,
            accuracy_score=evaluation['accuracy_score'],
            passed=evaluation['passed']
        )
        
        return True, {
            'evaluation': evaluation,
            'accuracy_update': accuracy_result,
            'honeypot_assignment_id': honeypot_assignment.id,
        }
    
    @classmethod
    def should_skip_consolidation(cls, task) -> bool:
        """
        Check if this task should skip consolidation.
        
        Honeypots are NOT consolidated - they're only for quality monitoring.
        """
        return HoneypotAssignment.objects.filter(
            task_assignment__task=task
        ).exists()
    
    @classmethod
    def get_annotator_honeypot_stats(
        cls,
        profile: AnnotatorProfile,
        project=None
    ) -> Dict[str, Any]:
        """
        Get honeypot statistics for an annotator.
        
        Useful for dashboard displays.
        """
        query = HoneypotAssignment.objects.filter(
            annotator=profile,
            status='evaluated'
        )
        
        if project:
            query = query.filter(golden_standard__task__project=project)
        
        total = query.count()
        passed = query.filter(passed=True).count()
        
        if total == 0:
            return {
                'total_honeypots': 0,
                'passed': 0,
                'failed': 0,
                'pass_rate': None,
                'average_accuracy': None,
            }
        
        from django.db.models import Avg
        avg_accuracy = query.aggregate(
            avg=Avg('accuracy_score')
        )['avg'] or 0
        
        return {
            'total_honeypots': total,
            'passed': passed,
            'failed': total - passed,
            'pass_rate': (passed / total) * 100,
            'average_accuracy': float(avg_accuracy),
        }
    
    @classmethod
    def cleanup_stale_honeypots(cls, days_old: int = 7) -> int:
        """
        Clean up honeypot assignments that were never completed.
        
        These might occur if an annotator abandons tasks.
        
        Returns number of cleaned up records.
        """
        from datetime import timedelta
        
        cutoff = timezone.now() - timedelta(days=days_old)
        
        stale = HoneypotAssignment.objects.filter(
            evaluated=False,
            assigned_at__lt=cutoff
        )
        
        count = stale.count()
        
        if count > 0:
            stale.update(
                evaluated=True,
                evaluation_details={'status': 'abandoned'},
                accuracy_score=Decimal('0'),
                passed=False,
            )
            
            logger.info(f"Cleaned up {count} stale honeypot assignments")
        
        return count
