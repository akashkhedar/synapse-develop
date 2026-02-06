"""
Honeypot Injector Service v2.0

Injects honeypot (golden standard) tasks into assignment queues.
This is SYSTEM-CONTROLLED - no client configuration allowed.

The injector:
1. Calculates injection points using randomized intervals
2. Gets unseen golden standards for the annotator
3. Inserts honeypots at calculated positions
4. Creates HoneypotAssignment records (internal tracking)
"""

import logging
import random
from typing import List, Tuple, Optional
from django.db import transaction

from .models import (
    AnnotatorProfile,
    GoldenStandardTask,
    HoneypotAssignment,
    TaskAssignment,
)
from .honeypot_constants import (
    MIN_INTERVAL_TASKS,
    MAX_INTERVAL_TASKS,
    MIN_GOLDEN_STANDARDS_PER_PROJECT,
)

logger = logging.getLogger(__name__)


class HoneypotInjector:
    """
    Injects honeypot tasks into assignment queues.
    
    SYSTEM-CONTROLLED - No client configuration allowed.
    """
    
    @classmethod
    def inject_honeypots(
        cls,
        annotator: AnnotatorProfile,
        project,
        task_list: List,
    ) -> List[Tuple]:
        """
        Inject honeypot tasks into a task assignment list.
        
        Args:
            annotator: AnnotatorProfile
            project: Project
            task_list: List of Task objects to be assigned
            
        Returns:
            List of (Task, is_honeypot, golden_standard_or_none) tuples
            with honeypots injected at calculated positions.
        """
        if len(task_list) == 0:
            return []
        
        # Check if project has enough golden standards
        available_golden = cls._get_available_golden_standards(annotator, project)
        
        if len(available_golden) < 3:
            logger.warning(
                f"Project {project.id} has insufficient golden standards "
                f"({len(available_golden)} available, need at least 3). "
                f"Skipping honeypot injection."
            )
            # Return tasks without honeypots
            return [(task, False, None) for task in task_list]
        
        # Calculate where to inject honeypots
        injection_points = cls._calculate_injection_points(
            task_count=len(task_list),
            annotator=annotator,
            project=project
        )
        
        logger.debug(
            f"Calculated {len(injection_points)} injection points for "
            f"{annotator.user.email} in project {project.id}: {injection_points}"
        )
        
        if not injection_points:
            return [(task, False, None) for task in task_list]
        
        # Build mixed queue
        result = []
        task_idx = 0
        honeypot_idx = 0
        result_position = 0
        
        # Total items = regular tasks + honeypots
        total_items = len(task_list) + min(len(injection_points), len(available_golden))
        
        while result_position < total_items and task_idx < len(task_list):
            if (result_position in injection_points and 
                honeypot_idx < len(available_golden)):
                # Insert honeypot at this position
                golden = available_golden[honeypot_idx]
                result.append((golden.task, True, golden))
                honeypot_idx += 1
                logger.debug(
                    f"Injecting honeypot at position {result_position} "
                    f"(golden_id={golden.id})"
                )
            else:
                # Insert regular task
                result.append((task_list[task_idx], False, None))
                task_idx += 1
            
            result_position += 1
        
        # Add remaining regular tasks
        while task_idx < len(task_list):
            result.append((task_list[task_idx], False, None))
            task_idx += 1
        
        logger.info(
            f"Injected {honeypot_idx} honeypots into {len(task_list)} tasks "
            f"for {annotator.user.email} (project {project.id})"
        )
        
        return result
    
    @classmethod
    def _calculate_injection_points(
        cls,
        task_count: int,
        annotator: AnnotatorProfile,
        project
    ) -> List[int]:
        """
        Calculate positions where honeypots should be inserted.
        
        Uses randomized intervals within bounds to prevent pattern detection.
        """
        if task_count == 0:
            return []
        
        # Get how many tasks since annotator's last honeypot in this project
        tasks_since_last = cls._get_tasks_since_last_honeypot(annotator, project)
        
        # Calculate first injection point
        # Account for tasks already completed since last honeypot
        remaining_interval = max(0, MIN_INTERVAL_TASKS - tasks_since_last)
        
        injection_points = []
        current_pos = remaining_interval
        
        while current_pos < task_count:
            injection_points.append(current_pos)
            
            # Random interval for next honeypot (prevents predictability)
            next_interval = random.randint(MIN_INTERVAL_TASKS, MAX_INTERVAL_TASKS)
            current_pos += next_interval
        
        return injection_points
    
    @classmethod
    def _get_available_golden_standards(
        cls,
        annotator: AnnotatorProfile,
        project
    ) -> List[GoldenStandardTask]:
        """Get golden standards this annotator hasn't seen yet in this project."""
        # Get IDs of golden standards already shown to this annotator
        seen_ids = HoneypotAssignment.objects.filter(
            annotator=annotator,
            golden_standard__project=project
        ).values_list('golden_standard_id', flat=True)
        
        # Get active, non-retired golden standards not yet seen
        available = list(
            GoldenStandardTask.objects.filter(
                project=project,
                is_active=True,
                is_retired=False
            ).exclude(
                id__in=seen_ids
            ).order_by('?')[:10]  # Random selection, get up to 10
        )
        
        return available
    
    @classmethod
    def _get_tasks_since_last_honeypot(
        cls,
        annotator: AnnotatorProfile,
        project
    ) -> int:
        """Count regular tasks completed since last honeypot in this project."""
        # Get last evaluated honeypot for this annotator in this project
        last_honeypot = HoneypotAssignment.objects.filter(
            annotator=annotator,
            golden_standard__project=project,
            status='evaluated'
        ).order_by('-submitted_at').first()
        
        if not last_honeypot or not last_honeypot.submitted_at:
            return 999  # No previous honeypot, inject soon
        
        # Count completed assignments since last honeypot
        count = TaskAssignment.objects.filter(
            annotator=annotator,
            project=project,
            status='completed',
            completed_at__gt=last_honeypot.submitted_at
        ).count()
        
        return count
    
    @classmethod
    @transaction.atomic
    def create_honeypot_assignment(
        cls,
        annotator: AnnotatorProfile,
        golden_standard: GoldenStandardTask,
        task_assignment: TaskAssignment,
        position_in_queue: int = 0
    ) -> HoneypotAssignment:
        """
        Create a HoneypotAssignment record to track this honeypot.
        
        This should be called when creating the TaskAssignment for a honeypot task.
        """
        honeypot_assignment = HoneypotAssignment.objects.create(
            annotator=annotator,
            golden_standard=golden_standard,
            task_assignment=task_assignment,
            position_in_queue=position_in_queue,
        )
        
        logger.debug(
            f"Created HoneypotAssignment {honeypot_assignment.id} for "
            f"{annotator.user.email} (golden_id={golden_standard.id})"
        )
        
        return honeypot_assignment
    
    @classmethod
    def check_project_honeypot_readiness(cls, project) -> dict:
        """
        Check if a project has enough golden standards for honeypot injection.
        
        Returns dict with status and recommendations.
        """
        total = GoldenStandardTask.objects.filter(project=project).count()
        active = GoldenStandardTask.objects.filter(
            project=project,
            is_active=True,
            is_retired=False
        ).count()
        retired = GoldenStandardTask.objects.filter(
            project=project,
            is_retired=True
        ).count()
        
        is_ready = active >= MIN_GOLDEN_STANDARDS_PER_PROJECT
        
        return {
            'is_ready': is_ready,
            'total_golden_standards': total,
            'active_golden_standards': active,
            'retired_golden_standards': retired,
            'minimum_required': MIN_GOLDEN_STANDARDS_PER_PROJECT,
            'message': (
                f"Project is ready for honeypot injection" if is_ready 
                else f"Need at least {MIN_GOLDEN_STANDARDS_PER_PROJECT} active golden standards. "
                     f"Currently have {active}."
            )
        }
