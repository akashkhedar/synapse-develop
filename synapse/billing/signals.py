"""
Signal handlers for billing operations:
- Credit deduction on annotation creation
- Project billing initialization on project creation
- Activity tracking for project lifecycle
- Annotator payment processing on annotation completion
"""

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from tasks.models import Annotation
from projects.models import Project
from .services import CreditService, ProjectBillingService
from .models import ProjectBilling, AnnotatorEarnings
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


# Annotation type rates for payment calculation (same as project billing)
ANNOTATION_RATES = {
    "classification": Decimal("2"),
    "bounding_box": Decimal("5"),
    "polygon": Decimal("8"),
    "segmentation": Decimal("15"),
    "keypoint": Decimal("10"),
    "ner": Decimal("3"),
    "default": Decimal("3"),
}

# Annotator revenue share percentage (40-50%)
DEFAULT_ANNOTATOR_SHARE = Decimal("45")  # 45%


@receiver(post_save, sender=Project)
def handle_project_created(sender, instance, created, **kwargs):
    """
    Initialize billing for new projects.

    Note: Security deposit is NOT automatically collected here.
    It should be collected explicitly during project creation flow
    after the user confirms the deposit amount.

    This signal creates the ProjectBilling record if it doesn't exist.
    """
    if not created:
        # For existing projects, just track activity
        try:
            if hasattr(instance, "billing"):
                instance.billing.record_activity()
        except ProjectBilling.DoesNotExist:
            pass
        return

    # Skip if no organization
    if not instance.organization:
        return

    try:
        # Create ProjectBilling record (without collecting deposit)
        project_billing, created = ProjectBilling.objects.get_or_create(
            project=instance,
            defaults={
                "state": ProjectBilling.ProjectState.ACTIVE,
            },
        )

        if created:
            logger.info(
                f"Created billing record for project {instance.id}: {instance.title}"
            )

    except Exception as e:
        logger.error(f"Error creating billing record for project {instance.id}: {e}")


@receiver(pre_delete, sender=Project)
def handle_project_deleted(sender, instance, **kwargs):
    """
    Handle project deletion - refund or forfeit deposit based on state.

    Note: This signal may not always fire (e.g., when temporary_disconnect_all_signals
    is used). The ProjectAPI.delete() method now handles refunds directly before deletion
    to ensure they are processed. This signal serves as a fallback for other deletion paths.
    """
    try:
        if hasattr(instance, "billing"):
            project_billing = instance.billing

            # Check if project was completed or already refunded
            if project_billing.state == ProjectBilling.ProjectState.COMPLETED:
                # Already handled
                return

            if project_billing.security_deposit_refunded > 0:
                # Already refunded (likely by ProjectAPI.delete)
                return

            # Check if deposit was paid
            if project_billing.security_deposit_paid <= 0:
                return

            # Check if project has annotations (was used)
            if instance.tasks.filter(annotations__isnull=False).exists():
                # Project was used, refund remaining deposit
                result = ProjectBillingService.refund_security_deposit(
                    instance, reason="Project deleted by user"
                )
                logger.info(f"Refunded deposit on project deletion (signal): {result}")
            else:
                # Project was never used (no annotations), full refund
                result = ProjectBillingService.refund_security_deposit(
                    instance, reason="Project deleted without use - full refund"
                )
                logger.info(
                    f"Full refund on unused project deletion (signal): {result}"
                )

    except ProjectBilling.DoesNotExist:
        pass
    except Exception as e:
        logger.error(f"Error handling project deletion billing for {instance.id}: {e}")


@receiver(post_save, sender=Annotation)
def handle_annotation_created(sender, instance, created, **kwargs):
    """
    Track annotation costs, update project billing, and process annotator payment.

    This signal:
    1. Tracks annotation costs for project billing
    2. Updates TaskAssignment if annotator system is active
    3. Processes payment for the annotator
    4. Updates annotator earnings

    Note: Credit deduction from client happens on EXPORT, not on annotation creation.
    Annotator payment is processed immediately (40% immediate, 40% consensus, 20% review).
    """
    if not created:
        return

    task = instance.task
    project = task.project
    organization = project.organization
    annotator_user = instance.completed_by  # The user who created the annotation

    # Skip if organization doesn't have billing enabled
    if not hasattr(organization, "billing"):
        return

    try:
        # Track activity on project
        if hasattr(project, "billing"):
            project.billing.record_activity()

        # Get annotation details from the annotation result
        result = instance.result
        if not result:
            return

        # Determine annotation type from result
        annotation_type = _detect_annotation_type(result)

        # Get annotation rate
        rate = ANNOTATION_RATES.get(annotation_type, ANNOTATION_RATES["default"])

        # Update project billing with accumulated cost
        if hasattr(project, "billing"):
            project.billing.actual_annotation_cost += rate
            project.billing.save(update_fields=["actual_annotation_cost"])

        logger.debug(
            f"Tracked annotation cost for {instance.id}: ₹{rate} ({annotation_type})"
        )

        # === ANNOTATOR PAYMENT PROCESSING ===
        if annotator_user:
            _process_annotator_payment(
                annotation=instance,
                annotator_user=annotator_user,
                task=task,
                project=project,
                organization=organization,
                annotation_type=annotation_type,
                rate=rate,
            )

    except Exception as e:
        logger.error(f"Error tracking annotation cost for {instance.id}: {e}")
        # Don't raise exception to avoid blocking annotation creation


def _detect_annotation_type(result):
    """Detect annotation type from result data"""
    annotation_type = "classification"  # default

    if not result:
        return annotation_type

    result_str = str(result).lower()

    if "rectanglelabels" in result_str or "rect" in result_str:
        annotation_type = "bounding_box"
    elif "polygonlabels" in result_str or "polygon" in result_str:
        annotation_type = "polygon"
    elif "keypointlabels" in result_str or "keypoint" in result_str:
        annotation_type = "keypoint"
    elif "brushlabels" in result_str or "brush" in result_str:
        annotation_type = "segmentation"
    elif "labels" in result_str and "ner" in result_str:
        annotation_type = "ner"
    elif any("labels" in str(r).lower() for r in result if isinstance(r, dict)):
        annotation_type = "ner"

    return annotation_type


def _process_annotator_payment(
    annotation, annotator_user, task, project, organization, annotation_type, rate
):
    """
    Process payment for an annotator when they complete an annotation.

    Payment flow:
    1. Check if annotator has a profile (is a registered annotator)
    2. Find or create TaskAssignment
    3. Calculate payment with multipliers
    4. Process immediate payment (40%)
    5. Update annotator earnings record
    6. Create transaction history
    """
    try:
        # Import annotator models
        from annotators.models import (
            AnnotatorProfile,
            TaskAssignment,
            TrustLevel,
            EarningsTransaction,
        )
        from annotators.payment_service import PaymentService

        # Check if user has an annotator profile
        try:
            annotator_profile = annotator_user.annotator_profile
        except AnnotatorProfile.DoesNotExist:
            # Not a registered annotator, skip payment processing
            logger.debug(
                f"User {annotator_user.email} is not a registered annotator, skipping payment"
            )
            return

        # Check if annotator profile is approved
        if annotator_profile.status != "approved":
            logger.debug(
                f"Annotator {annotator_user.email} not approved, skipping payment"
            )
            return

        # Find or create TaskAssignment
        task_assignment, created = TaskAssignment.objects.get_or_create(
            annotator=annotator_profile,
            task=task,
            defaults={
                "status": "completed",
                "annotation": annotation,
                "started_at": annotation.created_at,
                "completed_at": annotation.created_at,
            },
        )

        if not created:
            # Update existing assignment
            task_assignment.status = "completed"
            task_assignment.annotation = annotation
            task_assignment.completed_at = annotation.created_at
            task_assignment.save(update_fields=["status", "annotation", "completed_at"])

        # Get or create trust level
        trust_level, _ = TrustLevel.objects.get_or_create(
            annotator=annotator_profile,
            defaults={"level": "new", "multiplier": Decimal("0.8")},
        )

        # Calculate complexity score
        complexity_score = PaymentService.calculate_complexity_score(task)

        # Calculate base payment
        base_payment = rate * complexity_score
        trust_multiplier = trust_level.multiplier

        # Calculate escrow splits (40% immediate, 40% consensus, 20% review)
        immediate_payment = base_payment * Decimal("0.4")
        consensus_payment = base_payment * Decimal("0.4")
        review_payment = base_payment * Decimal("0.2")

        # Update task assignment with payment details
        task_assignment.base_payment = base_payment
        task_assignment.trust_multiplier = trust_multiplier
        task_assignment.immediate_payment = immediate_payment
        task_assignment.consensus_payment = consensus_payment
        task_assignment.review_payment = review_payment
        task_assignment.quality_multiplier = Decimal("1.0")  # Default, updated later
        task_assignment.save(
            update_fields=[
                "base_payment",
                "trust_multiplier",
                "immediate_payment",
                "consensus_payment",
                "review_payment",
                "quality_multiplier",
            ]
        )

        # Release immediate payment (40%)
        if not task_assignment.immediate_released:
            final_immediate = immediate_payment * trust_multiplier
            task_assignment.immediate_released = True
            task_assignment.amount_paid = final_immediate
            task_assignment.save(update_fields=["immediate_released", "amount_paid"])

            # Update annotator profile earnings
            annotator_profile.pending_approval += final_immediate
            annotator_profile.total_tasks_completed += 1
            annotator_profile.save(
                update_fields=["pending_approval", "total_tasks_completed"]
            )

            # Create earnings transaction
            EarningsTransaction.objects.create(
                annotator=annotator_profile,
                transaction_type="earning",
                earning_stage="immediate",
                amount=final_immediate,
                balance_after=annotator_profile.pending_approval,
                task_assignment=task_assignment,
                description=f"Immediate payment (40%) for annotation on task {task.id}",
                metadata={
                    "task_id": task.id,
                    "project_id": project.id,
                    "annotation_type": annotation_type,
                    "base_rate": float(rate),
                    "complexity_score": float(complexity_score),
                    "trust_multiplier": float(trust_multiplier),
                },
            )

            # Also update billing AnnotatorEarnings for organization tracking
            annotator_earnings, _ = AnnotatorEarnings.objects.get_or_create(
                annotator=annotator_user,
                organization=organization,
                defaults={"revenue_share_percentage": DEFAULT_ANNOTATOR_SHARE},
            )
            annotator_earnings.credits_earned += final_immediate
            annotator_earnings.inr_equivalent += final_immediate  # 1 credit = ₹1
            annotator_earnings.total_annotations += 1
            annotator_earnings.save(
                update_fields=[
                    "credits_earned",
                    "inr_equivalent",
                    "total_annotations",
                    "updated_at",
                ]
            )

            logger.info(
                f"Processed annotator payment for {annotator_user.email}: "
                f"₹{final_immediate} immediate (task {task.id}, {annotation_type})"
            )

        # Update trust level metrics
        trust_level.update_metrics(task_assignment)

        # === CONSENSUS PROCESSING ===
        # Check if task has enough annotations for consensus
        _trigger_consensus_check(task, project)

    except ImportError:
        # Annotator module not available
        logger.debug("Annotator module not available, skipping payment processing")
    except Exception as e:
        logger.error(f"Error processing annotator payment: {e}", exc_info=True)
        # Don't raise - allow annotation to be saved even if payment fails


def _trigger_consensus_check(task, project):
    """
    Check if task has enough annotations and trigger consensus processing.
    This releases the consensus payment (40%) based on quality scores.
    """
    try:
        from annotators.consensus_service import ConsensusService

        # Get required overlap from project
        required_overlap = getattr(project, "required_overlap", 1)

        if required_overlap <= 1:
            # Single annotator mode - no consensus needed
            # Automatically release consensus payment with full quality
            _auto_release_single_annotator_consensus(task)
            return

        # Check and process consensus for multi-annotator tasks
        result = ConsensusService.check_and_process_consensus(task)

        if result:
            logger.info(
                f"Consensus processed for task {task.id}: "
                f"status={result.get('status')}, agreement={result.get('average_agreement', 0):.1f}%"
            )
        else:
            logger.debug(f"Task {task.id}: waiting for more annotations for consensus")

    except ImportError:
        logger.debug("Consensus service not available")
    except Exception as e:
        logger.error(
            f"Error triggering consensus check for task {task.id}: {e}", exc_info=True
        )


def _auto_release_single_annotator_consensus(task):
    """
    For single-annotator projects, automatically release consensus payment.
    Since there's no consensus to validate, we give full quality score.
    """
    try:
        from annotators.models import TaskAssignment, EarningsTransaction

        assignment = (
            TaskAssignment.objects.filter(
                task=task,
                status="completed",
                immediate_released=True,
                consensus_released=False,
            )
            .select_related("annotator")
            .first()
        )

        if not assignment:
            return

        annotator = assignment.annotator

        # Full quality for single annotator
        assignment.quality_score = Decimal("100")
        assignment.quality_multiplier = Decimal("1.0")
        assignment.consensus_agreement = Decimal("100")

        # Release consensus payment
        final_payment = assignment.consensus_payment * assignment.trust_multiplier
        assignment.consensus_released = True
        assignment.amount_paid += final_payment
        assignment.save(
            update_fields=[
                "quality_score",
                "quality_multiplier",
                "consensus_agreement",
                "consensus_released",
                "amount_paid",
            ]
        )

        # Move immediate from pending to available, add consensus
        immediate_amount = assignment.immediate_payment * assignment.trust_multiplier
        annotator.pending_approval -= immediate_amount
        annotator.available_balance += immediate_amount + final_payment
        annotator.total_earned += final_payment
        annotator.save(
            update_fields=["pending_approval", "available_balance", "total_earned"]
        )

        # Record transaction
        EarningsTransaction.objects.create(
            annotator=annotator,
            transaction_type="earning",
            earning_stage="consensus",
            amount=final_payment,
            balance_after=annotator.available_balance,
            task_assignment=assignment,
            description=f"Consensus payment (40%) for task {task.id} (single annotator)",
            metadata={
                "task_id": task.id,
                "quality_score": 100,
                "single_annotator_mode": True,
            },
        )

        logger.info(
            f"Auto-released consensus payment for single annotator {annotator.user.email}: ₹{final_payment}"
        )

    except Exception as e:
        logger.error(
            f"Error auto-releasing single annotator consensus: {e}", exc_info=True
        )





