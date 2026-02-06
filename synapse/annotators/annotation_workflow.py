"""
Annotation Workflow Service

Handles:
1. Annotation creation/update restrictions
2. Annotation isolation between annotators
3. Auto-consolidation when all annotators complete
4. Auto-creation of expert review tasks for disagreements
5. Client visibility controls based on review status
"""

import logging
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.conf import settings

logger = logging.getLogger(__name__)

# Threshold settings
DISAGREEMENT_THRESHOLD = Decimal("70.0")  # Below this = high disagreement, needs review
RANDOM_SAMPLE_RATE = 0.05  # 5% of tasks sent for random sampling review


class AnnotationWorkflowService:
    """
    Centralized service for managing annotation workflow rules
    """

    @staticmethod
    def can_create_annotation(user, task):
        """
        Check if user can create a NEW annotation on this task.
        AUTO-CREATES assignment if user is an annotator but not assigned yet.

        Rules:
        1. User must be an annotator OR admin/staff
        2. If annotator, auto-create assignment if needed
        3. User must NOT already have an annotation on this task
        4. Task consensus must not be finalized
        5. Check if task still needs more annotations (respect overlap)

        Returns: (can_create: bool, reason: str)
        """
        from .models import (
            TaskAssignment,
            AnnotatorProfile,
            TaskConsensus,
            ProjectAssignment,
        )
        from tasks.models import Annotation
        from django.db import transaction

        # Allow admins and staff to annotate without restrictions
        if user.is_staff or user.is_superuser:
            return True, "Staff/admin can annotate any task"

        # Check if user is an annotator
        try:
            profile = user.annotator_profile
        except AnnotatorProfile.DoesNotExist:
            return True, "Not an annotator - using standard permissions"

        # Check if already has an annotation
        existing_annotation = Annotation.objects.filter(
            task=task, completed_by=user, was_cancelled=False
        ).first()

        if existing_annotation:
            return (
                False,
                "You have already submitted an annotation for this task. Use update instead.",
            )

        # Check if task consensus is finalized
        try:
            consensus = task.consensus
            if consensus.status == "finalized":
                return (
                    False,
                    "This task has been finalized and cannot accept new annotations",
                )
        except TaskConsensus.DoesNotExist:
            pass  # No consensus tracking yet, allow

        # Check if task still needs more annotations (respect overlap)
        project = task.project
        required_overlap = getattr(project, "required_overlap", 3)
        current_annotations = Annotation.objects.filter(
            task=task, was_cancelled=False
        ).count()

        if current_annotations >= required_overlap:
            return (
                False,
                f"This task already has {current_annotations}/{required_overlap} annotations (overlap limit reached)",
            )

        # Check if assigned to this task
        assignment = TaskAssignment.objects.filter(annotator=profile, task=task).first()

        if not assignment:
            # AUTO-CREATE ASSIGNMENT if annotator is assigned to project
            project_assignment = ProjectAssignment.objects.filter(
                annotator=profile, project=task.project, active=True
            ).first()

            if project_assignment:
                # Auto-create task assignment
                try:
                    with transaction.atomic():
                        assignment = TaskAssignment.objects.create(
                            annotator=profile,
                            task=task,
                            status="assigned",
                        )
                        logger.info(
                            f"Auto-created assignment for {user.email} on task {task.id}"
                        )
                except Exception as e:
                    logger.error(f"Failed to auto-create assignment: {e}")
                    return False, "Could not assign you to this task automatically"
            else:
                return (
                    False,
                    "You are not assigned to this project. Please contact admin.",
                )

        # Check assignment status
        if assignment.status not in ["assigned", "in_progress"]:
            return (
                False,
                f"Your assignment status is '{assignment.status}' and cannot be annotated",
            )

        return True, "OK"

    @staticmethod
    def can_update_annotation(user, annotation):
        """
        Check if user can UPDATE their existing annotation.

        Rules:
        1. User must be the owner of the annotation
        2. Task consensus must not be finalized
        3. If consensus is reached but not finalized, updates may be restricted

        Returns: (can_update: bool, reason: str)
        """
        from .models import TaskConsensus

        # Check ownership
        if annotation.completed_by != user:
            return False, "You can only update your own annotations"

        # Check consensus status
        try:
            consensus = annotation.task.consensus
            if consensus.status == "finalized":
                return False, "This task has been finalized and cannot be modified"
            if consensus.status in ["consensus_reached", "review_required"]:
                # Allow updates until expert review is done
                return True, "Task is in review - updates allowed until finalization"
        except TaskConsensus.DoesNotExist:
            pass

        return True, "OK"

    @staticmethod
    def get_visible_annotations(user, task, include_own=True):
        """
        Get annotations visible to a user for a task.

        Rules for annotators:
        - Can only see their own annotation(s)
        - Cannot see other annotators' work

        Rules for experts:
        - For tasks WITH consolidated results: See a virtual "consolidated annotation"
        - For tasks WITHOUT consolidated results: See all individual annotations for review
        - The consolidated annotation is created from TaskConsensus.consolidated_result

        Rules for clients/admins:
        - Can only see annotations AFTER expert review is complete (finalized)
        - OR if required_overlap is 1 (no consensus needed)

        Returns: QuerySet of Annotation
        """
        from tasks.models import Annotation
        from .models import AnnotatorProfile, ExpertProfile, TaskConsensus

        # Check if user is an annotator
        is_annotator = hasattr(user, "annotator_profile")
        is_expert_role = getattr(user, "is_expert", False)
        is_admin = user.is_superuser

        # Check if user is actively working as an expert (has ProjectAssignment as reviewer)
        is_active_expert = False
        if is_expert_role:
             try:
                 from annotators.models import ProjectAssignment 
                 is_active_expert = ProjectAssignment.objects.filter(
                     annotator__user=user, 
                     project=task.project,
                     role='reviewer',
                     active=True
                 ).exists()
             except Exception:
                 is_active_expert = False

        # Annotators can only see their own annotations
        # Even if user has is_expert flag, they should only see own annotations
        # unless they have an active Expert assignment
        if is_annotator and not is_active_expert and not is_admin:
            if include_own:
                return Annotation.objects.filter(
                    task=task, completed_by=user, was_cancelled=False
                )
            return Annotation.objects.none()

        # Experts: Check if consolidated result exists
        if is_active_expert:
            try:
                consensus = task.consensus
                if consensus.consolidated_result and consensus.status in [
                    "review_required",
                    "consensus_reached",
                ]:
                    # Task has consolidated result - create virtual consolidated annotation
                    # This is a pseudo-annotation that doesn't exist in DB but is serialized
                    # Get the first annotation as a template for metadata
                    template_ann = Annotation.objects.filter(
                        task=task, was_cancelled=False
                    ).first()

                    if template_ann:
                        # Create a pseudo-annotation object with consolidated result
                        consolidated_ann = Annotation(
                            id=-1,  # Negative ID to indicate it's virtual
                            task=task,
                            result=consensus.consolidated_result,
                            was_cancelled=False,
                            ground_truth=False,
                            created_at=consensus.updated_at,
                            updated_at=consensus.updated_at,
                            lead_time=0,
                            completed_by_id=template_ann.completed_by_id,
                            # Add metadata to identify as consolidated
                        )
                        # Mark it as consolidated for frontend identification
                        consolidated_ann._is_consolidated = True
                        consolidated_ann._consolidation_method = (
                            consensus.consolidation_method
                        )
                        consolidated_ann._average_agreement = float(
                            consensus.average_agreement or 0
                        )

                        # Return a list with just the consolidated annotation
                        # Django doesn't support returning a single object from ORM methods,
                        # so we return a filtered queryset that will be empty, but we'll
                        # inject the consolidated annotation in the serializer

                        # Store the consolidated annotation on the task object for retrieval
                        task._consolidated_annotation = consolidated_ann

                        # Return empty queryset - serializer will check for _consolidated_annotation
                        return Annotation.objects.none()
            except TaskConsensus.DoesNotExist:
                pass

            # No consolidated result - show all individual annotations for review
            return Annotation.objects.filter(task=task, was_cancelled=False)

        # Client/admin visibility rules
        # Check if task requires consensus
        project = task.project
        required_overlap = getattr(project, "required_overlap", 1)

        if required_overlap <= 1:
            # No consensus needed - show all annotations
            return Annotation.objects.filter(task=task, was_cancelled=False)

        # TEMPORARY FIX: Allow clients to see all annotations for review purposes
        # The original logic hid everything until finalized.
        return Annotation.objects.filter(task=task, was_cancelled=False)

    @staticmethod
    def get_visible_annotators(user, task):
        """
        Get annotators visible to a user for a task.

        Rules:
        - Annotators cannot see other annotators
        - Experts can see all annotators
        - Clients can only see annotators after review is complete

        Returns: List of annotator info dicts
        """
        from .models import TaskAssignment, TaskConsensus

        is_annotator = hasattr(user, "annotator_profile")
        is_expert_role = getattr(user, "is_expert", False)
        is_admin = user.is_superuser

        # Check if user is actively working as an expert (has ExpertProfile)
        is_active_expert = hasattr(user, "expert_profile") and is_expert_role

        # Annotators cannot see other annotators
        if is_annotator and not is_active_expert and not is_admin:
            return []

        # Check if task is finalized
        project = task.project
        required_overlap = getattr(project, "required_overlap", 1)

        if required_overlap <= 1:
            # No consensus - show annotators
            assignments = TaskAssignment.objects.filter(task=task).select_related(
                "annotator__user"
            )

            return [
                {
                    "user_id": a.annotator.user.id,
                    "email": a.annotator.user.email,
                    "status": a.status,
                }
                for a in assignments
            ]

        # Consensus required
        if is_expert:
            # Experts can always see annotators for review
            assignments = TaskAssignment.objects.filter(task=task).select_related(
                "annotator__user"
            )

            return [
                {
                    "user_id": a.annotator.user.id,
                    "email": a.annotator.user.email,
                    "status": a.status,
                }
                for a in assignments
            ]

        # Client/admin - check finalization
        try:
            consensus = task.consensus
            if consensus.status == "finalized":
                assignments = TaskAssignment.objects.filter(task=task).select_related(
                    "annotator__user"
                )

                return [
                    {
                        "user_id": a.annotator.user.id,
                        "email": a.annotator.user.email,
                        "status": a.status,
                    }
                    for a in assignments
                ]
        except TaskConsensus.DoesNotExist:
            pass

        return []

    @staticmethod
    @transaction.atomic
    def on_annotation_created(annotation):
        """
        Called after an annotation is created.

        1. Check if honeypot and evaluate (honeypots bypass consolidation)
        2. Update task assignment status
        3. Check if all annotations are complete
        4. Trigger consolidation if ready
        """
        from .models import TaskAssignment, TaskConsensus

        task = annotation.task
        user = annotation.completed_by
        project = task.project

        # =====================================================================
        # HONEYPOT DETECTION AND EVALUATION
        # =====================================================================
        # Check if this is a honeypot submission - if so, evaluate and skip
        # normal consolidation workflow. Honeypots are for quality monitoring.
        try:
            from .honeypot_handler import HoneypotHandler
            
            is_honeypot, honeypot_result = HoneypotHandler.handle_annotation_submission(
                annotation=annotation,
                user=user
            )
            
            if is_honeypot:
                logger.info(
                    f"Honeypot task {task.id} evaluated for {user.email}: "
                    f"passed={honeypot_result.get('evaluation', {}).get('passed', False)}"
                )
                # Honeypots skip consolidation - just update assignment and return
                try:
                    profile = user.annotator_profile
                    assignment = TaskAssignment.objects.filter(
                        annotator=profile, task=task
                    ).first()
                    if assignment:
                        assignment.status = "completed"
                        assignment.completed_at = timezone.now()
                        assignment.annotation_id = annotation.id
                        assignment.save(update_fields=["status", "completed_at", "annotation_id"])
                    
                    # Update streak for honeypot completion as well
                    from .models import AnnotatorStreak
                    streak, created = AnnotatorStreak.objects.get_or_create(
                        annotator=profile
                    )
                    streak.record_activity()
                except Exception as e:
                    logger.warning(f"Could not update honeypot task assignment: {e}")
                return  # Skip consolidation for honeypots
        except ImportError:
            pass  # Honeypot module not available
        except Exception as e:
            logger.warning(f"Error in honeypot handling: {e}")
            # Continue with normal workflow if honeypot handling fails

        # Update task assignment and record streak activity
        try:
            profile = user.annotator_profile
            assignment = TaskAssignment.objects.filter(
                annotator=profile, task=task
            ).first()

            if assignment:
                assignment.status = "completed"
                assignment.completed_at = timezone.now()
                assignment.annotation_id = annotation.id
                assignment.save(
                    update_fields=["status", "completed_at", "annotation_id"]
                )
                logger.info(f"Updated assignment {assignment.id} to completed")
                
                # =====================================================================
                # UPDATE ANNOTATOR STREAK
                # =====================================================================
                # Record daily activity for streak tracking
                try:
                    from .models import AnnotatorStreak
                    streak, created = AnnotatorStreak.objects.get_or_create(
                        annotator=profile
                    )
                    new_streak = streak.record_activity()
                    logger.info(f"Updated streak for {user.email}: {new_streak} days")
                except Exception as streak_error:
                    logger.warning(f"Could not update annotator streak: {streak_error}")
        except Exception as e:
            logger.warning(f"Could not update task assignment: {e}")

        # Check if consensus tracking is needed
        required_overlap = getattr(project, "required_overlap", 1)
        if required_overlap <= 1:
            return  # No consensus needed

        # Get or create consensus record
        consensus, created = TaskConsensus.objects.get_or_create(
            task=task,
            defaults={
                "required_annotations": required_overlap,
                "current_annotations": 0,
            },
        )

        # Update annotation count
        from tasks.models import Annotation

        current_count = Annotation.objects.filter(
            task=task, was_cancelled=False
        ).count()

        consensus.current_annotations = current_count
        consensus.save(update_fields=["current_annotations"])

        # Check if all required annotations are in
        if current_count >= required_overlap:
            logger.info(
                f"Task {task.id} has all required annotations ({current_count}/{required_overlap}). Triggering consolidation."
            )
            AnnotationWorkflowService.trigger_consolidation(task, consensus)

    @staticmethod
    @transaction.atomic
    def trigger_consolidation(task, consensus):
        """
        Trigger consolidation when all annotations are received.

        Steps:
        1. Get all completed assignments with annotations
        2. Calculate pairwise agreement scores between annotators
        3. Consolidate annotations based on annotation type
        4. Calculate individual annotator quality scores
        5. Determine if consensus is reached or needs expert review
        6. Auto-finalize if agreement is high, or create expert review if low
        """
        from .models import (
            AnnotatorAgreement,
            ExpertReviewTask,
            ExpertProfile,
            TaskAssignment,
            ConsensusQualityScore,
        )
        from .consensus_service import ConsensusService
        from tasks.models import Annotation
        from itertools import combinations

        logger.info(f"Starting consolidation for task {task.id}")

        # Update status
        consensus.status = "in_consensus"
        consensus.save(update_fields=["status"])

        # Get all completed assignments with annotations
        completed_assignments = TaskAssignment.objects.filter(
            task=task, status="completed", annotation__isnull=False
        ).select_related("annotation", "annotator", "annotator__user")

        if completed_assignments.count() < 1:
            logger.warning(f"No completed assignments found for task {task.id}")
            return

        # Single annotation - auto-finalize
        if completed_assignments.count() == 1:
            assignment = completed_assignments.first()
            consensus.status = "finalized"
            consensus.consolidated_result = assignment.annotation.result
            consensus.finalized_at = timezone.now()
            consensus.average_agreement = Decimal("100")
            consensus.consolidation_method = "single_annotator"
            consensus.save()

            # Give full quality score to single annotator
            ConsensusService._create_quality_score(
                consensus,
                assignment,
                Decimal("100"),
                Decimal("100"),
            )
            logger.info(f"Task {task.id} auto-finalized with single annotation")
            return

        # Multiple annotations - run full consolidation
        try:
            # Prepare annotation data
            annotations = []
            for assignment in completed_assignments:
                if assignment.annotation and assignment.annotation.result:
                    annotations.append(
                        {
                            "assignment": assignment,
                            "result": assignment.annotation.result,
                        }
                    )

            if len(annotations) < 2:
                logger.warning(f"Not enough valid annotations for task {task.id}")
                return

            # Detect annotation type
            annotation_type = ConsensusService.detect_annotation_type(
                annotations[0]["result"]
            )
            strategy = ConsensusService.get_strategy(annotation_type)

            logger.info(
                f"Task {task.id}: Detected annotation type '{annotation_type}', using strategy '{strategy.__name__}'"
            )

            # ================================================================
            # STEP 1: Calculate pairwise agreement scores
            # ================================================================
            agreement_scores = []
            for ann1, ann2 in combinations(annotations, 2):
                agreement = strategy.calculate_agreement(ann1["result"], ann2["result"])

                # Store pairwise agreement record
                # Note: Field constraints - agreement_score (max_digits=5, decimal_places=2)
                # Other scores (max_digits=5, decimal_places=4) - can only hold -9.9999 to 9.9999
                # Need to convert percentages (0-100) to fractions (0-1) for fields with 4 decimal places

                try:
                    agreement_score_val = float(agreement["overall"])
                    agreement_score_rounded = Decimal(
                        str(agreement_score_val)
                    ).quantize(Decimal("0.01"))

                    # Convert percentage values (0-100) to fractions (0-1) for decimal fields
                    # that can't hold values > 9.9999
                    iou_val = agreement.get("iou")
                    iou_score = (
                        Decimal(str(float(iou_val))).quantize(Decimal("0.0001"))
                        if iou_val is not None
                        else None
                    )

                    label_val = agreement.get("label")
                    # label is in percentage (0-100), convert to fraction (0-1)
                    label_agreement = (
                        Decimal(str(float(label_val) / 100.0)).quantize(
                            Decimal("0.0001")
                        )
                        if label_val is not None
                        else None
                    )

                    position_val = agreement.get("position")
                    # position is in percentage (0-100), convert to fraction (0-1)
                    position_agreement = (
                        Decimal(str(float(position_val) / 100.0)).quantize(
                            Decimal("0.0001")
                        )
                        if position_val is not None
                        else None
                    )

                    logger.debug(
                        f"Task {task.id}: Agreement={agreement_score_rounded}, "
                        f"IOU={iou_score}, Label={label_agreement}, Position={position_agreement}"
                    )

                    AnnotatorAgreement.objects.update_or_create(
                        task_consensus=consensus,
                        annotator_1=ann1["assignment"].annotator,
                        annotator_2=ann2["assignment"].annotator,
                        defaults={
                            "assignment_1": ann1["assignment"],
                            "assignment_2": ann2["assignment"],
                            "agreement_score": agreement_score_rounded,
                            "iou_score": iou_score,
                            "label_agreement": label_agreement,
                            "position_agreement": position_agreement,
                            "annotation_type": annotation_type,
                            "comparison_details": agreement,
                        },
                    )
                except Exception as e:
                    logger.error(
                        f"Error creating AnnotatorAgreement: {e}\n"
                        f"Values: overall={agreement.get('overall')}, iou={agreement.get('iou')}, "
                        f"label={agreement.get('label')}, position={agreement.get('position')}"
                    )
                    raise

                agreement_scores.append(agreement["overall"])
                logger.info(
                    f"Task {task.id}: Agreement between {ann1['assignment'].annotator.user.email} "
                    f"and {ann2['assignment'].annotator.user.email}: {agreement['overall']:.2f}%"
                )

            # Calculate overall agreement metrics
            avg_agreement = (
                sum(agreement_scores) / len(agreement_scores) if agreement_scores else 0
            )
            min_agreement = min(agreement_scores) if agreement_scores else 0
            max_agreement = max(agreement_scores) if agreement_scores else 0

            consensus.average_agreement = Decimal(str(avg_agreement))
            consensus.min_agreement = Decimal(str(min_agreement))
            consensus.max_agreement = Decimal(str(max_agreement))

            logger.info(
                f"Task {task.id}: Overall agreement - Avg: {avg_agreement:.2f}%, "
                f"Min: {min_agreement:.2f}%, Max: {max_agreement:.2f}%"
            )

            # ================================================================
            # STEP 2: Consolidate annotations
            # ================================================================
            results = [ann["result"] for ann in annotations]
            consolidated, confidence = strategy.consolidate(results)

            consensus.consolidated_result = consolidated
            consensus.consolidation_method = strategy.__name__

            logger.info(
                f"Task {task.id}: Consolidated using '{strategy.__name__}' with confidence {confidence:.2f}"
            )

            # ================================================================
            # STEP 3: Calculate individual annotator quality scores
            # ================================================================
            for ann in annotations:
                # Compare individual annotation to consolidated result
                individual_agreement = strategy.calculate_agreement(
                    ann["result"], consolidated
                )
                quality_score = Decimal(str(individual_agreement["overall"]))

                # Calculate average peer agreement (agreement with other annotators)
                peer_agreements = []
                for other in annotations:
                    if other["assignment"].id != ann["assignment"].id:
                        peer_agreement = strategy.calculate_agreement(
                            ann["result"], other["result"]
                        )
                        peer_agreements.append(peer_agreement["overall"])

                avg_peer = (
                    Decimal(str(sum(peer_agreements) / len(peer_agreements)))
                    if peer_agreements
                    else Decimal("0")
                )

                # Create quality score record
                ConsensusService._create_quality_score(
                    consensus,
                    ann["assignment"],
                    quality_score,
                    avg_peer,
                    individual_agreement,
                )

                logger.info(
                    f"Task {task.id}: Annotator {ann['assignment'].annotator.user.email} - "
                    f"Quality: {quality_score:.2f}%, Peer Agreement: {avg_peer:.2f}%"
                )

            # ================================================================
            # STEP 4: Determine consensus status and next action
            # ================================================================
            avg_agreement_decimal = Decimal(str(avg_agreement))

            if avg_agreement_decimal >= DISAGREEMENT_THRESHOLD:
                # Good agreement - consensus reached
                consensus.status = "consensus_reached"
                consensus.consensus_reached_at = timezone.now()

                logger.info(
                    f"Task {task.id}: Consensus reached with {avg_agreement:.2f}% agreement"
                )

                # Check if random sampling for quality assurance
                import random

                if random.random() < RANDOM_SAMPLE_RATE:
                    consensus.status = "review_required"
                    AnnotationWorkflowService._create_expert_review(
                        task, consensus, "random_sample", avg_agreement_decimal
                    )
                    logger.info(
                        f"Task {task.id}: Selected for random quality review (5% sample)"
                    )
                else:
                    # Auto-finalize - agreement is high enough
                    consensus.status = "finalized"
                    consensus.finalized_at = timezone.now()

                    # Create ground truth annotation from consolidated result
                    # This makes it visible to clients
                    AnnotationWorkflowService._create_ground_truth_annotation(
                        task, consensus, consolidated
                    )

                    logger.info(
                        f"Task {task.id}: Auto-finalized with high agreement ({avg_agreement:.2f}%), "
                        f"ground truth annotation created, visible to client"
                    )
            else:
                # High disagreement - needs expert review
                consensus.status = "review_required"
                AnnotationWorkflowService._create_expert_review(
                    task, consensus, "disagreement", avg_agreement_decimal
                )
                logger.info(
                    f"Task {task.id}: Disagreement detected ({avg_agreement:.2f}%), sent to expert review"
                )

            consensus.save()

        except Exception as e:
            logger.error(
                f"Error in consolidation for task {task.id}: {e}", exc_info=True
            )
            consensus.status = "review_required"
            consensus.save()
            # Create review task for manual handling
            AnnotationWorkflowService._create_expert_review(
                task, consensus, "error", Decimal("0")
            )

    @staticmethod
    def _create_expert_review(task, consensus, reason, disagreement_score):
        """Create an expert review task"""
        from .models import ExpertReviewTask, ExpertProfile, ExpertProjectAssignment

        project = task.project

        # Find an available expert for this project
        expert_assignment = (
            ExpertProjectAssignment.objects.filter(project=project, is_active=True)
            .select_related("expert")
            .first()
        )

        if not expert_assignment:
            # No expert assigned - find any active expert
            expert = (
                ExpertProfile.objects.filter(status="active")
                .order_by("current_workload")
                .first()
            )

            if not expert:
                logger.warning(f"No expert available for task {task.id} review")
                return None
        else:
            expert = expert_assignment.expert

        # Check if review task already exists
        existing = ExpertReviewTask.objects.filter(task=task, expert=expert).first()

        if existing:
            return existing

        # Create review task
        review_task = ExpertReviewTask.objects.create(
            expert=expert,
            task=task,
            task_consensus=consensus,
            project_assignment=expert_assignment,
            status="pending",
            assignment_reason=reason,
            disagreement_score=disagreement_score,
        )

        logger.info(
            f"Created expert review task {review_task.id} for task {task.id} ({reason})"
        )
        return review_task

    @staticmethod
    def _create_ground_truth_annotation(task, consensus, consolidated_result):
        """
        Create a ground truth annotation from the consolidated result.

        This is called when auto-finalizing tasks with high agreement.
        The ground truth annotation is what clients will see as the final result.
        """
        from tasks.models import Annotation

        # First, mark any existing annotations as not ground truth
        Annotation.objects.filter(task=task).update(ground_truth=False)

        # Get the user who created the first annotation to attribute the ground truth
        # (In auto-finalization, there's no expert, so we use the first annotator
        # or the project owner as the creator)
        first_annotation = Annotation.objects.filter(
            task=task, was_cancelled=False
        ).first()

        # If no existing annotations or no user, use project owner
        if first_annotation and first_annotation.completed_by:
            attributed_to = first_annotation.completed_by
        else:
            attributed_to = task.project.created_by

        # Create the ground truth annotation
        ground_truth_annotation = Annotation.objects.create(
            task=task,
            completed_by=attributed_to,
            result=consolidated_result,
            was_cancelled=False,
            ground_truth=True,  # This makes it visible to clients
            project=task.project,
        )

        logger.info(
            f"📝 Created ground truth annotation {ground_truth_annotation.id} "
            f"from auto-consolidated result for task {task.id} "
            f"(agreement: {consensus.average_agreement}%)"
        )

        return ground_truth_annotation

    @staticmethod
    def get_task_status_for_client(task):
        """
        Get the annotation status for a task from client perspective.

        Returns dict with:
        - status: pending, in_progress, reviewing, complete
        - can_view_annotations: bool
        - annotation_count: int
        - review_status: str or None
        """
        from .models import TaskConsensus, TaskAssignment

        project = task.project
        required_overlap = getattr(project, "required_overlap", 1)

        # Get assignment info
        assignments = TaskAssignment.objects.filter(task=task)
        total_assigned = assignments.count()
        completed = assignments.filter(status="completed").count()

        result = {
            "task_id": task.id,
            "required_annotations": required_overlap,
            "completed_annotations": completed,
            "can_view_annotations": False,
            "can_view_annotators": False,
            "status": "pending",
            "review_status": None,
        }

        if required_overlap <= 1:
            # No consensus needed
            result["can_view_annotations"] = completed > 0
            result["can_view_annotators"] = completed > 0
            result["status"] = "complete" if completed > 0 else "pending"
            return result

        # Check consensus status
        try:
            consensus = task.consensus
            result["review_status"] = consensus.status

            if consensus.status == "finalized":
                result["can_view_annotations"] = True
                result["can_view_annotators"] = True
                result["status"] = "complete"
            elif consensus.status in ["review_required", "conflict"]:
                result["status"] = "reviewing"
            elif consensus.status == "consensus_reached":
                result["status"] = "reviewing"
            elif completed >= required_overlap:
                result["status"] = "consolidating"
            elif completed > 0:
                result["status"] = "in_progress"
            else:
                result["status"] = "pending"

        except TaskConsensus.DoesNotExist:
            if completed >= required_overlap:
                result["status"] = "in_progress"
            elif completed > 0:
                result["status"] = "in_progress"

        return result

    @staticmethod
    @transaction.atomic
    def finalize_after_expert_review(review_task, corrected_result=None):
        """
        Finalize a task after expert review is complete.

        Args:
            review_task: ExpertReviewTask instance
            corrected_result: Optional corrected annotation result
        """
        consensus = review_task.task_consensus

        if corrected_result:
            consensus.consolidated_result = corrected_result

        consensus.status = "finalized"
        consensus.finalized_at = timezone.now()
        consensus.reviewed_by = review_task.expert.user
        consensus.save()

        review_task.status = "approved" if not corrected_result else "corrected"
        review_task.completed_at = timezone.now()
        review_task.save()

        logger.info(f"Task {review_task.task_id} finalized after expert review")





