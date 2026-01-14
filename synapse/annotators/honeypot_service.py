"""
Honeypot Service for Quality Control

Handles honeypot task injection and evaluation for annotators.
Honeypots are tasks with known ground truth that are silently injected
into the annotation queue to monitor annotator accuracy.
"""

import logging
import random
from decimal import Decimal
from typing import Optional, Dict, Any, Tuple
from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone

logger = logging.getLogger(__name__)


class HoneypotService:
    """Service for honeypot injection and evaluation"""

    # Default injection rate (10%)
    DEFAULT_INJECTION_RATE = Decimal("0.10")

    # Minimum tasks between honeypots for same annotator
    DEFAULT_MIN_INTERVAL = 5

    @staticmethod
    def should_inject_honeypot(
        annotator_profile: "AnnotatorProfile",
        project: "Project",
    ) -> bool:
        """
        Determine if the next task should be a honeypot.

        Decision factors:
        1. Project has honeypot enabled
        2. Injection rate probability
        3. Minimum interval since last honeypot
        4. Annotator hasn't seen all honeypots

        Args:
            annotator_profile: The annotator's profile
            project: The current project

        Returns:
            True if a honeypot should be injected
        """
        from annotators.models import TaskAssignment, HoneypotTask

        # Check if project has honeypots enabled
        honeypot_enabled = getattr(project, "honeypot_enabled", True)
        if not honeypot_enabled:
            return False

        # Check if project has any active honeypots
        honeypot_count = HoneypotTask.objects.filter(
            task__project=project, is_active=True
        ).count()
        if honeypot_count == 0:
            return False

        # Get injection settings
        injection_rate = float(
            getattr(
                project,
                "honeypot_injection_rate",
                HoneypotService.DEFAULT_INJECTION_RATE,
            )
        )
        min_interval = getattr(
            project, "honeypot_min_interval", HoneypotService.DEFAULT_MIN_INTERVAL
        )

        # Check minimum interval since last honeypot
        recent_assignments = TaskAssignment.objects.filter(
            annotator=annotator_profile,
            task__project=project,
        ).order_by("-assigned_at")[:min_interval]

        if recent_assignments.filter(is_honeypot=True).exists():
            # Too soon since last honeypot
            logger.debug(
                f"Honeypot skipped for {annotator_profile.user.email}: "
                f"within min_interval of {min_interval}"
            )
            return False

        # Check if annotator has unseen honeypots
        seen_honeypot_task_ids = TaskAssignment.objects.filter(
            annotator=annotator_profile,
            is_honeypot=True,
            task__project=project,
        ).values_list("task_id", flat=True)

        unseen_count = (
            HoneypotTask.objects.filter(task__project=project, is_active=True)
            .exclude(task_id__in=seen_honeypot_task_ids)
            .count()
        )

        if unseen_count == 0:
            logger.debug(
                f"Honeypot skipped for {annotator_profile.user.email}: "
                f"annotator has seen all honeypots"
            )
            return False

        # Random probability check
        should_inject = random.random() < injection_rate
        logger.debug(
            f"Honeypot injection check for {annotator_profile.user.email}: "
            f"rate={injection_rate}, inject={should_inject}"
        )

        return should_inject

    @staticmethod
    def get_honeypot_task(
        annotator_profile: "AnnotatorProfile",
        project: "Project",
    ) -> Optional["Task"]:
        """
        Get a random honeypot task the annotator hasn't seen.

        Args:
            annotator_profile: The annotator's profile
            project: The current project

        Returns:
            A Task object if honeypot available, None otherwise
        """
        from annotators.models import TaskAssignment, HoneypotTask

        # Get honeypots the annotator has already been assigned
        seen_honeypot_task_ids = TaskAssignment.objects.filter(
            annotator=annotator_profile,
            is_honeypot=True,
            task__project=project,
        ).values_list("task_id", flat=True)

        # Get active unseen honeypots
        unseen_honeypots = (
            HoneypotTask.objects.filter(
                task__project=project,
                is_active=True,
            )
            .exclude(task_id__in=seen_honeypot_task_ids)
            .select_related("task")
        )

        if not unseen_honeypots.exists():
            return None

        # Select a random honeypot
        honeypot = random.choice(list(unseen_honeypots))

        logger.info(
            f"Injecting honeypot task {honeypot.task.id} for {annotator_profile.user.email}"
        )

        return honeypot.task

    @staticmethod
    @transaction.atomic
    def process_honeypot_result(
        task_assignment: "TaskAssignment",
        annotation_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Evaluate a honeypot annotation and update annotator metrics.

        This is called after an annotator submits an annotation for a honeypot task.

        Args:
            task_assignment: The TaskAssignment being evaluated
            annotation_result: The annotation result submitted by annotator

        Returns:
            Dict with evaluation results:
            - passed: bool
            - score: float (0-1)
            - tolerance: float
            - message: str
        """
        from annotators.models import HoneypotTask, TrustLevel

        task = task_assignment.task
        annotator = task_assignment.annotator

        try:
            honeypot = task.honeypot_config
        except HoneypotTask.DoesNotExist:
            return {
                "passed": None,
                "message": "Not a honeypot task",
            }

        # Evaluate annotation against ground truth
        passed, score = honeypot.evaluate_annotation(annotation_result)

        # Update task assignment with honeypot results
        task_assignment.is_honeypot = True
        task_assignment.honeypot_passed = passed
        task_assignment.save(update_fields=["is_honeypot", "honeypot_passed"])

        # Update trust level metrics
        try:
            trust_level = annotator.trust_level
        except TrustLevel.DoesNotExist:
            trust_level = TrustLevel.objects.create(annotator=annotator)

        trust_level.total_honeypots += 1
        if passed:
            trust_level.passed_honeypots += 1

        # Recalculate honeypot pass rate
        trust_level.honeypot_pass_rate = Decimal(
            str((trust_level.passed_honeypots / trust_level.total_honeypots) * 100)
        )
        trust_level.save(
            update_fields=["total_honeypots", "passed_honeypots", "honeypot_pass_rate"]
        )

        # Check level upgrade/downgrade
        trust_level.check_level_upgrade()

        # Update annotator profile accuracy
        HoneypotService.update_annotator_accuracy(annotator)

        # Check for consecutive failures
        if not passed:
            HoneypotService._check_consecutive_failures(annotator, task.project)

        result = {
            "passed": passed,
            "score": score,
            "tolerance": float(honeypot.tolerance),
            "honeypot_pass_rate": float(trust_level.honeypot_pass_rate),
            "message": "Passed honeypot check" if passed else "Failed honeypot check",
        }

        logger.info(
            f"Honeypot result for {annotator.user.email} on task {task.id}: "
            f"passed={passed}, score={score:.2f}"
        )

        return result

    @staticmethod
    def update_annotator_accuracy(annotator_profile: "AnnotatorProfile"):
        """
        Recalculate and update annotator accuracy score based on recent honeypots.

        Uses the last 100 honeypot results to calculate accuracy.

        Args:
            annotator_profile: The annotator profile to update
        """
        from annotators.models import TaskAssignment

        # Get last 100 honeypot assignments
        honeypot_assignments = TaskAssignment.objects.filter(
            annotator=annotator_profile,
            is_honeypot=True,
            honeypot_passed__isnull=False,
        ).order_by("-completed_at")[:100]

        if not honeypot_assignments.exists():
            return

        passed_count = honeypot_assignments.filter(honeypot_passed=True).count()
        total_count = honeypot_assignments.count()

        accuracy = (passed_count / total_count) * 100
        annotator_profile.accuracy_score = Decimal(str(accuracy))
        annotator_profile.save(update_fields=["accuracy_score"])

        logger.debug(
            f"Updated accuracy for {annotator_profile.user.email}: "
            f"{passed_count}/{total_count} = {accuracy:.1f}%"
        )

    @staticmethod
    def _check_consecutive_failures(
        annotator_profile: "AnnotatorProfile",
        project: "Project",
    ):
        """
        Check for consecutive honeypot failures and take action if threshold exceeded.

        Args:
            annotator_profile: The annotator profile
            project: The project for context
        """
        from annotators.models import TaskAssignment, TrustLevel

        failure_threshold = getattr(project, "honeypot_failure_threshold", 3)

        # Get recent honeypot results
        recent_honeypots = TaskAssignment.objects.filter(
            annotator=annotator_profile,
            is_honeypot=True,
            honeypot_passed__isnull=False,
        ).order_by("-completed_at")[:failure_threshold]

        if recent_honeypots.count() < failure_threshold:
            return

        # Check if all recent honeypots are failures
        consecutive_failures = all(not hp.honeypot_passed for hp in recent_honeypots)

        if consecutive_failures:
            logger.warning(
                f"Annotator {annotator_profile.user.email} has {failure_threshold} "
                f"consecutive honeypot failures"
            )

            # Add fraud flag
            try:
                trust_level = annotator_profile.trust_level
                trust_level.add_fraud_flag(
                    f"Consecutive honeypot failures: {failure_threshold}"
                )
            except TrustLevel.DoesNotExist:
                pass

            # Flag for manual review
            annotator_profile.status = "under_review"
            annotator_profile.save(update_fields=["status"])

    @staticmethod
    def get_honeypot_stats(project: "Project") -> Dict[str, Any]:
        """
        Get honeypot statistics for a project.

        Args:
            project: The project

        Returns:
            Dict with statistics
        """
        from annotators.models import HoneypotTask, TaskAssignment

        honeypots = HoneypotTask.objects.filter(task__project=project)
        assignments = TaskAssignment.objects.filter(
            task__project=project,
            is_honeypot=True,
        )

        total_honeypots = honeypots.count()
        active_honeypots = honeypots.filter(is_active=True).count()
        total_attempts = assignments.count()
        passed_attempts = assignments.filter(honeypot_passed=True).count()
        failed_attempts = assignments.filter(honeypot_passed=False).count()

        return {
            "total_honeypots": total_honeypots,
            "active_honeypots": active_honeypots,
            "total_attempts": total_attempts,
            "passed_attempts": passed_attempts,
            "failed_attempts": failed_attempts,
            "pass_rate": (
                (passed_attempts / total_attempts * 100) if total_attempts > 0 else 0
            ),
        }

    @staticmethod
    @transaction.atomic
    def create_honeypot(
        task: "Task",
        ground_truth: Dict[str, Any],
        tolerance: float = 0.8,
        created_by: "User" = None,
    ) -> "HoneypotTask":
        """
        Create a new honeypot from an existing task.

        Args:
            task: The task to make a honeypot
            ground_truth: The expected annotation result
            tolerance: Minimum agreement score to pass (0-1)
            created_by: User creating the honeypot

        Returns:
            The created HoneypotTask
        """
        from annotators.models import HoneypotTask

        honeypot, created = HoneypotTask.objects.update_or_create(
            task=task,
            defaults={
                "ground_truth": ground_truth,
                "tolerance": Decimal(str(tolerance)),
                "created_by": created_by,
                "is_active": True,
            },
        )

        if created:
            logger.info(f"Created honeypot for task {task.id}")
        else:
            logger.info(f"Updated honeypot for task {task.id}")

        return honeypot
