"""
Payment Service for Annotators
Handles payment calculations, quality scoring, fraud detection, and payouts
"""

from decimal import Decimal
from django.db import transaction
from django.db.models import Avg, Count, Sum, F, Q
from django.utils import timezone
from datetime import timedelta
import logging
import json

logger = logging.getLogger(__name__)


class PaymentService:
    """Service for calculating and processing annotator payments"""

    # Base rates per annotation type (in INR)
    BASE_RATES = {
        "classification": Decimal("2.0"),
        "bounding_box": Decimal("5.0"),
        "polygon": Decimal("8.0"),
        "segmentation": Decimal("15.0"),
        "keypoint": Decimal("10.0"),
        "ner": Decimal("3.0"),
        "relation": Decimal("4.0"),
        "default": Decimal("3.0"),
    }

    # Complexity multipliers
    COMPLEXITY_MULTIPLIERS = {
        "very_low": Decimal("0.5"),
        "low": Decimal("0.75"),
        "medium": Decimal("1.0"),
        "high": Decimal("1.5"),
        "very_high": Decimal("2.0"),
    }

    # Time thresholds for fraud detection (seconds)
    MIN_TIME_THRESHOLDS = {
        "classification": 3,
        "bounding_box": 10,
        "polygon": 20,
        "segmentation": 30,
        "keypoint": 15,
        "ner": 8,
        "default": 5,
    }

    @staticmethod
    def calculate_task_payment(task_assignment, annotation_type="default"):
        """
        Calculate payment for a task assignment

        Payment Formula: Base Rate × Complexity × Quality × Trust

        Returns dict with payment breakdown
        """
        from .models import TrustLevel

        annotator = task_assignment.annotator
        task = task_assignment.task

        # Get base rate
        base_rate = PaymentService.BASE_RATES.get(
            annotation_type, PaymentService.BASE_RATES["default"]
        )

        # Get complexity score
        complexity_score = PaymentService.calculate_complexity_score(task)

        # Get trust multiplier
        try:
            trust_level = annotator.trust_level
            trust_multiplier = trust_level.multiplier
        except TrustLevel.DoesNotExist:
            trust_level = TrustLevel.objects.create(annotator=annotator)
            trust_multiplier = Decimal("0.8")

        # Calculate base payment
        base_payment = base_rate * complexity_score

        # Calculate escrow splits
        immediate_payment = base_payment * Decimal("0.4")
        consensus_payment = base_payment * Decimal("0.4")
        review_payment = base_payment * Decimal("0.2")

        # Update task assignment
        task_assignment.base_payment = base_payment
        task_assignment.trust_multiplier = trust_multiplier
        task_assignment.immediate_payment = immediate_payment
        task_assignment.consensus_payment = consensus_payment
        task_assignment.review_payment = review_payment
        task_assignment.save(
            update_fields=[
                "base_payment",
                "trust_multiplier",
                "immediate_payment",
                "consensus_payment",
                "review_payment",
            ]
        )

        return {
            "base_rate": float(base_rate),
            "complexity_score": float(complexity_score),
            "trust_multiplier": float(trust_multiplier),
            "base_payment": float(base_payment),
            "immediate_payment": float(immediate_payment),
            "consensus_payment": float(consensus_payment),
            "review_payment": float(review_payment),
            "max_total": float(base_payment * trust_multiplier),
        }

    @staticmethod
    def calculate_complexity_score(task):
        """
        Calculate task complexity based on various factors
        """
        complexity = Decimal("1.0")  # Base complexity

        try:
            data = task.data or {}

            # Check for multiple objects/items
            if isinstance(data, dict):
                # Count data fields
                field_count = len(data)
                if field_count > 5:
                    complexity += Decimal("0.3")

                # Check for nested structures
                for value in data.values():
                    if isinstance(value, (list, dict)):
                        complexity += Decimal("0.2")
                        break

            # Check task metadata for complexity hints
            meta = task.meta or {}
            if meta.get("complexity"):
                complexity_level = meta.get("complexity", "medium")
                return PaymentService.COMPLEXITY_MULTIPLIERS.get(
                    complexity_level, Decimal("1.0")
                )

            # Cap complexity
            complexity = min(complexity, Decimal("2.0"))

        except Exception as e:
            logger.warning(f"Error calculating complexity for task {task.id}: {e}")
            complexity = Decimal("1.0")

        return complexity

    @staticmethod
    def calculate_quality_score(task_assignment, annotation_result):
        """
        Calculate quality score for an annotation

        Factors:
        - Consensus agreement with other annotators
        - Time spent (not too fast, not too slow)
        - Completeness
        - Consistency with annotator's history

        Returns score 0-100
        """
        scores = []

        # 1. Time-based scoring
        time_score = PaymentService._calculate_time_score(task_assignment)
        scores.append(("time", time_score, 0.2))

        # 2. Completeness score
        completeness_score = PaymentService._calculate_completeness_score(
            annotation_result
        )
        scores.append(("completeness", completeness_score, 0.3))

        # 3. Consensus score (if available)
        consensus_score = PaymentService._calculate_consensus_score(task_assignment)
        if consensus_score is not None:
            scores.append(("consensus", consensus_score, 0.5))
        else:
            # Redistribute weight to other factors
            scores = [(name, score, weight * 2) for name, score, weight in scores[:2]]

        # Calculate weighted average
        total_weight = sum(weight for _, _, weight in scores)
        quality_score = (
            sum(score * weight for _, score, weight in scores) / total_weight
        )

        # Update task assignment
        task_assignment.quality_score = Decimal(str(quality_score))
        task_assignment.quality_multiplier = Decimal(str(quality_score / 100))
        task_assignment.save(update_fields=["quality_score", "quality_multiplier"])

        return {
            "quality_score": quality_score,
            "breakdown": {name: score for name, score, _ in scores},
        }

    @staticmethod
    def _calculate_time_score(task_assignment):
        """Calculate score based on time spent"""
        time_spent = task_assignment.time_spent_seconds

        if time_spent == 0:
            return 50  # No data

        # Get minimum threshold
        annotation_type = "default"  # Could detect from task
        min_time = PaymentService.MIN_TIME_THRESHOLDS.get(annotation_type, 5)

        # Too fast is suspicious
        if time_spent < min_time:
            return max(0, 30 - (min_time - time_spent) * 5)

        # Reasonable time range gets full score
        max_reasonable_time = min_time * 10
        if time_spent <= max_reasonable_time:
            return 100

        # Very slow decreases score slightly
        return max(70, 100 - (time_spent - max_reasonable_time) / 60)

    @staticmethod
    def _calculate_completeness_score(annotation_result):
        """Calculate score based on annotation completeness"""
        if not annotation_result:
            return 0

        try:
            results = (
                annotation_result
                if isinstance(annotation_result, list)
                else [annotation_result]
            )

            if not results:
                return 0

            # Check for required fields in each result
            complete_count = 0
            for result in results:
                if isinstance(result, dict):
                    # Check for essential annotation data
                    has_value = "value" in result or "result" in result
                    has_type = "type" in result or "from_name" in result
                    if has_value or has_type:
                        complete_count += 1

            return (complete_count / len(results)) * 100 if results else 0

        except Exception as e:
            logger.warning(f"Error calculating completeness: {e}")
            return 50

    @staticmethod
    def _calculate_consensus_score(task_assignment):
        """Calculate agreement with other annotators on the same task"""
        from .models import TaskAssignment

        # Get other completed assignments for the same task
        other_assignments = TaskAssignment.objects.filter(
            task=task_assignment.task, status="completed"
        ).exclude(id=task_assignment.id)

        if not other_assignments.exists():
            return None

        # For now, return average of stored consensus scores
        # In production, this would compare actual annotation results
        avg_consensus = other_assignments.aggregate(avg=Avg("consensus_agreement"))[
            "avg"
        ]

        if avg_consensus:
            return float(avg_consensus)

        return None

    @staticmethod
    def calculate_annotation_agreement(result1, result2):
        """
        Calculate agreement between two annotation results
        Returns a score from 0 to 1
        """
        if not result1 or not result2:
            return 0.0

        try:
            # Handle different result formats
            r1 = result1 if isinstance(result1, list) else [result1]
            r2 = result2 if isinstance(result2, list) else [result2]

            if not r1 or not r2:
                return 0.0

            # Simple comparison for classification
            if len(r1) == 1 and len(r2) == 1:
                v1 = r1[0].get("value", {})
                v2 = r2[0].get("value", {})

                # Classification/choice comparison
                if "choices" in v1 and "choices" in v2:
                    choices1 = set(v1.get("choices", []))
                    choices2 = set(v2.get("choices", []))
                    if choices1 and choices2:
                        return len(choices1 & choices2) / len(choices1 | choices2)

            # For bounding boxes, calculate IoU
            # For polygons, calculate overlap
            # For NER, calculate span overlap

            # Default: simple structural comparison
            return 0.5 if str(r1) == str(r2) else 0.3

        except Exception as e:
            logger.warning(f"Error calculating agreement: {e}")
            return 0.0

    @staticmethod
    @transaction.atomic
    def process_annotation_completion(task_assignment, annotation_result=None):
        """
        Process payment when an annotation is completed

        1. Check for honeypot
        2. Calculate quality score
        3. Calculate payment
        4. Release immediate payment (40%)
        5. Update trust level metrics
        """
        from .models import HoneypotTask, TrustLevel, EarningsTransaction

        annotator = task_assignment.annotator
        task = task_assignment.task

        # Check if honeypot
        try:
            honeypot = task.honeypot_config
            passed, score = honeypot.evaluate_annotation(annotation_result)
            task_assignment.is_honeypot = True
            task_assignment.honeypot_passed = passed
            task_assignment.save(update_fields=["is_honeypot", "honeypot_passed"])

            if not passed:
                # Failed honeypot - flag for review, no payment
                task_assignment.flagged_for_review = True
                task_assignment.flag_reason = (
                    f"Failed honeypot check (score: {score:.2f})"
                )
                task_assignment.save(
                    update_fields=["flagged_for_review", "flag_reason"]
                )

                # Update trust level
                trust_level, _ = TrustLevel.objects.get_or_create(annotator=annotator)
                trust_level.update_metrics(task_assignment)

                return {
                    "success": False,
                    "reason": "honeypot_failed",
                    "score": score,
                    "payment": 0,
                }
        except HoneypotTask.DoesNotExist:
            pass

        # Calculate quality score
        quality_result = PaymentService.calculate_quality_score(
            task_assignment, annotation_result
        )

        # Calculate payment
        payment_result = PaymentService.calculate_task_payment(task_assignment)

        # Release immediate payment (40%)
        immediate_amount = task_assignment.release_immediate_payment()

        # Create transaction record
        if immediate_amount > 0:
            EarningsTransaction.objects.create(
                annotator=annotator,
                transaction_type="earning",
                earning_stage="immediate",
                amount=immediate_amount,
                balance_after=annotator.pending_approval,
                task_assignment=task_assignment,
                description=f"Immediate payment for task {task.id}",
                metadata={
                    "task_id": task.id,
                    "quality_score": quality_result["quality_score"],
                    "trust_multiplier": float(task_assignment.trust_multiplier),
                },
            )

        # Update trust level
        trust_level, _ = TrustLevel.objects.get_or_create(annotator=annotator)
        trust_level.update_metrics(task_assignment)

        return {
            "success": True,
            "immediate_payment": float(immediate_amount),
            "pending_consensus": float(task_assignment.consensus_payment),
            "pending_review": float(task_assignment.review_payment),
            "quality_score": quality_result["quality_score"],
            "trust_level": trust_level.level,
        }

    @staticmethod
    @transaction.atomic
    def process_consensus_validation(task):
        """
        Process consensus validation for all annotations on a task
        Called when overlap is reached

        1. Compare all annotations
        2. Calculate consensus scores
        3. Release consensus payments (40%) for agreeing annotations
        4. Flag outliers for review
        """
        from .models import TaskAssignment, EarningsTransaction

        assignments = TaskAssignment.objects.filter(
            task=task,
            status="completed",
            immediate_released=True,
            consensus_released=False,
        ).select_related("annotator")

        if assignments.count() < 2:
            return {"processed": 0, "message": "Not enough annotations for consensus"}

        # Get all annotation results
        results = []
        for assignment in assignments:
            if assignment.annotation:
                results.append(
                    {
                        "assignment": assignment,
                        "result": assignment.annotation.result,
                    }
                )

        if len(results) < 2:
            return {"processed": 0, "message": "Not enough valid annotations"}

        # Calculate pairwise agreements
        for i, item in enumerate(results):
            agreement_scores = []
            for j, other in enumerate(results):
                if i != j:
                    score = PaymentService.calculate_annotation_agreement(
                        item["result"], other["result"]
                    )
                    agreement_scores.append(score)

            avg_agreement = (
                sum(agreement_scores) / len(agreement_scores) if agreement_scores else 0
            )
            item["consensus_score"] = avg_agreement * 100
            item["assignment"].consensus_agreement = Decimal(str(avg_agreement * 100))
            item["assignment"].save(update_fields=["consensus_agreement"])

        # Release payments for high-agreement annotations
        processed = 0
        flagged = 0

        for item in results:
            assignment = item["assignment"]

            if item["consensus_score"] >= 70:  # 70% agreement threshold
                consensus_amount = assignment.release_consensus_payment()

                if consensus_amount > 0:
                    EarningsTransaction.objects.create(
                        annotator=assignment.annotator,
                        transaction_type="earning",
                        earning_stage="consensus",
                        amount=consensus_amount,
                        balance_after=assignment.annotator.available_balance,
                        task_assignment=assignment,
                        description=f"Consensus payment for task {task.id}",
                        metadata={
                            "task_id": task.id,
                            "consensus_score": item["consensus_score"],
                        },
                    )
                    processed += 1
            else:
                # Low agreement - flag for review
                assignment.flagged_for_review = True
                assignment.flag_reason = (
                    f"Low consensus agreement: {item['consensus_score']:.1f}%"
                )
                assignment.save(update_fields=["flagged_for_review", "flag_reason"])
                flagged += 1

        return {
            "processed": processed,
            "flagged": flagged,
            "total": len(results),
        }

    @staticmethod
    @transaction.atomic
    def process_expert_review(task_assignment, approved=True, reviewer=None, notes=""):
        """
        Process expert review and release final payment (20%)
        """
        from .models import EarningsTransaction

        if not task_assignment.consensus_released:
            return {"success": False, "error": "Consensus payment not yet released"}

        if task_assignment.review_released:
            return {"success": False, "error": "Review payment already released"}

        if approved:
            review_amount = task_assignment.release_review_payment()

            if review_amount > 0:
                EarningsTransaction.objects.create(
                    annotator=task_assignment.annotator,
                    transaction_type="earning",
                    earning_stage="review",
                    amount=review_amount,
                    balance_after=task_assignment.annotator.available_balance,
                    task_assignment=task_assignment,
                    description=f"Review payment for task {task_assignment.task.id}",
                    metadata={
                        "task_id": task_assignment.task.id,
                        "reviewed_by": reviewer.email if reviewer else None,
                        "notes": notes,
                    },
                )

            # Clear flag
            task_assignment.flagged_for_review = False
            task_assignment.save(update_fields=["flagged_for_review"])

            return {
                "success": True,
                "review_payment": float(review_amount),
            }
        else:
            # Rejected - apply penalty
            penalty = task_assignment.review_payment * Decimal("0.5")
            task_assignment.annotator.available_balance -= penalty
            task_assignment.annotator.save(update_fields=["available_balance"])

            EarningsTransaction.objects.create(
                annotator=task_assignment.annotator,
                transaction_type="penalty",
                amount=-penalty,
                balance_after=task_assignment.annotator.available_balance,
                task_assignment=task_assignment,
                description=f"Review penalty for task {task_assignment.task.id}",
                metadata={
                    "task_id": task_assignment.task.id,
                    "reviewed_by": reviewer.email if reviewer else None,
                    "notes": notes,
                },
            )

            # Update trust level with fraud flag
            trust_level = task_assignment.annotator.trust_level
            trust_level.add_fraud_flag(f"Failed review: {notes}")

            return {
                "success": True,
                "penalty": float(penalty),
            }

    @staticmethod
    @transaction.atomic
    def release_final_payments_on_download(project, task_ids=None, downloaded_by=None):
        """
        Release final 20% payment for all eligible tasks when client downloads annotations.

        This is the third and final stage of the 40-40-20 payment split:
        - 40% immediate: Released on annotation submission
        - 40% consensus: Released after consensus validation
        - 20% final: Released when client downloads the annotations

        Args:
            project: The project being exported
            task_ids: Optional list of specific task IDs being downloaded
            downloaded_by: User who initiated the download

        Returns:
            dict with summary of payments released
        """
        from .models import TaskAssignment, EarningsTransaction

        # Find all eligible task assignments
        # Must have:
        # - consensus payment released (meaning annotation was validated)
        # - review payment NOT yet released
        query = TaskAssignment.objects.filter(
            task__project=project,
            status="completed",
            consensus_released=True,
            review_released=False,
        ).select_related("annotator", "task")

        if task_ids:
            query = query.filter(task_id__in=task_ids)

        total_released = Decimal("0")
        processed_count = 0
        annotator_payments = {}

        for assignment in query:
            try:
                review_amount = assignment.release_review_payment()

                if review_amount > 0:
                    # Create transaction record
                    EarningsTransaction.objects.create(
                        annotator=assignment.annotator,
                        transaction_type="earning",
                        earning_stage="review",
                        amount=review_amount,
                        balance_after=assignment.annotator.available_balance,
                        task_assignment=assignment,
                        description=f"Final payment on export for task {assignment.task.id}",
                        metadata={
                            "task_id": assignment.task.id,
                            "project_id": project.id,
                            "downloaded_by": (
                                downloaded_by.email if downloaded_by else None
                            ),
                            "release_trigger": "export_download",
                        },
                    )

                    total_released += review_amount
                    processed_count += 1

                    # Track per-annotator payments
                    annotator_id = assignment.annotator.id
                    if annotator_id not in annotator_payments:
                        annotator_payments[annotator_id] = {
                            "annotator": assignment.annotator.user.email,
                            "tasks": 0,
                            "amount": Decimal("0"),
                        }
                    annotator_payments[annotator_id]["tasks"] += 1
                    annotator_payments[annotator_id]["amount"] += review_amount

            except Exception as e:
                logger.error(
                    f"Error releasing final payment for assignment {assignment.id}: {str(e)}"
                )
                continue

        logger.info(
            f"Released final payments for project {project.id}: "
            f"{processed_count} assignments, ₹{total_released} total"
        )

        return {
            "success": True,
            "project_id": project.id,
            "processed_count": processed_count,
            "total_released": float(total_released),
            "annotator_payments": [
                {
                    "annotator": v["annotator"],
                    "tasks": v["tasks"],
                    "amount": float(v["amount"]),
                }
                for v in annotator_payments.values()
            ],
        }

    @staticmethod
    def get_pending_final_payments(project, task_ids=None):
        """
        Get summary of pending final payments for a project.
        Useful for showing the client how much will be released on download.

        Args:
            project: The project to check
            task_ids: Optional list of specific task IDs

        Returns:
            dict with pending payment summary
        """
        from .models import TaskAssignment

        query = TaskAssignment.objects.filter(
            task__project=project,
            status="completed",
            consensus_released=True,
            review_released=False,
        ).select_related("annotator", "task")

        if task_ids:
            query = query.filter(task_id__in=task_ids)

        total_pending = Decimal("0")
        assignment_count = 0
        annotator_summary = {}

        for assignment in query:
            # Calculate what would be released
            pending_amount = (
                assignment.review_payment
                * assignment.quality_multiplier
                * assignment.trust_multiplier
            )

            total_pending += pending_amount
            assignment_count += 1

            annotator_id = assignment.annotator.id
            if annotator_id not in annotator_summary:
                annotator_summary[annotator_id] = {
                    "annotator": assignment.annotator.user.email,
                    "tasks": 0,
                    "pending_amount": Decimal("0"),
                }
            annotator_summary[annotator_id]["tasks"] += 1
            annotator_summary[annotator_id]["pending_amount"] += pending_amount

        return {
            "project_id": project.id,
            "assignment_count": assignment_count,
            "total_pending": float(total_pending),
            "annotator_summary": [
                {
                    "annotator": v["annotator"],
                    "tasks": v["tasks"],
                    "pending_amount": float(v["pending_amount"]),
                }
                for v in annotator_summary.values()
            ],
        }


class FraudDetectionService:
    """Service for detecting fraudulent annotation patterns"""

    @staticmethod
    def check_annotation_fraud(task_assignment):
        """
        Run fraud detection checks on a completed annotation

        Returns dict with fraud indicators
        """
        flags = []

        # 1. Time-based checks
        time_flags = FraudDetectionService._check_time_fraud(task_assignment)
        flags.extend(time_flags)

        # 2. Pattern-based checks
        pattern_flags = FraudDetectionService._check_pattern_fraud(task_assignment)
        flags.extend(pattern_flags)

        # 3. Quality-based checks
        quality_flags = FraudDetectionService._check_quality_fraud(task_assignment)
        flags.extend(quality_flags)

        # Flag if any issues found
        if flags:
            task_assignment.flagged_for_review = True
            task_assignment.flag_reason = "; ".join(flags)
            task_assignment.save(update_fields=["flagged_for_review", "flag_reason"])

            # Update trust level
            from .models import TrustLevel

            trust_level, _ = TrustLevel.objects.get_or_create(
                annotator=task_assignment.annotator
            )
            trust_level.fraud_flags += 1
            trust_level.last_fraud_check = timezone.now()
            trust_level.save(update_fields=["fraud_flags", "last_fraud_check"])

        return {
            "has_flags": len(flags) > 0,
            "flags": flags,
            "score": max(0, 100 - len(flags) * 25),  # Each flag reduces score by 25
        }

    @staticmethod
    def _check_time_fraud(task_assignment):
        """Check for time-based fraud indicators"""
        flags = []

        time_spent = task_assignment.time_spent_seconds

        # Too fast
        if time_spent > 0 and time_spent < 3:
            flags.append("Suspiciously fast completion (<3 seconds)")

        # Check velocity (tasks per hour)
        from .models import TaskAssignment

        one_hour_ago = timezone.now() - timedelta(hours=1)
        recent_count = TaskAssignment.objects.filter(
            annotator=task_assignment.annotator,
            completed_at__gte=one_hour_ago,
            status="completed",
        ).count()

        if recent_count > 100:
            flags.append(f"High velocity: {recent_count} tasks in last hour")

        return flags

    @staticmethod
    def _check_pattern_fraud(task_assignment):
        """Check for pattern-based fraud indicators"""
        flags = []

        from .models import TaskAssignment

        # Check for repetitive patterns in recent annotations
        recent_assignments = TaskAssignment.objects.filter(
            annotator=task_assignment.annotator, status="completed"
        ).order_by("-completed_at")[:20]

        if recent_assignments.count() >= 10:
            # Check if all annotations are identical
            annotations = [a.annotation for a in recent_assignments if a.annotation]
            if annotations:
                results = [a.result for a in annotations if a.result]
                if results:
                    # Check for high repetition
                    unique_results = set(
                        json.dumps(r, sort_keys=True) for r in results if r
                    )
                    if len(unique_results) == 1 and len(results) > 5:
                        flags.append("All recent annotations are identical")

        return flags

    @staticmethod
    def _check_quality_fraud(task_assignment):
        """Check for quality-based fraud indicators"""
        flags = []

        # Very low quality score
        if task_assignment.quality_score and task_assignment.quality_score < 20:
            flags.append(f"Very low quality score: {task_assignment.quality_score}")

        # Failed honeypot
        if task_assignment.is_honeypot and not task_assignment.honeypot_passed:
            flags.append("Failed honeypot verification")

        # Very low consensus
        if (
            task_assignment.consensus_agreement
            and task_assignment.consensus_agreement < 30
        ):
            flags.append(f"Very low consensus: {task_assignment.consensus_agreement}%")

        return flags


class PayoutService:
    """Service for processing annotator payouts"""

    MINIMUM_PAYOUT = Decimal("100.00")  # Minimum ₹100 for payout
    TEST_MINIMUM_PAYOUT = Decimal("1.00")  # Minimum ₹1 for test payout

    @staticmethod
    def validate_payout_request(annotator, amount, is_test=False):
        """Validate a payout request"""
        errors = []

        # Check minimum amount (lower threshold for test payouts)
        min_amount = (
            PayoutService.TEST_MINIMUM_PAYOUT
            if is_test
            else PayoutService.MINIMUM_PAYOUT
        )
        if amount < min_amount:
            errors.append(f"Minimum payout amount is ₹{min_amount}")

        # Check available balance (skip for test payouts)
        if not is_test and annotator.available_balance < amount:
            errors.append(
                f"Insufficient balance. Available: ₹{annotator.available_balance}"
            )

        # Check for pending payouts (skip for test payouts)
        from .models import PayoutRequest

        if not is_test:
            pending = PayoutRequest.objects.filter(
                annotator=annotator, status__in=["pending", "processing"]
            ).exists()

            if pending:
                errors.append("You have a pending payout request")

        # Check bank details
        if not annotator.bank_name or not annotator.account_number:
            if not annotator.upi_id:
                errors.append("Please add bank account or UPI details")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
        }

    @staticmethod
    @transaction.atomic
    def create_payout_request(annotator, amount, payout_method="bank_transfer"):
        """Create a new payout request"""
        from .models import PayoutRequest

        # Validate
        validation = PayoutService.validate_payout_request(annotator, amount)
        if not validation["valid"]:
            return {
                "success": False,
                "errors": validation["errors"],
            }

        # Snapshot bank details
        bank_details = {}
        if payout_method == "bank_transfer":
            bank_details = {
                "bank_name": annotator.bank_name,
                "account_number": annotator.account_number,
                "ifsc_code": annotator.ifsc_code,
                "account_holder_name": annotator.account_holder_name,
            }
        else:
            bank_details = {
                "upi_id": annotator.upi_id,
            }

        # Create request
        payout = PayoutRequest.objects.create(
            annotator=annotator,
            amount=amount,
            payout_method=payout_method,
            bank_details=bank_details,
        )

        return {
            "success": True,
            "payout_id": payout.id,
            "amount": float(amount),
            "status": payout.status,
        }

    @staticmethod
    def get_earnings_summary(annotator):
        """Get earnings summary for an annotator"""
        from .models import TaskAssignment, EarningsTransaction, AnnotatorStreak
        from django.db.models.functions import TruncDate

        # Get completed assignments
        completed = TaskAssignment.objects.filter(
            annotator=annotator, status="completed"
        )

        # Calculate stats
        total_tasks = completed.count()
        total_earned = annotator.total_earned
        pending_approval = annotator.pending_approval
        available_balance = annotator.available_balance
        total_withdrawn = annotator.total_withdrawn

        # Get recent transactions
        recent_transactions = EarningsTransaction.objects.filter(
            annotator=annotator
        ).order_by("-created_at")[:10]

        # Calculate weekly/monthly earnings
        now = timezone.now()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        weekly_earnings = EarningsTransaction.objects.filter(
            annotator=annotator, transaction_type="earning", created_at__gte=week_ago
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

        monthly_earnings = EarningsTransaction.objects.filter(
            annotator=annotator, transaction_type="earning", created_at__gte=month_ago
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

        # Get trust level info
        try:
            trust_level = annotator.trust_level
            trust_info = {
                "level": trust_level.level,
                "multiplier": float(trust_level.multiplier),
                "tasks_completed": trust_level.tasks_completed,
                "accuracy_score": float(trust_level.accuracy_score),
                "honeypot_pass_rate": float(trust_level.honeypot_pass_rate),
            }
        except Exception:
            trust_info = {
                "level": "new",
                "multiplier": 0.8,
                "tasks_completed": 0,
                "accuracy_score": 0,
                "honeypot_pass_rate": 0,
            }

        # ================================================================
        # NEW: Calculate daily_earnings for earnings trend chart (last 30 days)
        # ================================================================
        thirty_days_ago = now - timedelta(days=30)
        daily_earnings_qs = (
            EarningsTransaction.objects.filter(
                annotator=annotator,
                transaction_type="earning",
                created_at__gte=thirty_days_ago,
            )
            .annotate(date=TruncDate("created_at"))
            .values("date")
            .annotate(amount=Sum("amount"))
            .order_by("date")
        )
        
        # Create a dict for quick lookup
        earnings_by_date = {
            str(entry["date"]): float(entry["amount"])
            for entry in daily_earnings_qs
        }
        
        # Generate all 30 days with 0 for missing days
        daily_earnings = []
        for i in range(30):
            date = (now - timedelta(days=29 - i)).date()
            date_str = str(date)
            daily_earnings.append({
                "date": date_str,
                "amount": earnings_by_date.get(date_str, 0)
            })

        # ================================================================
        # NEW: Calculate activity_days for streak calendar (last 60 days)
        # ================================================================
        sixty_days_ago = now - timedelta(days=60)
        activity_dates = (
            TaskAssignment.objects.filter(
                annotator=annotator,
                status="completed",
                completed_at__gte=sixty_days_ago,
            )
            .annotate(date=TruncDate("completed_at"))
            .values_list("date", flat=True)
            .distinct()
        )
        activity_days = [str(d) for d in activity_dates if d]

        # ================================================================
        # NEW: Get current streak from AnnotatorStreak model
        # ================================================================
        activity_streak = 0
        try:
            streak = AnnotatorStreak.objects.get(annotator=annotator)
            activity_streak = streak.current_streak
        except AnnotatorStreak.DoesNotExist:
            # Calculate streak from activity_days
            today = now.date()
            streak_count = 0
            for i in range(60):
                check_date = str(today - timedelta(days=i))
                if check_date in activity_days:
                    streak_count += 1
                else:
                    break
            activity_streak = streak_count

        return {
            "total_tasks": total_tasks,
            "total_earned": float(total_earned),
            "pending_approval": float(pending_approval),
            "available_balance": float(available_balance),
            "total_withdrawn": float(total_withdrawn),
            "weekly_earnings": float(weekly_earnings),
            "monthly_earnings": float(monthly_earnings),
            "trust_level": trust_info,
            "recent_transactions": [
                {
                    "id": t.id,
                    "type": t.transaction_type,
                    "stage": t.earning_stage,
                    "amount": float(t.amount),
                    "balance_after": float(t.balance_after),
                    "description": t.description,
                    "created_at": t.created_at.isoformat(),
                }
                for t in recent_transactions
            ],
            # NEW fields for frontend calendar and earnings trend
            "daily_earnings": daily_earnings,
            "activity_days": activity_days,
            "activity_streak": activity_streak,
        }

    @staticmethod
    @transaction.atomic
    def process_payout_with_razorpay(payout_request):
        """
        Process a payout request via RazorpayX

        Args:
            payout_request: PayoutRequest model instance

        Returns:
            dict: Result with success status and details
        """
        from .razorpayx_payout import process_annotator_payout, RazorpayXPayoutError

        try:
            # Call RazorpayX processing
            result = process_annotator_payout(payout_request)

            if result["success"]:
                # Payout initiated successfully
                logger.info(
                    f"Payout {payout_request.id} initiated: {result['payout_id']}"
                )
                return {
                    "success": True,
                    "payout_id": result["payout_id"],
                    "status": result.get("status", "processing"),
                    "message": "Payout initiated successfully",
                }
            else:
                # Failed to process
                payout_request.status = "failed"
                payout_request.rejection_reason = result.get("error", "Unknown error")
                payout_request.save(update_fields=["status", "rejection_reason"])
                return {
                    "success": False,
                    "error": result.get("error", "Payout processing failed"),
                }

        except Exception as e:
            logger.error(f"Payout processing error: {e}")
            payout_request.status = "failed"
            payout_request.rejection_reason = str(e)
            payout_request.save(update_fields=["status", "rejection_reason"])
            return {
                "success": False,
                "error": str(e),
            }

    @staticmethod
    def create_test_payout(user, amount_inr=1, payout_method="upi"):
        """
        Create a test payout of ₹1 to verify integration

        Args:
            user: User model instance (annotator or expert)
            amount_inr: Amount in INR (default ₹1)
            payout_method: 'upi' or 'bank_transfer'

        Returns:
            dict: Test payout result
        """
        from .razorpayx_payout import create_test_payout as razorpay_test_payout
        from .models import AnnotatorProfile

        try:
            # Get annotator profile
            try:
                profile = AnnotatorProfile.objects.get(user=user)
            except AnnotatorProfile.DoesNotExist:
                return {
                    "success": False,
                    "error": "Annotator profile not found",
                }

            # Get payment details
            name = user.get_full_name() or user.email
            email = user.email

            if payout_method == "upi":
                if not profile.upi_id:
                    return {
                        "success": False,
                        "error": "UPI ID not configured. Please add UPI ID first.",
                    }
                result = razorpay_test_payout(
                    email=email,
                    name=name,
                    upi_id=profile.upi_id,
                    amount_inr=amount_inr,
                )
            else:
                # Bank transfer
                if not profile.account_number or not profile.ifsc_code:
                    return {
                        "success": False,
                        "error": "Bank details not configured. Please add bank details first.",
                    }
                result = razorpay_test_payout(
                    email=email,
                    name=name,
                    bank_details={
                        "account_number": profile.account_number,
                        "ifsc_code": profile.ifsc_code,
                        "account_holder_name": profile.account_holder_name or name,
                    },
                    amount_inr=amount_inr,
                )

            return result

        except Exception as e:
            logger.error(f"Test payout error: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    @staticmethod
    def approve_and_process_payout(payout_request, admin_user):
        """
        Approve a payout request and process it via RazorpayX

        Args:
            payout_request: PayoutRequest instance
            admin_user: Admin user approving the payout

        Returns:
            dict: Processing result
        """
        from .models import EarningsTransaction

        if payout_request.status != "pending":
            return {
                "success": False,
                "error": f"Cannot approve payout with status: {payout_request.status}",
            }

        annotator = payout_request.annotator

        # Check if annotator has sufficient balance
        if annotator.available_balance < payout_request.amount:
            return {
                "success": False,
                "error": f"Insufficient balance. Available: ₹{annotator.available_balance}",
            }

        # Process via RazorpayX
        result = PayoutService.process_payout_with_razorpay(payout_request)

        if result["success"]:
            # Deduct from annotator balance
            annotator.available_balance -= payout_request.amount
            annotator.total_withdrawn += payout_request.amount
            annotator.save(update_fields=["available_balance", "total_withdrawn"])

            # Create withdrawal transaction
            EarningsTransaction.objects.create(
                annotator=annotator,
                transaction_type="withdrawal",
                amount=-payout_request.amount,
                balance_after=annotator.available_balance,
                description=f"Payout #{payout_request.id} - {payout_request.payout_method}",
            )

            # Update payout request
            payout_request.approved_by = admin_user
            payout_request.approved_at = timezone.now()
            payout_request.save(update_fields=["approved_by", "approved_at"])

        return result


class GamificationService:
    """Service for gamified payment features - streaks, achievements, leaderboards"""

    # Leaderboard bonus distribution (top 10 positions)
    LEADERBOARD_BONUSES = {
        1: Decimal("500"),  # 1st place
        2: Decimal("300"),  # 2nd place
        3: Decimal("200"),  # 3rd place
        4: Decimal("100"),
        5: Decimal("75"),
        6: Decimal("50"),
        7: Decimal("40"),
        8: Decimal("30"),
        9: Decimal("20"),
        10: Decimal("10"),
    }

    # Volume achievement thresholds
    VOLUME_ACHIEVEMENTS = [
        ("first_task", 1, Decimal("10"), "bronze", "First Steps"),
        ("task_10", 10, Decimal("25"), "bronze", "Getting Started"),
        ("task_50", 50, Decimal("50"), "silver", "Productive Bee"),
        ("task_100", 100, Decimal("100"), "silver", "Century Club"),
        ("task_500", 500, Decimal("250"), "gold", "Power Annotator"),
        ("task_1000", 1000, Decimal("500"), "gold", "Annotation Master"),
        ("task_5000", 5000, Decimal("1000"), "platinum", "Annotation Legend"),
        ("task_10000", 10000, Decimal("2000"), "diamond", "Ultimate Annotator"),
    ]

    # Quality achievement thresholds
    QUALITY_ACHIEVEMENTS = [
        ("quality_80", 80, 50, Decimal("50"), "silver", "Quality Minded"),
        ("quality_90", 90, 100, Decimal("100"), "gold", "Quality Expert"),
        ("quality_95", 95, 200, Decimal("250"), "platinum", "Perfectionist"),
        ("quality_99", 99, 500, Decimal("500"), "diamond", "Flawless"),
    ]

    # Streak achievement thresholds
    STREAK_ACHIEVEMENTS = [
        ("streak_3", 3, Decimal("15"), "bronze", "3 Day Streak"),
        ("streak_7", 7, Decimal("50"), "silver", "Week Warrior"),
        ("streak_14", 14, Decimal("100"), "gold", "Fortnight Champion"),
        ("streak_30", 30, Decimal("300"), "platinum", "Monthly Master"),
        ("streak_100", 100, Decimal("1000"), "diamond", "100 Day Legend"),
    ]

    @staticmethod
    @transaction.atomic
    def process_task_completion(task_assignment):
        """
        Process all gamification effects when a task is completed.

        This is the main entry point for gamification after annotation.

        Returns dict with all bonuses applied.
        """
        from .models import (
            AnnotatorStreak,
            Achievement,
            AnnotatorAchievement,
            DailyLeaderboard,
            EarningsTransaction,
            TrustLevel,
        )

        annotator = task_assignment.annotator
        results = {
            "streak_bonus": Decimal("0"),
            "achievement_bonuses": [],
            "leaderboard_bonus": Decimal("0"),
            "skill_bonus": Decimal("0"),
            "total_bonus": Decimal("0"),
        }

        # 1. Update streak
        streak, created = AnnotatorStreak.objects.get_or_create(annotator=annotator)
        new_streak = streak.record_activity()
        streak_multiplier = streak.get_streak_multiplier()

        # Calculate streak bonus on base payment
        if streak_multiplier > Decimal("1.0"):
            streak_bonus = task_assignment.base_payment * (
                streak_multiplier - Decimal("1.0")
            )
            results["streak_bonus"] = streak_bonus
            streak.total_streak_bonus += streak_bonus
            streak.save(update_fields=["total_streak_bonus"])

        # 2. Update trust level
        try:
            trust_level = annotator.trust_level
        except TrustLevel.DoesNotExist:
            trust_level = TrustLevel.objects.create(annotator=annotator)

        trust_level.update_metrics(task_assignment)

        # 3. Check and award achievements
        achievement_bonuses = GamificationService._check_achievements(
            annotator, trust_level, streak
        )
        results["achievement_bonuses"] = achievement_bonuses

        # 4. Update daily leaderboard
        today = timezone.now().date()
        leaderboard, _ = DailyLeaderboard.objects.get_or_create(
            date=today,
            annotator=annotator,
            defaults={"tasks_completed": 0, "earnings": Decimal("0")},
        )
        leaderboard.tasks_completed += 1
        leaderboard.earnings += task_assignment.amount_paid
        if task_assignment.quality_score:
            # Rolling average for quality
            n = leaderboard.tasks_completed
            leaderboard.quality_score = (
                leaderboard.quality_score * (n - 1) + task_assignment.quality_score
            ) / n
        leaderboard.save()

        # 5. Check skill badges
        skill_bonus = GamificationService._update_skill_badges(task_assignment)
        results["skill_bonus"] = skill_bonus

        # Calculate total bonus
        results["total_bonus"] = (
            results["streak_bonus"]
            + sum(a["bonus"] for a in results["achievement_bonuses"])
            + results["skill_bonus"]
        )

        # Create bonus transaction if applicable
        if results["total_bonus"] > 0:
            EarningsTransaction.objects.create(
                annotator=annotator,
                transaction_type="bonus",
                amount=results["total_bonus"],
                balance_after=annotator.available_balance + results["total_bonus"],
                task_assignment=task_assignment,
                description=f"Gamification bonuses for task completion",
                metadata={
                    "streak_bonus": float(results["streak_bonus"]),
                    "achievement_bonuses": results["achievement_bonuses"],
                    "skill_bonus": float(results["skill_bonus"]),
                },
            )

            # Update annotator balance
            annotator.available_balance += results["total_bonus"]
            annotator.total_earned += results["total_bonus"]
            annotator.save(update_fields=["available_balance", "total_earned"])

        return results

    @staticmethod
    def _check_achievements(annotator, trust_level, streak):
        """Check and award any newly earned achievements"""
        from .models import Achievement, AnnotatorAchievement

        earned = []

        # Ensure achievements exist in DB
        GamificationService._ensure_achievements_exist()

        # Check volume achievements
        for (
            code,
            threshold,
            bonus,
            tier,
            name,
        ) in GamificationService.VOLUME_ACHIEVEMENTS:
            if trust_level.tasks_completed >= threshold:
                achievement = Achievement.objects.filter(code=code).first()
                if achievement:
                    aa, created = AnnotatorAchievement.objects.get_or_create(
                        annotator=annotator,
                        achievement=achievement,
                        defaults={"bonus_paid": bonus},
                    )
                    if created:
                        earned.append(
                            {
                                "code": code,
                                "name": name,
                                "tier": tier,
                                "bonus": float(bonus),
                            }
                        )

        # Check quality achievements
        for (
            code,
            accuracy,
            min_tasks,
            bonus,
            tier,
            name,
        ) in GamificationService.QUALITY_ACHIEVEMENTS:
            if (
                trust_level.tasks_completed >= min_tasks
                and trust_level.accuracy_score >= accuracy
            ):
                achievement = Achievement.objects.filter(code=code).first()
                if achievement:
                    aa, created = AnnotatorAchievement.objects.get_or_create(
                        annotator=annotator,
                        achievement=achievement,
                        defaults={"bonus_paid": bonus},
                    )
                    if created:
                        earned.append(
                            {
                                "code": code,
                                "name": name,
                                "tier": tier,
                                "bonus": float(bonus),
                            }
                        )

        # Check streak achievements
        for (
            code,
            streak_days,
            bonus,
            tier,
            name,
        ) in GamificationService.STREAK_ACHIEVEMENTS:
            if streak.longest_streak >= streak_days:
                achievement = Achievement.objects.filter(code=code).first()
                if achievement:
                    aa, created = AnnotatorAchievement.objects.get_or_create(
                        annotator=annotator,
                        achievement=achievement,
                        defaults={"bonus_paid": bonus},
                    )
                    if created:
                        earned.append(
                            {
                                "code": code,
                                "name": name,
                                "tier": tier,
                                "bonus": float(bonus),
                            }
                        )

        return earned

    @staticmethod
    def _ensure_achievements_exist():
        """Ensure all achievement definitions exist in database"""
        from .models import Achievement

        # Volume achievements
        for (
            code,
            threshold,
            bonus,
            tier,
            name,
        ) in GamificationService.VOLUME_ACHIEVEMENTS:
            Achievement.objects.get_or_create(
                code=code,
                defaults={
                    "name": name,
                    "description": f"Complete {threshold} tasks",
                    "category": "volume",
                    "tier": tier,
                    "bonus_amount": bonus,
                    "requirement_type": "tasks_completed",
                    "requirement_value": threshold,
                },
            )

        # Quality achievements
        for (
            code,
            accuracy,
            min_tasks,
            bonus,
            tier,
            name,
        ) in GamificationService.QUALITY_ACHIEVEMENTS:
            Achievement.objects.get_or_create(
                code=code,
                defaults={
                    "name": name,
                    "description": f"Achieve {accuracy}% accuracy on {min_tasks}+ tasks",
                    "category": "quality",
                    "tier": tier,
                    "bonus_amount": bonus,
                    "requirement_type": "accuracy_score",
                    "requirement_value": accuracy,
                },
            )

        # Streak achievements
        for (
            code,
            streak_days,
            bonus,
            tier,
            name,
        ) in GamificationService.STREAK_ACHIEVEMENTS:
            Achievement.objects.get_or_create(
                code=code,
                defaults={
                    "name": name,
                    "description": f"Maintain a {streak_days}-day streak",
                    "category": "streak",
                    "tier": tier,
                    "bonus_amount": bonus,
                    "requirement_type": "streak_days",
                    "requirement_value": streak_days,
                },
            )

    @staticmethod
    def _update_skill_badges(task_assignment):
        """Update skill badge progress and return any bonus"""
        from .models import AnnotatorSkillBadge, SkillBadge

        # Determine annotation type from task
        annotation_type = "default"
        try:
            task = task_assignment.task
            if task.project and task.project.label_config:
                config = task.project.label_config.lower()
                if "rectanglelabels" in config or "rectangle" in config:
                    annotation_type = "bounding_box"
                elif "polygonlabels" in config or "polygon" in config:
                    annotation_type = "polygon"
                elif "brushlabels" in config or "brush" in config:
                    annotation_type = "segmentation"
                elif "keypointlabels" in config or "keypoint" in config:
                    annotation_type = "keypoint"
                elif "choices" in config:
                    annotation_type = "classification"
                elif "labels" in config and "text" in config:
                    annotation_type = "ner"
        except Exception:
            pass

        bonus = Decimal("0")

        # Find matching skill badge
        skill_badge = SkillBadge.objects.filter(
            annotation_type=annotation_type, is_active=True
        ).first()

        if skill_badge:
            annotator_badge, created = AnnotatorSkillBadge.objects.get_or_create(
                annotator=task_assignment.annotator, skill_badge=skill_badge
            )

            was_earned = annotator_badge.is_earned
            quality = task_assignment.quality_score or Decimal("80")
            annotator_badge.update_progress(quality)

            # Award bonus if just earned
            if annotator_badge.is_earned and not was_earned:
                bonus = Decimal("100")  # Skill badge bonus

        return bonus

    @staticmethod
    @transaction.atomic
    def distribute_daily_leaderboard_bonuses(date=None):
        """
        Distribute bonuses to top performers of the day.

        Should be called daily after midnight.
        """
        from .models import (
            DailyLeaderboard,
            EarningsTransaction,
            BonusPool,
            BonusDistribution,
        )

        if date is None:
            date = (timezone.now() - timedelta(days=1)).date()

        # Get top performers sorted by tasks completed
        top_performers = DailyLeaderboard.objects.filter(date=date).order_by(
            "-tasks_completed", "-quality_score"
        )[:10]

        results = {
            "date": str(date),
            "distributions": [],
            "total_distributed": Decimal("0"),
        }

        for rank, entry in enumerate(top_performers, 1):
            bonus = GamificationService.LEADERBOARD_BONUSES.get(rank, Decimal("0"))

            if bonus > 0:
                # Update rank
                entry.rank = rank
                entry.leaderboard_bonus = bonus
                entry.save(update_fields=["rank", "leaderboard_bonus"])

                # Create transaction
                annotator = entry.annotator
                EarningsTransaction.objects.create(
                    annotator=annotator,
                    transaction_type="bonus",
                    amount=bonus,
                    balance_after=annotator.available_balance + bonus,
                    description=f"Daily leaderboard #{rank} bonus for {date}",
                    metadata={
                        "leaderboard_date": str(date),
                        "rank": rank,
                        "tasks_completed": entry.tasks_completed,
                    },
                )

                # Update balance
                annotator.available_balance += bonus
                annotator.total_earned += bonus
                annotator.save(update_fields=["available_balance", "total_earned"])

                results["distributions"].append(
                    {
                        "rank": rank,
                        "annotator_id": annotator.id,
                        "bonus": float(bonus),
                        "tasks": entry.tasks_completed,
                    }
                )
                results["total_distributed"] += bonus

        results["total_distributed"] = float(results["total_distributed"])
        return results

    @staticmethod
    def get_annotator_gamification_stats(annotator):
        """Get full gamification stats for an annotator"""
        from .models import (
            AnnotatorStreak,
            AnnotatorAchievement,
            DailyLeaderboard,
            AnnotatorSkillBadge,
            TrustLevel,
        )

        # Get streak info
        streak_info = {"current_streak": 0, "longest_streak": 0, "multiplier": 1.0}
        try:
            streak = annotator.streak
            streak_info = {
                "current_streak": streak.current_streak,
                "longest_streak": streak.longest_streak,
                "multiplier": float(streak.get_streak_multiplier()),
                "tasks_this_week": streak.tasks_this_week,
                "tasks_this_month": streak.tasks_this_month,
                "total_streak_bonus": float(streak.total_streak_bonus),
            }
        except AnnotatorStreak.DoesNotExist:
            pass

        # Get achievements
        achievements = AnnotatorAchievement.objects.filter(
            annotator=annotator
        ).select_related("achievement")

        earned_achievements = [
            {
                "code": aa.achievement.code,
                "name": aa.achievement.name,
                "tier": aa.achievement.tier,
                "category": aa.achievement.category,
                "earned_at": aa.earned_at.isoformat(),
                "bonus_paid": float(aa.bonus_paid),
            }
            for aa in achievements
        ]

        # Get trust level
        trust_info = {"level": "new", "multiplier": 0.8}
        try:
            trust = annotator.trust_level
            trust_info = {
                "level": trust.level,
                "multiplier": float(trust.multiplier),
                "tasks_completed": trust.tasks_completed,
                "accuracy_score": float(trust.accuracy_score),
                "honeypot_pass_rate": float(trust.honeypot_pass_rate),
            }
        except TrustLevel.DoesNotExist:
            pass

        # Get skill badges
        skill_badges = AnnotatorSkillBadge.objects.filter(
            annotator=annotator
        ).select_related("skill_badge")

        badges = [
            {
                "name": sb.skill_badge.name,
                "annotation_type": sb.skill_badge.annotation_type,
                "is_earned": sb.is_earned,
                "progress": sb.tasks_completed,
                "required": sb.skill_badge.required_tasks,
                "accuracy": float(sb.current_accuracy),
            }
            for sb in skill_badges
        ]

        # Get recent leaderboard positions
        recent_leaderboard = DailyLeaderboard.objects.filter(
            annotator=annotator, rank__isnull=False
        ).order_by("-date")[:7]

        leaderboard_history = [
            {
                "date": str(lb.date),
                "rank": lb.rank,
                "tasks": lb.tasks_completed,
                "bonus": float(lb.leaderboard_bonus),
            }
            for lb in recent_leaderboard
        ]

        return {
            "streak": streak_info,
            "trust_level": trust_info,
            "achievements": earned_achievements,
            "achievement_count": len(earned_achievements),
            "skill_badges": badges,
            "leaderboard_history": leaderboard_history,
        }





