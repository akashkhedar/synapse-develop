"""
Expert Review Service

Handles:
- Expert assignment to projects and tasks
- Review task creation based on disagreement thresholds
- Expert payment calculations
- Review processing (approve/reject/correct)
"""

from decimal import Decimal
from django.db import transaction, models
from django.db.models import Avg, Count, Q, F, Sum
from django.utils import timezone
from datetime import timedelta
import logging
import random
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


# ============================================================================
# PAYMENT CONFIGURATION
# ============================================================================


class ExpertPaymentConfig:
    """Payment rates and configuration for experts"""

    # Base rates per review (in INR)
    BASE_REVIEW_RATES = {
        "classification": Decimal("5.0"),
        "bounding_box": Decimal("10.0"),
        "polygon": Decimal("15.0"),
        "segmentation": Decimal("25.0"),
        "keypoint": Decimal("15.0"),
        "ner": Decimal("8.0"),
        "default": Decimal("8.0"),
    }

    # Expertise level multipliers
    LEVEL_MULTIPLIERS = {
        "junior_expert": Decimal("1.0"),
        "senior_expert": Decimal("1.3"),
        "lead_expert": Decimal("1.5"),
    }

    # Action-based multipliers
    ACTION_MULTIPLIERS = {
        "approved": Decimal("1.0"),  # Simple approval
        "rejected": Decimal("1.2"),  # Rejection requires justification
        "corrected": Decimal("1.5"),  # Correction requires actual work
        "escalated": Decimal("0.8"),  # Escalation is less work
    }

    # Quality bonuses
    QUALITY_BONUSES = {
        "speed_bonus": Decimal("5.0"),  # Review under 2 minutes
        "accuracy_bonus": Decimal("10.0"),  # High consistency score
        "volume_bonus": Decimal("50.0"),  # 50+ reviews in a day
    }

    # Disagreement thresholds for auto-assignment
    HIGH_DISAGREEMENT_THRESHOLD = 30  # Below 30% agreement = high conflict
    MODERATE_DISAGREEMENT_THRESHOLD = 50  # Below 50% = moderate conflict

    # Sampling rates
    RANDOM_SAMPLE_RATE = 10  # 10% of tasks go to expert review even without conflict
    MINIMUM_PAYOUT = Decimal("100.0")  # Minimum payout amount


# ============================================================================
# EXPERT SERVICE
# ============================================================================


class ExpertService:
    """Main service for expert review management"""

    @classmethod
    @transaction.atomic
    def assign_expert_role(
        cls, user, assigned_by, expertise_level="junior_expert", expertise_areas=None
    ) -> Dict:
        """
        Assign expert role to a user (admin action).

        Args:
            user: User to assign expert role
            assigned_by: Admin user making the assignment
            expertise_level: junior_expert, senior_expert, lead_expert
            expertise_areas: List of annotation types they can review

        Returns:
            Dict with result
        """
        from .models import ExpertProfile

        if expertise_areas is None:
            expertise_areas = ["classification", "bounding_box", "ner"]

        # Check if already an expert
        expert, created = ExpertProfile.objects.get_or_create(
            user=user,
            defaults={
                "expertise_level": expertise_level,
                "expertise_areas": expertise_areas,
                "assigned_by": assigned_by,
                "status": "active",
            },
        )

        if not created:
            # Update existing expert
            expert.expertise_level = expertise_level
            expert.expertise_areas = expertise_areas
            expert.status = "active"
            expert.save(update_fields=["expertise_level", "expertise_areas", "status"])

        logger.info(f"Assigned expert role to {user.email} by {assigned_by.email}")

        return {
            "success": True,
            "created": created,
            "expert_id": expert.id,
            "user_email": user.email,
            "expertise_level": expertise_level,
        }

    @classmethod
    @transaction.atomic
    def revoke_expert_role(cls, user, revoked_by) -> Dict:
        """Revoke expert role from a user"""
        from .models import ExpertProfile

        try:
            expert = ExpertProfile.objects.get(user=user)
            expert.status = "inactive"
            expert.save(update_fields=["status"])

            logger.info(f"Revoked expert role from {user.email} by {revoked_by.email}")

            return {
                "success": True,
                "message": f"Expert role revoked from {user.email}",
            }

        except ExpertProfile.DoesNotExist:
            return {"success": False, "error": "User is not an expert"}

    @classmethod
    @transaction.atomic
    def assign_expert_to_project(
        cls,
        expert,
        project,
        assigned_by,
        review_all_tasks=False,
        sample_rate=100,
        priority=0,
    ) -> Dict:
        """
        Assign an expert to review tasks in a project.

        Args:
            expert: ExpertProfile instance
            project: Project instance
            assigned_by: User making the assignment
            review_all_tasks: If True, expert reviews all tasks, not just conflicts
            sample_rate: Percentage of tasks to assign (0-100)
            priority: Higher priority gets tasks first

        Returns:
            Dict with assignment result
        """
        from .models import ExpertProjectAssignment

        assignment, created = ExpertProjectAssignment.objects.get_or_create(
            expert=expert,
            project=project,
            defaults={
                "is_active": True,
                "review_all_tasks": review_all_tasks,
                "sample_rate": Decimal(str(sample_rate)),
                "priority": priority,
                "assigned_by": assigned_by,
            },
        )

        if not created:
            assignment.is_active = True
            assignment.review_all_tasks = review_all_tasks
            assignment.sample_rate = Decimal(str(sample_rate))
            assignment.priority = priority
            assignment.save()

        logger.info(f"Assigned expert {expert.user.email} to project {project.title}")

        return {
            "success": True,
            "assignment_id": assignment.id,
            "expert_email": expert.user.email,
            "project_title": project.title,
        }

    @classmethod
    def check_and_assign_expert_review(cls, task_consensus) -> Optional[Dict]:
        """
        Check if a task needs expert review based on agreement level.
        If needed, assign to an available expert using ExpertAssignmentEngine.

        Called after consensus processing.

        Args:
            task_consensus: TaskConsensus instance

        Returns:
            Dict with assignment result or None
        """
        from .expert_assignment_engine import ExpertAssignmentEngine
        
        try:
            # Use the new ExpertAssignmentEngine for assignment
            result = ExpertAssignmentEngine.assign_task_to_expert(
                task_consensus=task_consensus,
                force=False,
            )
            
            if result.get('assigned'):
                return {
                    "needs_review": True,
                    "assigned": True,
                    "review_task_id": result.get('review_task_id'),
                    "expert_email": result.get('expert_email'),
                    "reason": result.get('assignment_reason'),
                }
            elif result.get('reason') == 'no_experts':
                # Update consensus status to indicate review needed but no expert
                task_consensus.status = "review_required"
                task_consensus.save(update_fields=["status"])
                return {
                    "needs_review": True,
                    "assigned": False,
                    "reason": "No expert available",
                }
            elif result.get('reason') == 'skipped':
                # Task skipped expert review (low agreement, random selection passed)
                return None
            
            return result
            
        except Exception as e:
            logger.error(f"Error in check_and_assign_expert_review: {e}")
            return None

    @classmethod
    def _check_if_needs_review(cls, task_consensus) -> Dict:
        """Determine if task needs expert review"""
        avg_agreement = float(task_consensus.average_agreement or 0)

        # High disagreement - always needs review
        if avg_agreement < ExpertPaymentConfig.HIGH_DISAGREEMENT_THRESHOLD:
            return {
                "needs_review": True,
                "reason": "high_disagreement",
                "disagreement_score": Decimal(str(100 - avg_agreement)),
            }

        # Moderate disagreement - needs review
        if avg_agreement < ExpertPaymentConfig.MODERATE_DISAGREEMENT_THRESHOLD:
            return {
                "needs_review": True,
                "reason": "moderate_disagreement",
                "disagreement_score": Decimal(str(100 - avg_agreement)),
            }

        # Random sampling for quality control
        if random.random() * 100 < ExpertPaymentConfig.RANDOM_SAMPLE_RATE:
            return {
                "needs_review": True,
                "reason": "random_sample",
                "disagreement_score": Decimal(str(100 - avg_agreement)),
            }

        # Status already indicates conflict
        if task_consensus.status in ["conflict", "review_required"]:
            return {
                "needs_review": True,
                "reason": "status_conflict",
                "disagreement_score": Decimal(str(100 - avg_agreement)),
            }

        return {"needs_review": False}

    @classmethod
    def _find_available_expert(
        cls, project, task_consensus
    ) -> Optional["ExpertProjectAssignment"]:
        """Find an available expert for the project"""
        from .models import ExpertProjectAssignment

        # Get annotation type from consensus
        annotation_type = task_consensus.consolidation_method or "default"

        # Find experts assigned to this project
        assignments = (
            ExpertProjectAssignment.objects.filter(
                project=project,
                is_active=True,
                expert__status="active",
            )
            .select_related("expert")
            .order_by("-priority")
        )

        for assignment in assignments:
            expert = assignment.expert

            # Check if expert can handle this annotation type
            if (
                annotation_type not in expert.expertise_areas
                and "all" not in expert.expertise_areas
            ):
                continue

            # Check availability
            if not expert.is_available:
                continue

            # Check sample rate (random selection)
            if random.random() * 100 > float(assignment.sample_rate):
                continue

            return assignment

        # No project-specific expert, try global experts
        global_experts = (
            ExpertProjectAssignment.objects.filter(
                project__isnull=True,
                is_active=True,
                expert__status="active",
            )
            .select_related("expert")
            .order_by("-priority")
        )

        for assignment in global_experts:
            if assignment.expert.is_available:
                return assignment

        return None

    @classmethod
    @transaction.atomic
    def _create_review_task(
        cls, expert_assignment, task_consensus, reason, disagreement_score
    ) -> "ExpertReviewTask":
        """Create a review task for an expert"""
        from .models import ExpertReviewTask

        expert = expert_assignment.expert

        review_task = ExpertReviewTask.objects.create(
            expert=expert,
            task=task_consensus.task,
            task_consensus=task_consensus,
            project_assignment=expert_assignment,
            status="pending",
            assignment_reason=reason,
            disagreement_score=disagreement_score,
        )

        # Update expert workload
        expert.current_workload += 1
        expert.save(update_fields=["current_workload"])

        # Update consensus status
        task_consensus.status = "review_required"
        task_consensus.save(update_fields=["status"])

        logger.info(
            f"Created review task {review_task.id} for expert {expert.user.email} "
            f"(reason: {reason})"
        )

        return review_task

    @classmethod
    @transaction.atomic
    def process_expert_review(
        cls,
        review_task,
        action,
        reviewer_notes="",
        corrected_result=None,
        rejection_reason="",
    ) -> Dict:
        """
        Process an expert's review decision.

        Args:
            review_task: ExpertReviewTask instance
            action: approve, reject, correct, escalate
            reviewer_notes: Notes from the expert
            corrected_result: Corrected annotation if action is 'correct'
            rejection_reason: Reason if action is 'reject'

        Returns:
            Dict with result
        """
        from .models import ExpertEarningsTransaction

        expert = review_task.expert
        task_consensus = review_task.task_consensus

        # Update review task
        review_task.review_notes = reviewer_notes
        review_task.completed_at = timezone.now()

        if review_task.started_at:
            review_task.review_time_seconds = int(
                (review_task.completed_at - review_task.started_at).total_seconds()
            )

        if action == "approved":
            review_task.status = "approved"
            task_consensus.status = "finalized"
            task_consensus.finalized_at = timezone.now()
            task_consensus.reviewed_by = expert.user
            task_consensus.review_notes = reviewer_notes

            expert.total_approvals += 1

        elif action == "rejected":
            review_task.status = "rejected"
            review_task.rejection_reason = rejection_reason
            task_consensus.status = "conflict"  # Back to conflict for rework

            expert.total_rejections += 1

            # Send tasks back to annotators
            cls._send_back_for_rework(task_consensus, rejection_reason, reviewer_notes)

        elif action == "corrected":
            review_task.status = "corrected"
            review_task.corrected_result = corrected_result
            review_task.correction_summary = reviewer_notes

            # Update consensus with corrected result
            task_consensus.consolidated_result = corrected_result
            task_consensus.status = "finalized"
            task_consensus.finalized_at = timezone.now()
            task_consensus.reviewed_by = expert.user
            task_consensus.review_notes = f"Corrected by expert: {reviewer_notes}"

            expert.total_corrections += 1

        elif action == "escalated":
            review_task.status = "escalated"
            # Find a lead expert
            cls._escalate_to_lead(review_task)

        # Save updates
        review_task.save()
        task_consensus.save()

        # Update expert stats
        expert.total_reviews_completed += 1
        expert.current_workload = max(0, expert.current_workload - 1)
        expert.last_active = timezone.now()

        # Update average review time
        if expert.total_reviews_completed > 0:
            total_time = (
                expert.average_review_time * (expert.total_reviews_completed - 1)
                + review_task.review_time_seconds
            )
            expert.average_review_time = int(
                total_time / expert.total_reviews_completed
            )

        expert.save()

        # Process payment
        payment_result = cls._process_review_payment(review_task, action)

        # Release annotator payments if approved/corrected
        if action in ["approved", "corrected"]:
            cls._release_annotator_review_payments(task_consensus)

        # Update project assignment stats
        if review_task.project_assignment:
            assignment = review_task.project_assignment
            assignment.tasks_reviewed += 1
            if action == "approved":
                assignment.tasks_approved += 1
            elif action == "rejected":
                assignment.tasks_rejected += 1
            assignment.save()

        return {
            "success": True,
            "action": action,
            "review_task_id": review_task.id,
            "payment": payment_result,
            "task_status": task_consensus.status,
        }

    @classmethod
    def _send_back_for_rework(cls, task_consensus, rejection_reason, notes):
        """Send task back to annotators for rework"""
        from .models import TaskAssignment

        # Reset all assignments for this task
        TaskAssignment.objects.filter(
            task=task_consensus.task, status="completed"
        ).update(
            status="assigned",
            flagged_for_review=True,
            flag_reason=f"Expert rejected: {rejection_reason}. {notes}",
        )

        logger.info(
            f"Task {task_consensus.task_id} sent back for rework: {rejection_reason}"
        )

    @classmethod
    def _escalate_to_lead(cls, review_task):
        """Escalate task to a lead expert"""
        from .models import ExpertProfile, ExpertReviewTask

        # Find a lead expert
        lead_expert = (
            ExpertProfile.objects.filter(expertise_level="lead_expert", status="active")
            .exclude(id=review_task.expert_id)
            .first()
        )

        if lead_expert:
            # Create new review task for lead
            ExpertReviewTask.objects.create(
                expert=lead_expert,
                task=review_task.task,
                task_consensus=review_task.task_consensus,
                status="pending",
                assignment_reason="escalated",
                disagreement_score=review_task.disagreement_score,
                review_notes=f"Escalated from {review_task.expert.user.email}: {review_task.review_notes}",
            )

            lead_expert.current_workload += 1
            lead_expert.save(update_fields=["current_workload"])

            logger.info(
                f"Escalated task {review_task.task_id} to lead expert {lead_expert.user.email}"
            )

    @classmethod
    @transaction.atomic
    def _process_review_payment(cls, review_task, action) -> Dict:
        """Calculate and record payment for expert review"""
        from .models import ExpertEarningsTransaction

        expert = review_task.expert
        task = review_task.task

        # Detect annotation type
        annotation_type = cls._detect_annotation_type(task)

        # Base rate
        base_rate = ExpertPaymentConfig.BASE_REVIEW_RATES.get(
            annotation_type, ExpertPaymentConfig.BASE_REVIEW_RATES["default"]
        )

        # Level multiplier
        level_multiplier = ExpertPaymentConfig.LEVEL_MULTIPLIERS.get(
            expert.expertise_level, Decimal("1.0")
        )

        # Action multiplier
        action_multiplier = ExpertPaymentConfig.ACTION_MULTIPLIERS.get(
            action, Decimal("1.0")
        )

        # Calculate payment
        payment = base_rate * level_multiplier * action_multiplier

        # Check for bonuses
        bonuses = Decimal("0")

        # Speed bonus (under 2 minutes)
        if (
            review_task.review_time_seconds > 0
            and review_task.review_time_seconds < 120
        ):
            bonuses += ExpertPaymentConfig.QUALITY_BONUSES["speed_bonus"]

        # Volume bonus (check if this is 50th review today)
        today_reviews = expert.review_tasks.filter(
            completed_at__date=timezone.now().date()
        ).count()
        if today_reviews == 50:
            bonuses += ExpertPaymentConfig.QUALITY_BONUSES["volume_bonus"]

        total_payment = payment + bonuses

        # Update review task
        review_task.payment_amount = total_payment
        review_task.payment_released = True
        review_task.save(update_fields=["payment_amount", "payment_released"])

        # Update expert earnings (ensure Decimal types)
        expert.pending_payout = Decimal(str(expert.pending_payout)) + total_payment
        expert.total_earned = Decimal(str(expert.total_earned)) + total_payment
        expert.save(update_fields=["pending_payout", "total_earned"])

        # Create transaction
        ExpertEarningsTransaction.objects.create(
            expert=expert,
            transaction_type="review_payment",
            amount=total_payment,
            balance_after=expert.pending_payout,
            review_task=review_task,
            description=f"Review payment for task {task.id} ({action})",
            metadata={
                "task_id": task.id,
                "action": action,
                "base_rate": float(base_rate),
                "level_multiplier": float(level_multiplier),
                "action_multiplier": float(action_multiplier),
                "bonuses": float(bonuses),
                "review_time": review_task.review_time_seconds,
            },
        )

        logger.info(
            f"Processed expert payment for {expert.user.email}: ₹{total_payment}"
        )

        return {
            "amount": float(total_payment),
            "base_rate": float(base_rate),
            "bonuses": float(bonuses),
        }

    @classmethod
    def _detect_annotation_type(cls, task) -> str:
        """Detect annotation type from task"""
        try:
            # Try to get from consensus
            if hasattr(task, "consensus") and task.consensus.consolidation_method:
                method = task.consensus.consolidation_method.lower()
                if "bounding" in method or "rectangle" in method:
                    return "bounding_box"
                elif "polygon" in method:
                    return "polygon"
                elif "keypoint" in method:
                    return "keypoint"
                elif "brush" in method or "segment" in method:
                    return "segmentation"
                elif "ner" in method or "labels" in method:
                    return "ner"
                elif "class" in method or "choice" in method:
                    return "classification"

            # Try to get from annotations
            annotations = task.annotations.first()
            if annotations and annotations.result:
                result_str = str(annotations.result).lower()
                if "rectanglelabels" in result_str:
                    return "bounding_box"
                elif "polygonlabels" in result_str:
                    return "polygon"
                elif "keypointlabels" in result_str:
                    return "keypoint"
                elif "brushlabels" in result_str:
                    return "segmentation"
                elif "labels" in result_str:
                    return "ner"

        except Exception as e:
            logger.warning(f"Error detecting annotation type: {e}")

        return "default"

    @classmethod
    def _release_annotator_review_payments(cls, task_consensus):
        """Release final review payments (20%) for annotators when expert approves"""
        from .consensus_service import ConsensusService

        ConsensusService._release_review_payments(task_consensus)

    @classmethod
    def get_expert_dashboard_data(cls, expert) -> Dict:
        """Get dashboard data for an expert"""
        from .models import ExpertReviewTask

        # Pending tasks
        pending_tasks = (
            ExpertReviewTask.objects.filter(
                expert=expert, status__in=["pending", "in_review"]
            )
            .select_related("task", "task_consensus")
            .order_by("-assigned_at")
        )

        # Recent completed
        recent_completed = ExpertReviewTask.objects.filter(
            expert=expert, status__in=["approved", "rejected", "corrected"]
        ).order_by("-completed_at")[:10]

        # Today's stats
        today = timezone.now().date()
        today_tasks = ExpertReviewTask.objects.filter(
            expert=expert, completed_at__date=today
        )

        # Earnings this month
        month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0)
        monthly_earnings = ExpertReviewTask.objects.filter(
            expert=expert, payment_released=True, completed_at__gte=month_start
        ).aggregate(total=Sum("payment_amount"))["total"] or Decimal("0")

        return {
            "expert_id": expert.id,
            "status": expert.status,
            "expertise_level": expert.expertise_level,
            "expertise_areas": expert.expertise_areas,
            "pending_reviews": pending_tasks.count(),
            "pending_tasks": [
                {
                    "id": t.id,
                    "task_id": t.task_id,
                    "project_title": t.task.project.title,
                    "assignment_reason": t.assignment_reason,
                    "disagreement_score": float(t.disagreement_score or 0),
                    "assigned_at": t.assigned_at.isoformat(),
                    "is_overdue": t.is_overdue,
                }
                for t in pending_tasks[:20]
            ],
            "recent_completed": [
                {
                    "id": t.id,
                    "task_id": t.task_id,
                    "status": t.status,
                    "payment": float(t.payment_amount),
                    "completed_at": (
                        t.completed_at.isoformat() if t.completed_at else None
                    ),
                }
                for t in recent_completed
            ],
            "stats": {
                "total_reviews": expert.total_reviews_completed,
                "total_approvals": expert.total_approvals,
                "total_rejections": expert.total_rejections,
                "total_corrections": expert.total_corrections,
                "approval_rate": float(expert.approval_rate),
                "average_review_time": expert.average_review_time,
            },
            "today": {
                "reviews_completed": today_tasks.count(),
                "earnings": float(
                    today_tasks.aggregate(t=Sum("payment_amount"))["t"] or 0
                ),
            },
            "earnings": {
                "total_earned": float(expert.total_earned),
                "pending_payout": float(expert.pending_payout),
                "available_balance": float(expert.available_balance),
                "monthly_earnings": float(monthly_earnings),
            },
        }

    @classmethod
    def get_review_task_details(cls, review_task) -> Dict:
        """Get detailed information for a review task

        Returns the CONSOLIDATED annotation for expert review, along with:
        - Individual annotator performance metrics
        - Agreement scores between annotators
        - Original annotations for reference (if needed for correction)
        """
        from .models import AnnotatorAgreement, ConsensusQualityScore

        task = review_task.task
        consensus = review_task.task_consensus

        # Get individual annotator metrics (performance data, not full annotations)
        annotator_metrics = []
        for assignment in task.annotator_assignments.filter(status="completed"):
            if assignment.annotation:
                # Get quality score for this annotator
                quality_score_record = ConsensusQualityScore.objects.filter(
                    task_consensus=consensus, task_assignment=assignment
                ).first()

                annotator_metrics.append(
                    {
                        "annotator_id": assignment.annotator_id,
                        "annotator_email": assignment.annotator.user.email,
                        "quality_score": float(
                            quality_score_record.quality_score
                            if quality_score_record
                            else 0
                        ),
                        "peer_agreement": float(
                            quality_score_record.peer_agreement
                            if quality_score_record
                            else 0
                        ),
                        "completed_at": assignment.annotation.created_at.isoformat(),
                        # Individual annotations hidden by default - expert reviews consolidated result
                        "individual_result": (
                            assignment.annotation.result
                            if consensus.status == "review_required"
                            else None
                        ),
                    }
                )

        # Get agreement scores between annotators
        agreements = AnnotatorAgreement.objects.filter(
            task_consensus=consensus
        ).select_related("annotator_1", "annotator_2")

        agreement_data = [
            {
                "annotator_1": a.annotator_1.user.email,
                "annotator_2": a.annotator_2.user.email,
                "agreement_score": float(a.agreement_score),
                "iou_score": float(a.iou_score) if a.iou_score else None,
                "label_agreement": (
                    float(a.label_agreement) if a.label_agreement else None
                ),
            }
            for a in agreements
        ]

        return {
            "review_task_id": review_task.id,
            "task_id": task.id,
            "status": review_task.status,
            "assignment_reason": review_task.assignment_reason,
            "disagreement_score": float(review_task.disagreement_score or 0),
            "task_data": task.data,
            "project_title": task.project.title,
            "project_id": task.project.id,
            # PRIMARY: Consolidated annotation for expert to review
            "consolidated_annotation": {
                "result": consensus.consolidated_result,
                "method": consensus.consolidation_method,
                "confidence": float(consensus.average_agreement or 0),
            },
            # Consensus metadata
            "consensus": {
                "status": consensus.status,
                "average_agreement": float(consensus.average_agreement or 0),
                "min_agreement": float(consensus.min_agreement or 0),
                "max_agreement": float(consensus.max_agreement or 0),
                "annotations_count": len(annotator_metrics),
            },
            # Annotator performance metrics (not full annotations)
            "annotator_metrics": annotator_metrics,
            # Agreement scores for transparency
            "agreements": agreement_data,
            "assigned_at": review_task.assigned_at.isoformat(),
            "started_at": (
                review_task.started_at.isoformat() if review_task.started_at else None
            ),
        }

    @classmethod
    @transaction.atomic
    def start_review(cls, review_task) -> Dict:
        """Mark a review task as started"""
        if review_task.status != "pending":
            return {"success": False, "error": "Review already started or completed"}

        review_task.status = "in_review"
        review_task.started_at = timezone.now()
        review_task.save(update_fields=["status", "started_at"])

        return {"success": True, "started_at": review_task.started_at.isoformat()}

    @classmethod
    def get_project_review_stats(cls, project) -> Dict:
        """Get review statistics for a project"""
        from .models import ExpertReviewTask

        reviews = ExpertReviewTask.objects.filter(task__project=project)

        status_counts = reviews.values("status").annotate(count=Count("id"))
        status_dict = {s["status"]: s["count"] for s in status_counts}

        avg_review_time = reviews.filter(review_time_seconds__gt=0).aggregate(
            avg=Avg("review_time_seconds")
        )["avg"]

        return {
            "project_id": project.id,
            "total_reviews": reviews.count(),
            "status_breakdown": {
                "pending": status_dict.get("pending", 0),
                "in_review": status_dict.get("in_review", 0),
                "approved": status_dict.get("approved", 0),
                "rejected": status_dict.get("rejected", 0),
                "corrected": status_dict.get("corrected", 0),
                "escalated": status_dict.get("escalated", 0),
            },
            "average_review_time": int(avg_review_time) if avg_review_time else None,
            "approval_rate": (
                (status_dict.get("approved", 0) + status_dict.get("corrected", 0))
                / reviews.filter(
                    status__in=["approved", "rejected", "corrected"]
                ).count()
                * 100
                if reviews.filter(
                    status__in=["approved", "rejected", "corrected"]
                ).count()
                > 0
                else None
            ),
        }

    # ========================================================================
    # ACCEPT/REJECT WORKFLOW
    # ========================================================================

    @classmethod
    @transaction.atomic
    def accept_consolidated_annotation(
        cls,
        task,
        expert_user,
        review_notes: str = "",
        corrected_result: Optional[Dict] = None,
    ) -> Dict:
        """
        Accept a consolidated annotation and finalize it.

        Args:
            task: Task object
            expert_user: User performing the review (must have expert_profile)
            review_notes: Optional review notes
            corrected_result: Optional corrected annotation if expert made changes

        Returns:
            Dict with success status and details
        """
        from .models import TaskConsensus, ExpertReviewTask, TaskAssignment

        try:
            consensus = TaskConsensus.objects.get(task=task)
        except TaskConsensus.DoesNotExist:
            return {"success": False, "error": "No consensus found for this task"}

        # Verify user is an expert
        try:
            expert_profile = expert_user.expert_profile
        except AttributeError:
            return {"success": False, "error": "User is not an expert"}

        # Check if there's an active review task
        try:
            review_task = ExpertReviewTask.objects.get(
                task=task, expert=expert_profile, status__in=["pending", "in_review"]
            )
        except ExpertReviewTask.DoesNotExist:
            # Create a review task if it doesn't exist
            review_task = ExpertReviewTask.objects.create(
                expert=expert_profile,
                task=task,
                task_consensus=consensus,
                status="in_review",
                assignment_reason="manual_review",
            )

        # Update consensus status
        old_status = consensus.status
        consensus.status = "finalized"
        consensus.reviewed_by = expert_user
        consensus.review_notes = review_notes
        consensus.finalized_at = timezone.now()

        # If expert provided corrections, use them
        if corrected_result:
            consensus.consolidated_result = corrected_result
            review_task.corrected_result = corrected_result
            review_task.correction_summary = (
                "Expert made corrections to consolidated annotation"
            )
            review_task.status = "corrected"
        else:
            review_task.status = "approved"

        consensus.save()

        # Create a client-visible annotation from the consolidated result
        from tasks.models import Annotation

        # Mark any existing annotations as not ground truth
        Annotation.objects.filter(task=task).update(ground_truth=False)

        # Create the final annotation for the client from consolidated result
        final_annotation = Annotation.objects.create(
            task=task,
            completed_by=expert_user,
            result=(
                corrected_result if corrected_result else consensus.consolidated_result
            ),
            was_cancelled=False,
            ground_truth=True,  # Mark as ground truth so client sees this as the final annotation
            project=task.project,
        )

        logger.info(
            f"📝 Created client annotation {final_annotation.id} from consolidated result for task {task.id}"
        )

        # Update review task
        review_task.completed_at = timezone.now()
        if review_task.started_at:
            review_task.review_time_seconds = int(
                (review_task.completed_at - review_task.started_at).total_seconds()
            )
        review_task.review_notes = review_notes
        review_task.save()

        # Process payment for review
        payment_result = cls._process_review_payment(review_task, review_task.status)

        # Get the ground truth result for accuracy calculation
        ground_truth_result = (
            corrected_result if corrected_result else consensus.consolidated_result
        )

        # Calculate accuracy for all annotators against ground truth
        from .accuracy_service import (
            AccuracyService,
            ClientBillingService,
            PaymentFinalizationService,
        )

        accuracy_results = AccuracyService.calculate_accuracy_for_task(
            task=task,
            ground_truth_result=ground_truth_result,
            expert_user=expert_user,
        )

        logger.info(
            f"📊 Accuracy calculated for task {task.id}: "
            f"Average {accuracy_results.get('average_accuracy', 0):.1f}%"
        )

        # Finalize payments to annotators with accuracy bonuses
        payment_finalization = PaymentFinalizationService.finalize_payments_for_task(
            task=task,
            consensus=consensus,
            accuracy_results=accuracy_results,
            expert_user=expert_user,
        )

        logger.info(
            f"💰 Payments finalized for task {task.id}: "
            f"Total released ₹{payment_finalization.get('total_released', 0)}"
        )

        # Charge the client for the finalized annotation
        billing_result = ClientBillingService.charge_for_finalized_annotation(
            task=task,
            ground_truth_annotation=final_annotation,
            expert_user=expert_user,
        )

        if billing_result.get("success"):
            logger.info(
                f"💳 Client charged {billing_result.get('credits_charged', 0)} credits for task {task.id}"
            )

        # Send notifications to annotators (with accuracy info)
        cls._notify_annotators_accepted(task, consensus, expert_user, accuracy_results)

        logger.info(
            f"✅ Task {task.id} consolidated annotation ACCEPTED by expert {expert_user.email}"
            f" (status: {old_status} → finalized)"
        )

        return {
            "success": True,
            "task_id": task.id,
            "consensus_id": consensus.id,
            "status": "finalized",
            "review_task_id": review_task.id,
            "corrected": corrected_result is not None,
            "expert_payment": float(payment_result.get("total_payment", 0)),
            "accuracy": {
                "average": accuracy_results.get("average_accuracy", 0),
                "distribution": accuracy_results.get("accuracy_distribution", {}),
                "annotators": len(accuracy_results.get("annotator_scores", [])),
            },
            "annotator_payments": {
                "total_released": float(payment_finalization.get("total_released", 0)),
                "count": len(payment_finalization.get("annotator_payments", [])),
            },
            "client_billing": {
                "credits_charged": billing_result.get("credits_charged", 0),
                "success": billing_result.get("success", False),
            },
            "message": "Consolidated annotation accepted and finalized",
        }

    @classmethod
    @transaction.atomic
    def reject_consolidated_annotation(
        cls,
        task,
        expert_user,
        rejection_reason: str,
        review_notes: str = "",
        notify_annotators: bool = True,
        require_reannotation: bool = True,
    ) -> Dict:
        """
        Reject a consolidated annotation and request re-annotation.

        Args:
            task: Task object
            expert_user: User performing the review
            rejection_reason: Reason code for rejection
            review_notes: Detailed notes for annotators
            notify_annotators: Whether to notify annotators
            require_reannotation: Whether to reset task for re-annotation

        Returns:
            Dict with success status and details
        """
        from .models import TaskConsensus, ExpertReviewTask, TaskAssignment
        from tasks.models import Annotation

        try:
            consensus = TaskConsensus.objects.get(task=task)
        except TaskConsensus.DoesNotExist:
            return {"success": False, "error": "No consensus found for this task"}

        # Verify user is an expert
        try:
            expert_profile = expert_user.expert_profile
        except AttributeError:
            return {"success": False, "error": "User is not an expert"}

        # Get or create review task
        try:
            review_task = ExpertReviewTask.objects.get(
                task=task, expert=expert_profile, status__in=["pending", "in_review"]
            )
        except ExpertReviewTask.DoesNotExist:
            review_task = ExpertReviewTask.objects.create(
                expert=expert_profile,
                task=task,
                task_consensus=consensus,
                status="in_review",
                assignment_reason="manual_review",
            )

        # Update consensus status
        old_status = consensus.status
        consensus.status = "conflict"  # Mark as conflict to prevent client access
        consensus.reviewed_by = expert_user
        consensus.review_notes = review_notes
        consensus.save()

        # Update review task
        review_task.status = "rejected"
        review_task.rejection_reason = rejection_reason
        review_task.review_notes = review_notes
        review_task.completed_at = timezone.now()
        if review_task.started_at:
            review_task.review_time_seconds = int(
                (review_task.completed_at - review_task.started_at).total_seconds()
            )
        review_task.save()

        # Process payment for review
        payment_result = cls._process_review_payment(review_task, "rejected")

        # Get all assignments for this task
        assignments = TaskAssignment.objects.filter(
            task=task, status="completed"
        ).select_related("annotator", "annotator__user")

        annotator_emails = []

        if require_reannotation:
            # Reset assignments to request re-annotation
            for assignment in assignments:
                # Mark old annotation as cancelled/rejected
                if assignment.annotation:
                    old_annotation = assignment.annotation
                    # Mark the old annotation as cancelled so it won't show in task
                    old_annotation.was_cancelled = True
                    old_annotation.save(update_fields=["was_cancelled"])

                    # Store rejection info in assignment for annotator reference
                    assignment.flagged_for_review = True
                    assignment.flag_reason = (
                        f"Expert rejected: {rejection_reason}. {review_notes}"
                    )

                # Reset assignment so annotator can re-annotate
                assignment.status = "assigned"
                assignment.annotation = None
                assignment.completed_at = None
                assignment.time_spent_seconds = 0
                assignment.save()

                annotator_emails.append(assignment.annotator.user.email)

            # Reset consensus
            consensus.current_annotations = 0
            consensus.consolidated_result = None
            consensus.status = "pending"
            consensus.save()

            logger.info(
                f"❌ Task {task.id} REJECTED by expert - {len(assignments)} assignments reset for re-annotation"
            )
        else:
            # Just notify without resetting
            annotator_emails = [a.annotator.user.email for a in assignments]
            logger.info(
                f"❌ Task {task.id} REJECTED by expert - annotators notified but no re-annotation required"
            )

        # Send notifications
        if notify_annotators:
            cls._notify_annotators_rejected(
                task,
                consensus,
                expert_user,
                rejection_reason,
                review_notes,
                annotator_emails,
                require_reannotation,
            )

        return {
            "success": True,
            "task_id": task.id,
            "consensus_id": consensus.id,
            "status": consensus.status,
            "review_task_id": review_task.id,
            "rejection_reason": rejection_reason,
            "annotators_notified": len(annotator_emails),
            "require_reannotation": require_reannotation,
            "expert_payment": float(payment_result.get("total_payment", 0)),
            "message": f"Consolidated annotation rejected. {len(annotator_emails)} annotators notified.",
        }

    @classmethod
    def _release_annotator_payments(cls, task, consensus):
        """Release payments to annotators when annotation is accepted"""
        from .models import TaskAssignment
        from .payment_service import PaymentService

        assignments = TaskAssignment.objects.filter(
            task=task, status="completed"
        ).select_related("annotator")

        for assignment in assignments:
            # Skip if consensus payment already released
            if assignment.consensus_released:
                continue

            try:
                # Mark consensus payment as released
                assignment.consensus_released = True
                assignment.save(update_fields=["consensus_released"])

                # Update annotator balance
                annotator = assignment.annotator
                annotator.available_balance += assignment.consensus_payment
                annotator.save(update_fields=["available_balance"])

                logger.info(
                    f"💰 Released consensus payment for annotator {assignment.annotator.user.email} "
                    f"on task {task.id}: {assignment.consensus_payment}"
                )
            except Exception as e:
                logger.error(
                    f"❌ Failed to release payment for assignment {assignment.id}: {e}"
                )

    @classmethod
    def _notify_annotators_accepted(
        cls, task, consensus, expert_user, accuracy_results=None
    ):
        """Send acceptance notifications to annotators with accuracy feedback"""
        from .models import TaskAssignment, AnnotatorNotification

        assignments = TaskAssignment.objects.filter(
            task=task, status="completed"
        ).select_related("annotator", "annotator__user")

        for assignment in assignments:
            try:
                # Get accuracy info for this annotator
                accuracy_info = None
                if accuracy_results:
                    accuracy_info = next(
                        (
                            a
                            for a in accuracy_results.get("annotator_scores", [])
                            if a["annotator_id"] == assignment.annotator.id
                        ),
                        None,
                    )

                # Build message with accuracy feedback
                accuracy_message = ""
                if accuracy_info:
                    score = accuracy_info.get("accuracy_score", 0)
                    level = accuracy_info.get("accuracy_level", "unknown")
                    bonus = accuracy_info.get("bonus_multiplier", 1.0)

                    level_emoji = {
                        "excellent": "🌟",
                        "good": "👍",
                        "acceptable": "✓",
                        "poor": "⚠️",
                        "very_poor": "⚠️",
                    }.get(level, "")

                    accuracy_message = (
                        f"\n\n📊 Your Accuracy: {score:.1f}% ({level} {level_emoji})"
                    )
                    if bonus > 1.0:
                        accuracy_message += (
                            f"\n🎁 Bonus applied: {int((bonus - 1) * 100)}% extra!"
                        )
                    elif bonus < 1.0:
                        accuracy_message += (
                            f"\n💡 Tip: Improve accuracy to earn bonus payments."
                        )

                # Create notification
                AnnotatorNotification.objects.create(
                    annotator=assignment.annotator,
                    notification_type="review_accepted",
                    title="✅ Your Annotation Accepted!",
                    message=(
                        f"Great work! Your annotation for task #{task.id} in project "
                        f"'{task.project.title}' has been reviewed and accepted by an expert. "
                        f"Payment has been released to your account.{accuracy_message}"
                    ),
                    task=task,
                    is_read=False,
                    metadata={
                        "accuracy_score": (
                            accuracy_info.get("accuracy_score")
                            if accuracy_info
                            else None
                        ),
                        "accuracy_level": (
                            accuracy_info.get("accuracy_level")
                            if accuracy_info
                            else None
                        ),
                        "bonus_multiplier": (
                            accuracy_info.get("bonus_multiplier")
                            if accuracy_info
                            else None
                        ),
                    },
                )

                logger.info(
                    f"📧 Notified annotator {assignment.annotator.user.email} of acceptance "
                    f"(accuracy: {accuracy_info.get('accuracy_score', 'N/A') if accuracy_info else 'N/A'}%)"
                )
            except Exception as e:
                logger.error(
                    f"❌ Failed to notify annotator {assignment.annotator.user.email}: {e}"
                )

    @classmethod
    def _notify_annotators_rejected(
        cls,
        task,
        consensus,
        expert_user,
        rejection_reason,
        review_notes,
        annotator_emails,
        require_reannotation,
    ):
        """Send rejection notifications to annotators"""
        from .models import TaskAssignment, AnnotatorNotification

        assignments = TaskAssignment.objects.filter(
            task=task, annotator__user__email__in=annotator_emails
        ).select_related("annotator", "annotator__user")

        # Create human-readable rejection reason
        rejection_reasons_map = {
            "low_quality": "Low quality annotations",
            "disagreement": "High disagreement between annotators",
            "incorrect_labels": "Incorrect labels used",
            "incomplete": "Incomplete annotation",
            "ambiguous": "Ambiguous data",
            "other": "Other issues",
        }

        reason_text = rejection_reasons_map.get(rejection_reason, rejection_reason)

        for assignment in assignments:
            try:
                # Determine message based on re-annotation requirement
                if require_reannotation:
                    message = (
                        f"⚠️ Your annotation for task #{task.id} in project "
                        f"'{task.project.title}' has been reviewed and requires improvement.\n\n"
                        f"Reason: {reason_text}\n\n"
                        f"Expert Notes: {review_notes or 'No additional notes provided.'}\n\n"
                        f"Please re-annotate this task carefully. This is a learning opportunity "
                        f"to improve your annotation quality."
                    )
                    notification_type = "review_rejected_reannotate"
                    title = "⚠️ Re-annotation Required"
                else:
                    message = (
                        f"ℹ️ Your annotation for task #{task.id} in project "
                        f"'{task.project.title}' has been reviewed.\n\n"
                        f"Reason: {reason_text}\n\n"
                        f"Expert Notes: {review_notes or 'No additional notes provided.'}\n\n"
                        f"Please review this feedback to improve future annotations."
                    )
                    notification_type = "review_feedback"
                    title = "ℹ️ Annotation Feedback"

                # Create notification
                AnnotatorNotification.objects.create(
                    annotator=assignment.annotator,
                    notification_type=notification_type,
                    title=title,
                    message=message,
                    task=task,
                    is_read=False,
                )

                logger.info(
                    f"📧 Notified annotator {assignment.annotator.user.email} of rejection"
                )
            except Exception as e:
                logger.error(
                    f"❌ Failed to notify annotator {assignment.annotator.user.email}: {e}"
                )

    @classmethod
    def get_review_task_details(cls, task, expert_user) -> Dict:
        """
        Get detailed information for expert to review a task

        Returns:
            Dict with task data, annotations, consensus, and agreement metrics
        """
        from .models import TaskConsensus, TaskAssignment, ExpertReviewTask

        try:
            consensus = TaskConsensus.objects.get(task=task)
        except TaskConsensus.DoesNotExist:
            return {"success": False, "error": "No consensus found for this task"}

        # Get all assignments and annotations
        assignments = TaskAssignment.objects.filter(
            task=task, annotation__isnull=False
        ).select_related("annotator", "annotator__user", "annotation")

        # Get existing review task if any
        review_task = None
        try:
            expert_profile = expert_user.expert_profile
            review_task = ExpertReviewTask.objects.filter(
                task=task, expert=expert_profile
            ).first()
        except AttributeError:
            pass

        # Build annotations list
        annotations_data = []
        for assignment in assignments:
            annotations_data.append(
                {
                    "id": assignment.annotation.id,
                    "annotator_email": assignment.annotator.user.email,
                    "annotator_id": assignment.annotator.id,
                    "completed_at": (
                        assignment.completed_at.isoformat()
                        if assignment.completed_at
                        else None
                    ),
                    "time_spent": assignment.time_spent_seconds,
                    "result": assignment.annotation.result,
                    "flagged": assignment.flagged_for_review,
                    "flag_reason": assignment.flag_reason,
                }
            )

        return {
            "success": True,
            "task_id": task.id,
            "task_data": task.data,
            "project_id": task.project_id,
            "project_title": task.project.title,
            "consensus": {
                "id": consensus.id,
                "status": consensus.status,
                "consolidated_result": consensus.consolidated_result,
                "average_agreement": float(consensus.average_agreement or 0),
                "min_agreement": float(consensus.min_agreement or 0),
                "max_agreement": float(consensus.max_agreement or 0),
                "consolidation_method": consensus.consolidation_method,
                "required_annotations": consensus.required_annotations,
                "current_annotations": consensus.current_annotations,
            },
            "annotations": annotations_data,
            "review_task": (
                {
                    "id": review_task.id if review_task else None,
                    "status": review_task.status if review_task else None,
                    "assigned_at": (
                        review_task.assigned_at.isoformat() if review_task else None
                    ),
                    "assignment_reason": (
                        review_task.assignment_reason if review_task else None
                    ),
                }
                if review_task
                else None
            ),
            "can_accept": consensus.status
            in ["review_required", "consensus_reached", "conflict"],
            "can_reject": consensus.status
            in ["review_required", "consensus_reached", "finalized"],
        }





