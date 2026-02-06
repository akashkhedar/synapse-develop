"""
Expert Assignment Engine

Handles assignment of consolidated annotation tasks to experts for review.
This runs after the consolidation algorithm produces a consolidated annotation.

Key Features:
1. No expert levels - all experts are equal
2. Workload based on concurrent task count (not hourly)
3. Activity tracking with timeout and reactivation
4. Agreement-based assignment:
   - Agreement >= threshold: Always assign to expert
   - Agreement < threshold: Random selection for expert review

Cases:
1. No experts available → Hold task (pending_expert_review)
2. Experts available → Assign based on workload balance
"""

import logging
import random
from datetime import timedelta
from typing import Dict, List, Optional, Any

from django.db import models, transaction
from django.db.models import Count, F
from django.utils import timezone

from .models import ExpertProfile, ExpertReviewTask, ExpertProjectAssignment

logger = logging.getLogger(__name__)


# Configuration Constants
EXPERT_REVIEW_TIMEOUT_HOURS = 48  # Hours before review is considered stale
EXPERT_INACTIVITY_THRESHOLD_DAYS = 7  # Days of inactivity before marking inactive
AGREEMENT_THRESHOLD = 70  # Percentage - above this always goes to expert
RANDOM_SELECTION_RATE = 30  # Percentage - probability for low-agreement tasks to get expert review
DEFAULT_EXPERT_CAPACITY = 50  # Default max concurrent reviews per expert


class ExpertAssignmentEngine:
    """
    Engine for assigning consolidated tasks to experts for review.
    
    Simpler than the annotator assignment engine:
    - No overlap (1 expert per task)
    - No trust levels (all experts are equal)
    - Workload-based distribution
    - Activity tracking for staleness
    """
    
    @classmethod
    def get_eligible_experts(cls, project=None) -> List[ExpertProfile]:
        """
        Get all experts eligible for review assignments.
        
        Eligibility Criteria:
        1. Status = 'active'
        2. User is active
        3. is_active_for_assignments = True
        4. Has available capacity
        5. Has verified expertise matching project requirements (if specified)
        
        Args:
            project: Optional - filter by project assignment
            
        Returns:
            List of ExpertProfile instances sorted by workload (lowest first)
        """
        # Base query: active experts with active users
        eligible = ExpertProfile.objects.filter(
            status='active',
            user__is_active=True,
            is_active_for_assignments=True,
        ).select_related('user')
        
        # If project specified, filter by project assignment
        if project:
            assigned_expert_ids = ExpertProjectAssignment.objects.filter(
                project=project,
                is_active=True,
            ).values_list('expert_id', flat=True)
            
            # Include both project-assigned experts and experts with no specific assignments
            eligible = eligible.filter(
                models.Q(id__in=assigned_expert_ids) |
                ~models.Q(project_assignments__is_active=True)
            ).distinct()
            
            # ================================================================
            # EXPERTISE-BASED FILTERING FOR EXPERT REVIEW
            # Filter experts by expertise if project requires it
            # ================================================================
            expertise_required = getattr(project, "expertise_required", False)
            required_category = getattr(project, "required_expertise_category", None)
            required_specialization = getattr(project, "required_expertise_specialization", None)
            
            if expertise_required and (required_category or required_specialization):
                from .models import ExpertExpertise
                
                # Build expertise filter query for experts
                expertise_query = ExpertExpertise.objects.filter(
                    status='active'  # Only active expertise counts for experts
                )
                
                if required_specialization:
                    # If specialization is specified, filter by exact specialization
                    expertise_query = expertise_query.filter(
                        specialization=required_specialization
                    )
                elif required_category:
                    # If only category is specified, any specialization in that category works
                    expertise_query = expertise_query.filter(
                        category=required_category
                    )
                
                # Get expert IDs with matching active expertise
                eligible_expert_ids = expertise_query.values_list('expert_id', flat=True)
                
                # Filter experts to only those with matching expertise
                eligible = eligible.filter(id__in=eligible_expert_ids)
                
                logger.info(
                    f"[ExpertExpertiseFilter] Project {project.id} requires expertise "
                    f"(category={required_category}, specialization={required_specialization}). "
                    f"Filtered to {eligible.count()} eligible experts."
                )
        
        # Filter by capacity
        eligible_list = []
        for expert in eligible:
            if expert.available_capacity > 0:
                eligible_list.append(expert)
        
        # Sort by workload (lowest first for fair distribution)
        eligible_list.sort(key=lambda e: e.current_workload)
        
        return eligible_list
    
    @classmethod
    def check_expert_capacity(cls, expert: ExpertProfile) -> Dict[str, Any]:
        """
        Check expert's current capacity.
        
        Returns dict with:
        - current: Current active reviews
        - maximum: Max concurrent reviews
        - available: Remaining capacity
        - at_capacity: Boolean if at max
        """
        # Get actual pending count from database
        active_count = ExpertReviewTask.objects.filter(
            expert=expert,
            status__in=['pending', 'in_review']
        ).count()
        
        max_reviews = expert.max_concurrent_reviews or DEFAULT_EXPERT_CAPACITY
        
        return {
            'current': active_count,
            'maximum': max_reviews,
            'available': max(0, max_reviews - active_count),
            'at_capacity': active_count >= max_reviews,
        }
    
    @classmethod
    def should_assign_to_expert(cls, agreement_score: float) -> tuple:
        """
        Determine if a consolidated task should be assigned to expert.
        
        Logic:
        - If agreement >= AGREEMENT_THRESHOLD: Always assign (return True)
        - If agreement < AGREEMENT_THRESHOLD: Random selection
        
        Args:
            agreement_score: Agreement percentage (0-100)
            
        Returns:
            tuple of (should_assign: bool, reason: str)
        """
        if agreement_score >= AGREEMENT_THRESHOLD:
            return True, 'high_agreement'
        
        # Low agreement - random selection
        if random.random() * 100 < RANDOM_SELECTION_RATE:
            return True, 'random_sample'
        
        return False, 'skipped'
    
    @classmethod
    @transaction.atomic
    def assign_task_to_expert(
        cls,
        task_consensus,
        expert: ExpertProfile = None,
        force: bool = False,
    ) -> Dict[str, Any]:
        """
        Assign a consolidated task to an expert for review.
        
        Args:
            task_consensus: TaskConsensus instance (consolidated result)
            expert: Optional - specific expert (if None, auto-select)
            force: If True, skip agreement check and always assign
            
        Returns:
            Dict with assignment result
        """
        from .models import TaskConsensus
        
        task = task_consensus.task
        project = task.project
        
        # Check if already assigned
        existing = ExpertReviewTask.objects.filter(
            task=task,
            status__in=['pending', 'in_review']
        ).first()
        
        if existing:
            return {
                'success': False,
                'error': 'Task already assigned to an expert',
                'existing_assignment_id': existing.id,
                'expert_email': existing.expert.user.email,
            }
        
        # Check if should assign (agreement-based)
        agreement_score = float(task_consensus.average_agreement or 100)
        
        if not force:
            should_assign, reason = cls.should_assign_to_expert(agreement_score)
            if not should_assign:
                return {
                    'success': True,
                    'assigned': False,
                    'reason': reason,
                    'message': f'Task skipped - {reason} (agreement: {agreement_score:.1f}%)',
                }
        else:
            reason = 'forced'
        
        # Get expert if not specified
        if not expert:
            eligible = cls.get_eligible_experts(project=project)
            
            if not eligible:
                # CASE 1: No experts available - hold task
                logger.warning(
                    f"[ExpertAssignment] No eligible experts for task {task.id}. Task held."
                )
                return {
                    'success': True,
                    'assigned': False,
                    'status': 'waiting',
                    'reason': 'no_experts',
                    'message': 'No experts available. Task held for later assignment.',
                }
            
            # Select expert with lowest workload
            expert = eligible[0]
        
        # Check capacity
        capacity = cls.check_expert_capacity(expert)
        if capacity['at_capacity']:
            return {
                'success': False,
                'error': f'Expert {expert.user.email} is at capacity ({capacity["current"]}/{capacity["maximum"]})',
            }
        
        # Get project assignment if exists
        project_assignment = ExpertProjectAssignment.objects.filter(
            expert=expert,
            project=project,
            is_active=True,
        ).first()
        
        # Calculate disagreement score
        disagreement_score = 100 - agreement_score
        
        # Create the review task
        review_task = ExpertReviewTask.objects.create(
            expert=expert,
            task=task,
            task_consensus=task_consensus,
            project_assignment=project_assignment,
            status='pending',
            assignment_reason=reason,
            disagreement_score=disagreement_score,
        )
        
        # Update expert workload
        expert.current_workload = F('current_workload') + 1
        expert.save(update_fields=['current_workload'])
        expert.refresh_from_db()
        
        # Update consensus status
        task_consensus.status = 'review_required'
        task_consensus.save(update_fields=['status'])
        
        logger.info(
            f"[ExpertAssignment] Assigned task {task.id} to expert {expert.user.email} "
            f"(reason: {reason}, agreement: {agreement_score:.1f}%)"
        )
        
        return {
            'success': True,
            'assigned': True,
            'review_task_id': review_task.id,
            'task_id': task.id,
            'expert_id': expert.id,
            'expert_email': expert.user.email,
            'assignment_reason': reason,
            'agreement_score': agreement_score,
        }
    
    @classmethod
    @transaction.atomic
    def batch_assign_pending_tasks(
        cls,
        project=None,
        max_assignments: int = 50,
    ) -> Dict[str, Any]:
        """
        Batch assign pending consolidated tasks to experts.
        
        Args:
            project: Optional - only assign for this project
            max_assignments: Maximum assignments to make
            
        Returns:
            Dict with batch results
        """
        from .models import TaskConsensus
        
        # Get eligible experts first
        eligible_experts = cls.get_eligible_experts(project=project)
        
        if not eligible_experts:
            return {
                'success': True,
                'assignments_made': 0,
                'reason': 'no_experts',
                'message': 'No eligible experts available',
            }
        
        # Get pending tasks needing expert review
        query = TaskConsensus.objects.filter(
            status__in=['review_required', 'conflict', 'consensus_reached']
        ).exclude(
            expert_reviews__status__in=['pending', 'in_review']
        ).select_related('task', 'task__project')
        
        if project:
            query = query.filter(task__project=project)
        
        assignments_made = 0
        skipped = 0
        failed = 0
        results = []
        
        for consensus in query[:max_assignments * 2]:  # Get extra to account for skips
            if assignments_made >= max_assignments:
                break
            
            try:
                result = cls.assign_task_to_expert(
                    task_consensus=consensus,
                    force=False,
                )
                
                if result.get('assigned'):
                    assignments_made += 1
                    results.append(result)
                elif result.get('reason') == 'skipped':
                    skipped += 1
                elif result.get('reason') == 'no_experts':
                    # Stop if no experts
                    break
                    
            except Exception as e:
                logger.error(f"[ExpertAssignment] Failed to assign task: {e}")
                failed += 1
        
        logger.info(
            f"[ExpertAssignment] Batch complete: {assignments_made} assigned, "
            f"{skipped} skipped, {failed} failed"
        )
        
        return {
            'success': True,
            'assignments_made': assignments_made,
            'skipped': skipped,
            'failed': failed,
            'results': results,
        }
    
    @classmethod
    def handle_review_timeout(cls, review_task: ExpertReviewTask) -> str:
        """
        Handle review timeout with activity-based logic.
        
        Logic:
        1. If expert was active since assignment: Extend timer
        2. If expert inactive for > INACTIVITY_THRESHOLD_DAYS: Mark inactive, release all
        3. Otherwise: Release this review, reassign
        
        Args:
            review_task: ExpertReviewTask instance
            
        Returns:
            str: 'extended', 'marked_inactive', or 'released'
        """
        expert = review_task.expert
        now = timezone.now()
        
        # Check if expert has been active since assignment
        if expert.last_active and expert.last_active > review_task.assigned_at:
            # Expert is active, just hasn't reached this task
            review_task.assigned_at = now
            review_task.save(update_fields=['assigned_at'])
            logger.info(
                f"[ExpertTimeout] Extended timeout for active expert {expert.id} "
                f"on task {review_task.task_id}"
            )
            return 'extended'
        
        # Check for prolonged inactivity
        inactivity_cutoff = now - timedelta(days=EXPERT_INACTIVITY_THRESHOLD_DAYS)
        
        if not expert.last_active or expert.last_active < inactivity_cutoff:
            # Expert hasn't been active for too long
            logger.warning(
                f"[ExpertTimeout] Marking expert {expert.id} as inactive "
                f"(last active: {expert.last_active})"
            )
            cls._mark_expert_inactive(expert)
            cls._release_all_pending_reviews(expert)
            return 'marked_inactive'
        
        # Normal timeout - release just this review
        cls._release_review(review_task)
        cls._trigger_task_reassignment(review_task.task_consensus)
        
        return 'released'
    
    @classmethod
    def _mark_expert_inactive(cls, expert: ExpertProfile):
        """Mark expert as inactive"""
        expert.mark_inactive()
        logger.info(f"[ExpertInactive] Expert {expert.id} marked as inactive")
    
    @classmethod
    def _release_all_pending_reviews(cls, expert: ExpertProfile):
        """Release all pending reviews for an expert"""
        pending = ExpertReviewTask.objects.filter(
            expert=expert,
            status__in=['pending', 'in_review']
        )
        
        count = pending.count()
        
        for review in pending:
            cls._release_review(review)
            cls._trigger_task_reassignment(review.task_consensus)
        
        logger.info(
            f"[ExpertInactive] Released {count} pending reviews for expert {expert.id}"
        )
    
    @classmethod
    def _release_review(cls, review_task: ExpertReviewTask):
        """Release a single review task"""
        review_task.status = 'expired'
        review_task.save(update_fields=['status'])
        
        # Decrement expert workload
        ExpertProfile.objects.filter(id=review_task.expert_id).update(
            current_workload=F('current_workload') - 1
        )
    
    @classmethod
    def _trigger_task_reassignment(cls, task_consensus):
        """Trigger reassignment for a single task"""
        project = task_consensus.task.project
        eligible = cls.get_eligible_experts(project=project)
        
        if not eligible:
            logger.warning(
                f"[ExpertReassign] No eligible experts for task {task_consensus.task_id}"
            )
            return
        
        # Assign to expert with lowest workload
        expert = eligible[0]
        
        try:
            result = cls.assign_task_to_expert(
                task_consensus=task_consensus,
                expert=expert,
                force=True,  # Force since it was already in review
            )
            
            if result.get('assigned'):
                logger.info(
                    f"[ExpertReassign] Reassigned task {task_consensus.task_id} "
                    f"to expert {expert.user.email}"
                )
        except Exception as e:
            logger.error(
                f"[ExpertReassign] Failed to reassign task {task_consensus.task_id}: {e}"
            )
    
    @classmethod
    def check_and_process_timeouts(cls, project=None):
        """
        Check for timed out reviews and process them.
        
        Args:
            project: Optional - only check for this project
        """
        timeout_cutoff = timezone.now() - timedelta(hours=EXPERT_REVIEW_TIMEOUT_HOURS)
        
        queryset = ExpertReviewTask.objects.filter(
            status__in=['pending', 'in_review'],
            assigned_at__lt=timeout_cutoff,
        ).select_related('expert', 'task', 'task_consensus')
        
        if project:
            queryset = queryset.filter(task__project=project)
        
        extended = 0
        released = 0
        marked_inactive = 0
        
        for review in queryset:
            result = cls.handle_review_timeout(review)
            
            if result == 'extended':
                extended += 1
            elif result == 'released':
                released += 1
            elif result == 'marked_inactive':
                marked_inactive += 1
        
        if extended + released + marked_inactive > 0:
            logger.info(
                f"[ExpertTimeout] Processed timeouts: {extended} extended, "
                f"{released} released, {marked_inactive} marked inactive"
            )
        
        return {
            'extended': extended,
            'released': released,
            'marked_inactive': marked_inactive,
        }
    
    @classmethod
    def reactivate_expert_on_login(cls, expert: ExpertProfile):
        """
        Reactivate expert when they log in.
        
        Called from signal handler when expert logs in.
        """
        was_inactive = not expert.is_active_for_assignments
        
        expert.reactivate_on_login()
        
        if was_inactive:
            logger.info(
                f"[ExpertReactivation] Expert {expert.id} reactivated on login"
            )
            # Trigger assignment of pending tasks
            cls.batch_assign_pending_tasks(max_assignments=10)
    
    @classmethod
    def on_expert_review_complete(cls, expert: ExpertProfile, review_task: ExpertReviewTask):
        """
        Called when expert completes a review.
        
        Updates workload and triggers new assignment.
        """
        # Update workload (already decremented when review completed)
        expert.update_last_active()
        
        # Try to assign next task
        project = review_task.task.project
        eligible = cls.get_eligible_experts(project=project)
        
        if expert in eligible:
            # Expert still has capacity, try to assign next task
            cls.batch_assign_pending_tasks(project=project, max_assignments=1)
    
    @classmethod
    def get_expert_workload_stats(cls, project=None) -> Dict[str, Any]:
        """
        Get workload statistics for all experts.
        
        Returns distribution info for monitoring.
        """
        eligible = cls.get_eligible_experts(project=project)
        
        stats = []
        for expert in eligible:
            capacity = cls.check_expert_capacity(expert)
            stats.append({
                'expert_id': expert.id,
                'email': expert.user.email,
                'current': capacity['current'],
                'maximum': capacity['maximum'],
                'available': capacity['available'],
                'at_capacity': capacity['at_capacity'],
                'last_active': expert.last_active.isoformat() if expert.last_active else None,
            })
        
        return {
            'total_experts': len(stats),
            'experts_with_capacity': len([s for s in stats if not s['at_capacity']]),
            'total_capacity': sum(s['available'] for s in stats),
            'total_workload': sum(s['current'] for s in stats),
            'experts': stats,
        }
