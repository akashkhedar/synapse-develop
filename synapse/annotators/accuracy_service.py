"""
Accuracy Service for calculating annotator accuracy against ground truth.

This service handles:
- Comparing individual annotations to the finalized ground truth
- Calculating accuracy scores for each annotator
- Updating annotator performance metrics (TrustLevel)
- Calculating quality-based payment bonuses
"""

from decimal import Decimal
from django.db import transaction
from django.utils import timezone
import logging
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger(__name__)


class AccuracyService:
    """
    Service for calculating accuracy by comparing annotations to ground truth.
    """

    # Accuracy thresholds for performance classification
    EXCELLENT_THRESHOLD = 95  # 95%+ = excellent
    GOOD_THRESHOLD = 85  # 85-95% = good
    ACCEPTABLE_THRESHOLD = 70  # 70-85% = acceptable
    POOR_THRESHOLD = 50  # 50-70% = poor, <50% = very poor

    # Bonus multipliers based on accuracy
    ACCURACY_BONUS_MULTIPLIERS = {
        "excellent": Decimal("1.20"),  # 20% bonus
        "good": Decimal("1.10"),  # 10% bonus
        "acceptable": Decimal("1.00"),  # No bonus
        "poor": Decimal("0.90"),  # 10% penalty
        "very_poor": Decimal("0.70"),  # 30% penalty
    }

    @classmethod
    def calculate_accuracy_for_task(
        cls,
        task,
        ground_truth_result: List[Dict],
        expert_user=None,
    ) -> Dict[str, Any]:
        """
        Calculate accuracy for all annotations on a task against the ground truth.

        Args:
            task: Task object
            ground_truth_result: The finalized ground truth annotation result
            expert_user: The expert who approved (for logging)

        Returns:
            Dict with accuracy results for each annotator
        """
        from .models import TaskAssignment, TrustLevel
        from .consensus_service import ConsensusService

        results = {
            "task_id": task.id,
            "ground_truth_established": True,
            "annotator_scores": [],
            "average_accuracy": 0.0,
            "accuracy_distribution": {
                "excellent": 0,
                "good": 0,
                "acceptable": 0,
                "poor": 0,
                "very_poor": 0,
            },
        }

        # Get all completed assignments for this task
        assignments = TaskAssignment.objects.filter(
            task=task,
            status="completed",
            annotation__isnull=False,
        ).select_related("annotator", "annotator__user", "annotation")

        if not assignments.exists():
            logger.warning(f"No completed assignments found for task {task.id}")
            return results

        # Detect annotation type from ground truth
        annotation_type = ConsensusService.detect_annotation_type(ground_truth_result)
        strategy = ConsensusService.get_strategy(annotation_type)

        total_accuracy = 0.0
        annotator_count = 0

        for assignment in assignments:
            if not assignment.annotation or not assignment.annotation.result:
                continue

            annotator_result = assignment.annotation.result

            # Calculate accuracy against ground truth
            accuracy_details = strategy.calculate_agreement(
                annotator_result, ground_truth_result
            )
            accuracy_score = accuracy_details.get("overall", 0)

            # Classify accuracy level
            accuracy_level = cls._classify_accuracy(accuracy_score)

            # Calculate bonus multiplier
            bonus_multiplier = cls.ACCURACY_BONUS_MULTIPLIERS.get(
                accuracy_level, Decimal("1.0")
            )

            # Update assignment with accuracy
            assignment.ground_truth_accuracy = Decimal(str(accuracy_score))
            assignment.accuracy_level = accuracy_level
            assignment.accuracy_bonus_multiplier = bonus_multiplier
            assignment.save(
                update_fields=[
                    "ground_truth_accuracy",
                    "accuracy_level",
                    "accuracy_bonus_multiplier",
                ]
            )

            # Update annotator's TrustLevel
            cls._update_annotator_performance(
                assignment.annotator,
                accuracy_score,
                accuracy_details,
                task,
            )

            # Track distribution
            results["accuracy_distribution"][accuracy_level] += 1

            # Add to results
            results["annotator_scores"].append(
                {
                    "annotator_id": assignment.annotator.id,
                    "annotator_email": assignment.annotator.user.email,
                    "annotation_id": assignment.annotation.id,
                    "accuracy_score": float(accuracy_score),
                    "accuracy_level": accuracy_level,
                    "bonus_multiplier": float(bonus_multiplier),
                    "details": accuracy_details,
                }
            )

            total_accuracy += accuracy_score
            annotator_count += 1

            logger.info(
                f"📊 Annotator {assignment.annotator.user.email} accuracy on task {task.id}: "
                f"{accuracy_score:.1f}% ({accuracy_level})"
            )

        # Calculate average accuracy
        if annotator_count > 0:
            results["average_accuracy"] = total_accuracy / annotator_count

        logger.info(
            f"✅ Accuracy calculated for task {task.id}: "
            f"Average {results['average_accuracy']:.1f}% across {annotator_count} annotators"
        )

        return results

    @classmethod
    def _classify_accuracy(cls, accuracy_score: float) -> str:
        """Classify accuracy score into a level."""
        if accuracy_score >= cls.EXCELLENT_THRESHOLD:
            return "excellent"
        elif accuracy_score >= cls.GOOD_THRESHOLD:
            return "good"
        elif accuracy_score >= cls.ACCEPTABLE_THRESHOLD:
            return "acceptable"
        elif accuracy_score >= cls.POOR_THRESHOLD:
            return "poor"
        else:
            return "very_poor"

    @classmethod
    @transaction.atomic
    def _update_annotator_performance(
        cls,
        annotator,
        accuracy_score: float,
        accuracy_details: Dict,
        task,
    ):
        """
        Update annotator's performance metrics in TrustLevel.

        Args:
            annotator: AnnotatorProfile object
            accuracy_score: The accuracy score (0-100)
            accuracy_details: Detailed accuracy breakdown
            task: The task that was scored
        """
        from .models import TrustLevel, AnnotatorPerformanceHistory

        try:
            trust_level = annotator.trust_level
        except TrustLevel.DoesNotExist:
            trust_level = TrustLevel.objects.create(annotator=annotator)

        # Store old values for history
        old_accuracy = float(trust_level.accuracy_score)
        old_level = trust_level.level

        # Update accuracy using weighted moving average
        # More recent accuracy scores have higher weight
        alpha = 0.3  # Weight for new score (0.3 = 30% new, 70% old)

        if trust_level.ground_truth_evaluations == 0:
            # First evaluation - use raw score
            trust_level.accuracy_score = Decimal(str(accuracy_score))
        else:
            # Exponential moving average
            new_accuracy = alpha * accuracy_score + (1 - alpha) * float(
                trust_level.accuracy_score
            )
            trust_level.accuracy_score = Decimal(str(new_accuracy))

        # Increment evaluation count
        trust_level.ground_truth_evaluations = (
            trust_level.ground_truth_evaluations or 0
        ) + 1
        trust_level.last_accuracy_update = timezone.now()

        # Track accuracy history (last 100 scores)
        accuracy_history = trust_level.accuracy_history or []
        accuracy_history.append(
            {
                "score": accuracy_score,
                "task_id": task.id,
                "timestamp": timezone.now().isoformat(),
            }
        )
        # Keep only last 100 entries
        trust_level.accuracy_history = accuracy_history[-100:]

        trust_level.save()

        # Check for level upgrade/downgrade
        trust_level.check_level_upgrade()

        # Record performance history
        try:
            AnnotatorPerformanceHistory.objects.create(
                annotator=annotator,
                task=task,
                metric_type="ground_truth_accuracy",
                old_value=Decimal(str(old_accuracy)),
                new_value=trust_level.accuracy_score,
                change_reason=f"Ground truth comparison for task {task.id}",
                details={
                    "accuracy_score": accuracy_score,
                    "accuracy_details": accuracy_details,
                    "old_level": old_level,
                    "new_level": trust_level.level,
                },
            )
        except Exception as e:
            logger.warning(f"Could not create performance history: {e}")

        logger.info(
            f"📈 Updated performance for {annotator.user.email}: "
            f"Accuracy {old_accuracy:.1f}% → {float(trust_level.accuracy_score):.1f}%"
        )

    @classmethod
    def get_annotator_accuracy_summary(cls, annotator) -> Dict:
        """
        Get a summary of an annotator's accuracy performance.

        Args:
            annotator: AnnotatorProfile object

        Returns:
            Dict with accuracy statistics
        """
        from .models import TrustLevel, TaskAssignment

        try:
            trust_level = annotator.trust_level
        except TrustLevel.DoesNotExist:
            return {
                "accuracy_score": 0,
                "ground_truth_evaluations": 0,
                "accuracy_trend": "unknown",
                "level": "new",
            }

        # Get recent accuracy from assignments
        recent_assignments = TaskAssignment.objects.filter(
            annotator=annotator,
            ground_truth_accuracy__isnull=False,
        ).order_by("-completed_at")[:20]

        recent_scores = [float(a.ground_truth_accuracy) for a in recent_assignments]

        # Calculate trend
        trend = "stable"
        if len(recent_scores) >= 5:
            first_half = sum(recent_scores[len(recent_scores) // 2 :]) / (
                len(recent_scores) // 2
            )
            second_half = sum(recent_scores[: len(recent_scores) // 2]) / (
                len(recent_scores) // 2
            )

            if second_half > first_half + 5:
                trend = "improving"
            elif second_half < first_half - 5:
                trend = "declining"

        return {
            "accuracy_score": float(trust_level.accuracy_score),
            "ground_truth_evaluations": trust_level.ground_truth_evaluations or 0,
            "accuracy_trend": trend,
            "level": trust_level.level,
            "recent_scores": recent_scores[:10],
            "accuracy_history": (
                trust_level.accuracy_history[-20:]
                if trust_level.accuracy_history
                else []
            ),
        }


class ClientBillingService:
    """
    Service for billing clients when annotations are finalized.
    """

    @classmethod
    @transaction.atomic
    def charge_for_finalized_annotation(
        cls,
        task,
        ground_truth_annotation,
        expert_user=None,
    ) -> Dict[str, Any]:
        """
        Charge the client (organization) for a finalized annotation.

        Args:
            task: Task object
            ground_truth_annotation: The finalized Annotation object
            expert_user: The expert who approved

        Returns:
            Dict with billing details
        """
        from billing.models import (
            OrganizationBilling,
            CreditTransaction,
            AnnotationPricing,
        )
        from billing.services import CreditService, InsufficientCreditsError

        project = task.project
        organization = project.organization

        result = {
            "success": False,
            "task_id": task.id,
            "project_id": project.id,
            "organization_id": organization.id,
            "credits_charged": 0,
            "message": "",
        }

        try:
            # Get or create billing record
            billing, _ = OrganizationBilling.objects.select_for_update().get_or_create(
                organization=organization
            )

            # Calculate credit cost based on annotation type
            annotation_result = ground_truth_annotation.result or []
            credit_cost = cls._calculate_annotation_cost(project, annotation_result)

            if credit_cost <= 0:
                result["success"] = True
                result["message"] = "No credits to charge (free tier or zero cost)"
                return result

            # Check if sufficient credits
            if not billing.has_sufficient_credits(credit_cost):
                # Log warning but don't fail - annotation is already done
                logger.warning(
                    f"⚠️ Organization {organization.title} has insufficient credits "
                    f"for task {task.id}. Required: {credit_cost}, Available: {billing.available_credits}"
                )
                result["message"] = "Insufficient credits - billing deferred"
                result["credits_required"] = float(credit_cost)
                result["credits_available"] = float(billing.available_credits)
                return result

            # Deduct credits
            description = (
                f"Annotation completed for Task #{task.id} in Project '{project.title}' "
                f"(Expert approved)"
            )
            billing.deduct_credits(credit_cost, description)

            # Update transaction metadata
            transaction = (
                CreditTransaction.objects.filter(
                    organization=organization,
                    transaction_type="debit",
                )
                .order_by("-created_at")
                .first()
            )

            if transaction:
                transaction.category = "annotation"
                transaction.metadata = {
                    "task_id": task.id,
                    "project_id": project.id,
                    "annotation_id": ground_truth_annotation.id,
                    "expert_approved": True,
                    "expert_user": expert_user.email if expert_user else None,
                }
                transaction.save()

            result["success"] = True
            result["credits_charged"] = float(credit_cost)
            result["credits_remaining"] = float(billing.available_credits)
            result["message"] = (
                f"Charged {credit_cost} credits for finalized annotation"
            )

            logger.info(
                f"💳 Charged {credit_cost} credits to {organization.title} "
                f"for task {task.id} (Expert: {expert_user.email if expert_user else 'N/A'})"
            )

            return result

        except Exception as e:
            logger.error(f"❌ Error charging for annotation: {e}")
            result["error"] = str(e)
            return result

    @classmethod
    def _calculate_annotation_cost(
        cls, project, annotation_result: List[Dict]
    ) -> Decimal:
        """
        Calculate the credit cost for an annotation based on project settings
        and annotation complexity.

        Args:
            project: Project object
            annotation_result: The annotation result

        Returns:
            Decimal credit cost
        """
        from billing.models import AnnotationPricing, ProjectBilling

        # Check if project has custom billing
        try:
            project_billing = ProjectBilling.objects.get(project=project)
            if project_billing.credit_rate_override:
                return Decimal(str(project_billing.credit_rate_override))
        except ProjectBilling.DoesNotExist:
            pass

        # Default pricing based on annotation type
        base_cost = Decimal("1.0")  # Default 1 credit per annotation

        # Analyze annotation complexity
        if annotation_result:
            annotation_types = set()
            total_items = 0

            for item in annotation_result:
                if isinstance(item, dict):
                    item_type = item.get("type", "").lower()
                    annotation_types.add(item_type)
                    total_items += 1

            # Adjust cost based on complexity
            if (
                "rectanglelabels" in annotation_types
                or "polygonlabels" in annotation_types
            ):
                base_cost = Decimal("2.0")  # Object detection is more expensive
            elif "brushlabels" in annotation_types:
                base_cost = Decimal("3.0")  # Segmentation is most expensive
            elif "keypointlabels" in annotation_types:
                base_cost = Decimal("2.5")  # Keypoints are complex

            # Additional cost for multiple items
            if total_items > 5:
                base_cost += Decimal(str(total_items - 5)) * Decimal("0.2")

        return base_cost


class PaymentFinalizationService:
    """
    Service to finalize all payments after expert approval.
    Combines accuracy-based bonuses with payment release.
    """

    @classmethod
    @transaction.atomic
    def finalize_payments_for_task(
        cls,
        task,
        consensus,
        accuracy_results: Dict,
        expert_user=None,
    ) -> Dict[str, Any]:
        """
        Finalize all annotator payments after expert approval.

        This releases:
        - Remaining consensus payment (if not already released)
        - Review payment (20%)
        - Accuracy bonus/penalty adjustments

        Args:
            task: Task object
            consensus: TaskConsensus object
            accuracy_results: Results from AccuracyService
            expert_user: The expert who approved

        Returns:
            Dict with payment details for all annotators
        """
        from .models import TaskAssignment, EarningsTransaction, TrustLevel

        results = {
            "task_id": task.id,
            "total_released": Decimal("0"),
            "annotator_payments": [],
        }

        assignments = TaskAssignment.objects.filter(
            task=task,
            status="completed",
        ).select_related("annotator", "annotator__user")

        for assignment in assignments:
            annotator = assignment.annotator
            payment_details = {
                "annotator_id": annotator.id,
                "annotator_email": annotator.user.email,
                "payments": [],
                "total_payment": Decimal("0"),
            }

            # Get accuracy info for this annotator
            annotator_accuracy = next(
                (
                    a
                    for a in accuracy_results.get("annotator_scores", [])
                    if a["annotator_id"] == annotator.id
                ),
                None,
            )

            accuracy_bonus = Decimal("1.0")
            if annotator_accuracy:
                accuracy_bonus = Decimal(
                    str(annotator_accuracy.get("bonus_multiplier", 1.0))
                )

            # 1. Release consensus payment if not already done
            if not assignment.consensus_released and assignment.immediate_released:
                consensus_amount = (
                    assignment.consensus_payment
                    * assignment.quality_multiplier
                    * assignment.trust_multiplier
                    * accuracy_bonus
                )

                assignment.consensus_released = True
                assignment.amount_paid += consensus_amount
                assignment.save(update_fields=["consensus_released", "amount_paid"])

                # Move immediate from pending to available
                immediate_amount = (
                    assignment.immediate_payment
                    * assignment.quality_multiplier
                    * assignment.trust_multiplier
                )
                annotator.pending_approval -= immediate_amount
                annotator.available_balance += immediate_amount + consensus_amount
                annotator.total_earned += consensus_amount
                annotator.save(
                    update_fields=[
                        "pending_approval",
                        "available_balance",
                        "total_earned",
                    ]
                )

                # Record transaction
                EarningsTransaction.objects.create(
                    annotator=annotator,
                    transaction_type="earning",
                    earning_stage="consensus",
                    amount=consensus_amount,
                    balance_after=annotator.available_balance,
                    task_assignment=assignment,
                    description=(
                        f"Consensus payment for task {task.id} "
                        f"(Accuracy bonus: {accuracy_bonus}x)"
                    ),
                    metadata={
                        "task_id": task.id,
                        "accuracy_bonus": float(accuracy_bonus),
                        "quality_multiplier": float(assignment.quality_multiplier),
                        "trust_multiplier": float(assignment.trust_multiplier),
                    },
                )

                payment_details["payments"].append(
                    {
                        "type": "consensus",
                        "amount": float(consensus_amount),
                    }
                )
                payment_details["total_payment"] += consensus_amount
                results["total_released"] += consensus_amount

            # 2. Release review payment (20%)
            if not assignment.review_released and assignment.consensus_released:
                review_amount = (
                    assignment.review_payment
                    * assignment.quality_multiplier
                    * assignment.trust_multiplier
                    * accuracy_bonus
                )

                assignment.review_released = True
                assignment.amount_paid += review_amount
                assignment.save(update_fields=["review_released", "amount_paid"])

                annotator.available_balance += review_amount
                annotator.total_earned += review_amount
                annotator.save(update_fields=["available_balance", "total_earned"])

                # Record transaction
                EarningsTransaction.objects.create(
                    annotator=annotator,
                    transaction_type="earning",
                    earning_stage="review",
                    amount=review_amount,
                    balance_after=annotator.available_balance,
                    task_assignment=assignment,
                    description=(
                        f"Review payment for task {task.id} "
                        f"(Expert approved, Accuracy: {annotator_accuracy.get('accuracy_score', 0) if annotator_accuracy else 0:.1f}%)"
                    ),
                    metadata={
                        "task_id": task.id,
                        "expert_user": expert_user.email if expert_user else None,
                        "accuracy_score": (
                            annotator_accuracy.get("accuracy_score", 0)
                            if annotator_accuracy
                            else 0
                        ),
                        "accuracy_level": (
                            annotator_accuracy.get("accuracy_level", "unknown")
                            if annotator_accuracy
                            else "unknown"
                        ),
                    },
                )

                payment_details["payments"].append(
                    {
                        "type": "review",
                        "amount": float(review_amount),
                    }
                )
                payment_details["total_payment"] += review_amount
                results["total_released"] += review_amount

            # Update annotator task completion count
            annotator.total_tasks_completed = (annotator.total_tasks_completed or 0) + 1
            annotator.save(update_fields=["total_tasks_completed"])

            # Update TrustLevel task count
            try:
                trust_level = annotator.trust_level
                trust_level.tasks_completed = (trust_level.tasks_completed or 0) + 1
                trust_level.save(update_fields=["tasks_completed"])
            except Exception as e:
                logger.warning(f"Could not update trust level task count: {e}")

            results["annotator_payments"].append(payment_details)

            logger.info(
                f"💰 Finalized payment for {annotator.user.email} on task {task.id}: "
                f"₹{payment_details['total_payment']}"
            )

        logger.info(
            f"✅ Total released for task {task.id}: ₹{results['total_released']}"
        )

        return results





