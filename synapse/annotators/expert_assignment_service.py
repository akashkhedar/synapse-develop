"""
Expert Task Assignment Service

Handles intelligent assignment of tasks to experts based on:
- Disagreement level (high disagreement tasks prioritized)
- Random sampling for quality control
- Expert availability and workload
- Expertise matching
- Fair distribution across experts
"""

from decimal import Decimal
from django.db import transaction
from django.db.models import Count, Q, F, Avg
from django.utils import timezone
import logging
import random
from typing import Dict, List, Optional, Any
from datetime import timedelta

logger = logging.getLogger(__name__)


class ExpertAssignmentConfig:
    """Configuration for expert task assignment"""

    # Disagreement thresholds
    CRITICAL_DISAGREEMENT_THRESHOLD = 50  # <50% agreement - highest priority
    HIGH_DISAGREEMENT_THRESHOLD = 70  # 50-70% agreement - high priority
    MODERATE_DISAGREEMENT_THRESHOLD = 85  # 70-85% agreement - normal priority

    # Random sampling rates (percentage of tasks to sample)
    RANDOM_SAMPLE_RATE_HIGH_AGREEMENT = 5  # 5% of high-agreement tasks
    RANDOM_SAMPLE_RATE_MODERATE = 10  # 10% of moderate agreement

    # Assignment limits
    MAX_PENDING_TASKS_PER_EXPERT = 20
    MAX_TASKS_PER_DAY = 50

    # Priority weights for scoring
    PRIORITY_WEIGHTS = {
        "critical_disagreement": 100,
        "high_disagreement": 75,
        "moderate_disagreement": 50,
        "random_sample": 25,
        "flagged": 90,
        "manual_request": 80,
    }

    # Workload balancing
    WORKLOAD_PENALTY_FACTOR = 5  # Reduce score by 5 per pending task


class ExpertTaskAssignmentService:
    """
    Service for assigning tasks to experts for review.

    Uses a scoring system to prioritize:
    1. High disagreement tasks (most important)
    2. Flagged tasks (annotator/system flagged)
    3. Random samples (quality control)
    4. Balanced workload across experts
    """

    @classmethod
    def get_pending_tasks_for_assignment(cls, project=None, limit=100) -> List[Dict]:
        """
        Get tasks that need expert review but haven't been assigned yet.

        Args:
            project: Optional project to filter by
            limit: Maximum tasks to return

        Returns:
            List of task dicts with priority scores
        """
        from .models import TaskConsensus, ExpertReviewTask
        from tasks.models import Task

        # Get consensus records that need review
        query = (
            TaskConsensus.objects.filter(
                status__in=["review_required", "conflict", "consensus_reached"]
            )
            .exclude(
                # Exclude tasks already assigned to experts
                expert_reviews__status__in=["pending", "in_review"]
            )
            .select_related("task", "task__project")
        )

        if project:
            query = query.filter(task__project=project)

        pending_tasks = []

        for consensus in query[:limit]:
            avg_agreement = float(consensus.average_agreement or 100)

            # Calculate priority based on disagreement
            priority_score, assignment_reason = cls._calculate_priority_score(
                avg_agreement, consensus
            )

            if priority_score > 0:
                pending_tasks.append(
                    {
                        "consensus_id": consensus.id,
                        "task_id": consensus.task_id,
                        "project_id": consensus.task.project_id,
                        "project_title": consensus.task.project.title,
                        "average_agreement": avg_agreement,
                        "disagreement_score": 100 - avg_agreement,
                        "priority_score": priority_score,
                        "assignment_reason": assignment_reason,
                        "current_annotations": consensus.current_annotations,
                        "status": consensus.status,
                        "created_at": consensus.created_at.isoformat(),
                    }
                )

        # Sort by priority score (highest first)
        pending_tasks.sort(key=lambda x: x["priority_score"], reverse=True)

        return pending_tasks

    @classmethod
    def _calculate_priority_score(cls, avg_agreement: float, consensus) -> tuple:
        """Calculate priority score for a task"""
        config = ExpertAssignmentConfig

        # Critical disagreement - always assign
        if avg_agreement < config.CRITICAL_DISAGREEMENT_THRESHOLD:
            return (
                config.PRIORITY_WEIGHTS["critical_disagreement"],
                "critical_disagreement",
            )

        # High disagreement
        if avg_agreement < config.HIGH_DISAGREEMENT_THRESHOLD:
            return (config.PRIORITY_WEIGHTS["high_disagreement"], "high_disagreement")

        # Moderate disagreement
        if avg_agreement < config.MODERATE_DISAGREEMENT_THRESHOLD:
            # Check for random sampling
            if random.random() * 100 < config.RANDOM_SAMPLE_RATE_MODERATE:
                return (
                    config.PRIORITY_WEIGHTS["moderate_disagreement"],
                    "moderate_disagreement",
                )
            return (0, None)

        # High agreement - random sample for QC
        if random.random() * 100 < config.RANDOM_SAMPLE_RATE_HIGH_AGREEMENT:
            return (config.PRIORITY_WEIGHTS["random_sample"], "random_sample")

        # Status already indicates review needed
        if consensus.status in ["conflict", "review_required"]:
            return (config.PRIORITY_WEIGHTS["flagged"], "status_flagged")

        return (0, None)

    @classmethod
    def get_available_experts(
        cls, project=None, annotation_type: str = None
    ) -> List[Dict]:
        """
        Get experts available for task assignment.

        Args:
            project: Optional project to filter by assignment
            annotation_type: Optional annotation type to match expertise

        Returns:
            List of expert dicts with availability scores
        """
        from .models import ExpertProfile, ExpertProjectAssignment

        # Get active experts
        experts_query = ExpertProfile.objects.filter(status="active").select_related(
            "user"
        )

        # If project specified, filter to assigned experts
        if project:
            assigned_expert_ids = ExpertProjectAssignment.objects.filter(
                project=project, is_active=True
            ).values_list("expert_id", flat=True)

            experts_query = experts_query.filter(
                Q(id__in=assigned_expert_ids)
                | Q(
                    project_assignments__project__isnull=True,
                    project_assignments__is_active=True,
                )
            ).distinct()

        available_experts = []
        config = ExpertAssignmentConfig

        for expert in experts_query:
            # Check availability
            if not expert.is_available:
                continue

            # Check workload limits
            if expert.current_workload >= config.MAX_PENDING_TASKS_PER_EXPERT:
                continue

            # Check daily limit
            today_completed = expert.review_tasks.filter(
                completed_at__date=timezone.now().date()
            ).count()
            if today_completed >= config.MAX_TASKS_PER_DAY:
                continue

            # Check expertise match
            if annotation_type:
                if (
                    annotation_type not in expert.expertise_areas
                    and "all" not in expert.expertise_areas
                ):
                    continue

            # Calculate availability score
            availability_score = cls._calculate_expert_availability_score(expert)

            available_experts.append(
                {
                    "expert_id": expert.id,
                    "user_id": expert.user_id,
                    "email": expert.user.email,
                    "name": expert.user.get_full_name() or expert.user.username,
                    "expertise_level": expert.expertise_level,
                    "expertise_areas": expert.expertise_areas,
                    "current_workload": expert.current_workload,
                    "max_reviews_per_day": expert.max_reviews_per_day,
                    "today_completed": today_completed,
                    "availability_score": availability_score,
                    "approval_rate": float(expert.approval_rate),
                }
            )

        # Sort by availability score (highest first)
        available_experts.sort(key=lambda x: x["availability_score"], reverse=True)

        return available_experts

    @classmethod
    def _calculate_expert_availability_score(cls, expert) -> float:
        """
        Calculate availability score for an expert.
        Higher score = more available/suitable.
        """
        config = ExpertAssignmentConfig

        # Base score
        score = 100.0

        # Reduce score based on current workload
        score -= expert.current_workload * config.WORKLOAD_PENALTY_FACTOR

        # Boost score based on expertise level
        level_bonuses = {
            "junior_expert": 0,
            "senior_expert": 10,
            "lead_expert": 20,
        }
        score += level_bonuses.get(expert.expertise_level, 0)

        # Boost score based on approval rate (quality indicator)
        approval_rate = float(expert.approval_rate)
        if approval_rate > 90:
            score += 15
        elif approval_rate > 80:
            score += 10
        elif approval_rate > 70:
            score += 5

        return max(0, score)

    @classmethod
    @transaction.atomic
    def assign_task_to_expert(
        cls,
        task_consensus,
        expert=None,
        assignment_reason: str = "auto",
        manual: bool = False,
    ) -> Dict[str, Any]:
        """
        Assign a task to an expert for review.

        Args:
            task_consensus: TaskConsensus instance
            expert: Optional specific ExpertProfile (if None, auto-select)
            assignment_reason: Reason for assignment
            manual: Whether this is a manual assignment

        Returns:
            Dict with assignment result
        """
        from .models import ExpertProfile, ExpertReviewTask, ExpertProjectAssignment

        task = task_consensus.task
        project = task.project

        # Check if already assigned
        existing = ExpertReviewTask.objects.filter(
            task=task, status__in=["pending", "in_review"]
        ).first()

        if existing:
            return {
                "success": False,
                "error": "Task already assigned to an expert",
                "existing_assignment": existing.id,
            }

        # Select expert if not specified
        if not expert:
            annotation_type = task_consensus.consolidation_method or "default"
            available = cls.get_available_experts(
                project=project, annotation_type=annotation_type
            )

            if not available:
                return {
                    "success": False,
                    "error": "No available experts for this project",
                }

            # Use weighted random selection for fairness
            expert = cls._select_expert_weighted(available)
            if not expert:
                return {
                    "success": False,
                    "error": "Could not select an expert",
                }

        # Get project assignment if exists
        project_assignment = ExpertProjectAssignment.objects.filter(
            expert=expert, project=project, is_active=True
        ).first()

        # Calculate disagreement score
        avg_agreement = float(task_consensus.average_agreement or 100)
        disagreement_score = Decimal(str(100 - avg_agreement))

        # Create review task
        review_task = ExpertReviewTask.objects.create(
            expert=expert,
            task=task,
            task_consensus=task_consensus,
            project_assignment=project_assignment,
            status="pending",
            assignment_reason=(
                assignment_reason
                if manual
                else cls._get_assignment_reason(avg_agreement)
            ),
            disagreement_score=disagreement_score,
        )

        # Update expert workload
        expert.current_workload = F("current_workload") + 1
        expert.save(update_fields=["current_workload"])
        expert.refresh_from_db()

        # Update consensus status
        task_consensus.status = "review_required"
        task_consensus.save(update_fields=["status"])

        logger.info(
            f"✅ Assigned task {task.id} to expert {expert.user.email} "
            f"(reason: {review_task.assignment_reason}, disagreement: {disagreement_score}%)"
        )

        return {
            "success": True,
            "review_task_id": review_task.id,
            "task_id": task.id,
            "expert_id": expert.id,
            "expert_email": expert.user.email,
            "assignment_reason": review_task.assignment_reason,
            "disagreement_score": float(disagreement_score),
        }

    @classmethod
    def _select_expert_weighted(cls, available_experts: List[Dict]):
        """
        Select an expert using weighted random selection.
        Experts with higher availability scores have higher chance.
        """
        from .models import ExpertProfile

        if not available_experts:
            return None

        # Calculate weights based on availability score
        total_score = sum(e["availability_score"] for e in available_experts)

        if total_score <= 0:
            # Equal weight if all scores are 0
            selected = random.choice(available_experts)
        else:
            # Weighted random selection
            rand_val = random.uniform(0, total_score)
            cumulative = 0
            selected = available_experts[0]

            for expert_data in available_experts:
                cumulative += expert_data["availability_score"]
                if cumulative >= rand_val:
                    selected = expert_data
                    break

        return ExpertProfile.objects.get(id=selected["expert_id"])

    @classmethod
    def _get_assignment_reason(cls, avg_agreement: float) -> str:
        """Determine assignment reason based on agreement level"""
        config = ExpertAssignmentConfig

        if avg_agreement < config.CRITICAL_DISAGREEMENT_THRESHOLD:
            return "critical_disagreement"
        elif avg_agreement < config.HIGH_DISAGREEMENT_THRESHOLD:
            return "high_disagreement"
        elif avg_agreement < config.MODERATE_DISAGREEMENT_THRESHOLD:
            return "moderate_disagreement"
        else:
            return "random_sample"

    @classmethod
    @transaction.atomic
    def batch_assign_pending_tasks(
        cls, project=None, max_assignments: int = 50
    ) -> Dict[str, Any]:
        """
        Batch assign pending tasks to available experts.
        Called by a background job or manually triggered.

        Args:
            project: Optional project to limit assignments
            max_assignments: Maximum number of assignments to make

        Returns:
            Dict with assignment results
        """
        # Get pending tasks
        pending_tasks = cls.get_pending_tasks_for_assignment(
            project=project,
            limit=max_assignments * 2,  # Get more to account for failures
        )

        if not pending_tasks:
            return {
                "success": True,
                "assignments_made": 0,
                "message": "No pending tasks require expert review",
            }

        # Get available experts
        available_experts = cls.get_available_experts(project=project)

        if not available_experts:
            return {
                "success": False,
                "assignments_made": 0,
                "error": "No experts available",
                "pending_tasks": len(pending_tasks),
            }

        assignments_made = 0
        failed_assignments = 0
        results = []

        from .models import TaskConsensus

        for task_data in pending_tasks:
            if assignments_made >= max_assignments:
                break

            try:
                consensus = TaskConsensus.objects.get(id=task_data["consensus_id"])

                result = cls.assign_task_to_expert(
                    task_consensus=consensus,
                    assignment_reason=task_data["assignment_reason"],
                )

                if result["success"]:
                    assignments_made += 1
                    results.append(result)
                else:
                    failed_assignments += 1

            except Exception as e:
                logger.error(f"Failed to assign task {task_data['task_id']}: {e}")
                failed_assignments += 1

        logger.info(
            f"📋 Batch assignment complete: {assignments_made} assigned, "
            f"{failed_assignments} failed, {len(pending_tasks)} total pending"
        )

        return {
            "success": True,
            "assignments_made": assignments_made,
            "failed": failed_assignments,
            "remaining_pending": len(pending_tasks) - assignments_made,
            "assignments": results,
        }

    @classmethod
    def get_expert_task_queue(cls, expert) -> List[Dict]:
        """
        Get the task queue for a specific expert.
        Returns tasks ordered by priority.

        Args:
            expert: ExpertProfile instance

        Returns:
            List of pending review tasks
        """
        from .models import ExpertReviewTask

        pending_tasks = (
            ExpertReviewTask.objects.filter(
                expert=expert, status__in=["pending", "in_review"]
            )
            .select_related("task", "task__project", "task_consensus")
            .order_by("-disagreement_score", "-assigned_at")
        )

        task_queue = []
        for review_task in pending_tasks:
            task_queue.append(
                {
                    "review_task_id": review_task.id,
                    "task_id": review_task.task_id,
                    "project_id": review_task.task.project_id,
                    "project_title": review_task.task.project.title,
                    "status": review_task.status,
                    "assignment_reason": review_task.assignment_reason,
                    "disagreement_score": float(review_task.disagreement_score or 0),
                    "assigned_at": review_task.assigned_at.isoformat(),
                    "is_overdue": review_task.is_overdue,
                    "priority": cls._get_task_priority_label(review_task),
                    "consensus_status": (
                        review_task.task_consensus.status
                        if review_task.task_consensus
                        else None
                    ),
                    "annotations_count": (
                        review_task.task_consensus.current_annotations
                        if review_task.task_consensus
                        else 0
                    ),
                }
            )

        return task_queue

    @classmethod
    def _get_task_priority_label(cls, review_task) -> str:
        """Get human-readable priority label"""
        disagreement = float(review_task.disagreement_score or 0)

        if disagreement >= 50:
            return "critical"
        elif disagreement >= 30:
            return "high"
        elif disagreement >= 15:
            return "medium"
        else:
            return "low"

    @classmethod
    def get_assignment_stats(cls, project=None) -> Dict[str, Any]:
        """
        Get statistics about expert task assignments.

        Args:
            project: Optional project to filter by

        Returns:
            Dict with assignment statistics
        """
        from .models import ExpertReviewTask, ExpertProfile

        # Base query
        query = ExpertReviewTask.objects.all()
        if project:
            query = query.filter(task__project=project)

        # Status breakdown
        status_counts = query.values("status").annotate(count=Count("id"))
        status_dict = {s["status"]: s["count"] for s in status_counts}

        # Assignment reason breakdown
        reason_counts = query.values("assignment_reason").annotate(count=Count("id"))
        reason_dict = {r["assignment_reason"]: r["count"] for r in reason_counts}

        # Average disagreement by status
        avg_disagreement = query.filter(disagreement_score__isnull=False).aggregate(
            avg=Avg("disagreement_score")
        )["avg"]

        # Expert workload
        experts = ExpertProfile.objects.filter(status="active")
        workload_data = []
        for expert in experts[:20]:
            pending = query.filter(
                expert=expert, status__in=["pending", "in_review"]
            ).count()
            completed = query.filter(
                expert=expert, status__in=["approved", "rejected", "corrected"]
            ).count()
            workload_data.append(
                {
                    "expert_id": expert.id,
                    "email": expert.user.email,
                    "pending": pending,
                    "completed": completed,
                }
            )

        # Time-based stats
        today = timezone.now().date()
        today_assigned = query.filter(assigned_at__date=today).count()
        today_completed = query.filter(completed_at__date=today).count()

        return {
            "total_review_tasks": query.count(),
            "status_breakdown": {
                "pending": status_dict.get("pending", 0),
                "in_review": status_dict.get("in_review", 0),
                "approved": status_dict.get("approved", 0),
                "rejected": status_dict.get("rejected", 0),
                "corrected": status_dict.get("corrected", 0),
            },
            "assignment_reasons": reason_dict,
            "average_disagreement": float(avg_disagreement) if avg_disagreement else 0,
            "expert_workload": workload_data,
            "today": {
                "assigned": today_assigned,
                "completed": today_completed,
            },
        }





