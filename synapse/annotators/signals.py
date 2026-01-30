"""
Signal handlers for automatic task assignment in the annotators app.

These signals trigger automatic assignment when:
1. Tasks are created/imported into a project (auto-publishes and assigns)
2. Project is saved with tasks (checks if assignment needed)
3. NEW: When annotators are added to a project (reassign incomplete tasks)
4. NEW: When annotator completes a task (trigger reassignment if capacity available)

The workflow is fully automatic with FIXED OVERLAP=3:
- Client creates project → adds tasks → system auto-assigns to annotators
- No manual "publish" step required
- Always uses 3 annotators per task
"""

import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Count

logger = logging.getLogger(__name__)

# Force logging to console for debugging
import sys

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


def auto_assign_on_project_update(sender, instance, created, **kwargs):
    """
    Signal handler triggered when a Project is saved.

    Triggers automatic assignment when:
    - Project has tasks (regardless of is_published status)
    - Auto-assignment is enabled for the project
    - Project doesn't already have assignments

    This enables fully automatic workflow where client just creates
    project and adds tasks - no manual publish required.
    """
    # Debug: confirm signal is firing
    print(
        f"[SIGNAL DEBUG] auto_assign_on_project_update fired for project {instance.id}"
    )
    logger.info(
        f"[SIGNAL] Project update signal fired: project_id={instance.id}, created={created}"
    )

    from annotators.assignment_engine import AssignmentEngine

    project = instance

    # Check if project has tasks
    task_count = project.tasks.count()
    if task_count == 0:
        logger.debug(f"Project {project.id} has no tasks, skipping auto-assignment")
        return

    # Check if auto-assignment is enabled (default True if attribute doesn't exist)
    auto_assign_enabled = getattr(project, "auto_assign_enabled", True)
    if not auto_assign_enabled:
        logger.debug(f"Auto-assignment disabled for project {project.id}")
        return

    try:
        # Check if project already has assignments
        from annotators.models import ProjectAssignment

        existing_assignments = ProjectAssignment.objects.filter(
            project=project, active=True
        ).count()

        if existing_assignments > 0:
            logger.debug(
                f"Project {project.id} already has {existing_assignments} assignments"
            )
            return

        logger.info(
            f"🚀 Auto-triggering assignment for project {project.id} ({project.title}) with {task_count} tasks"
        )

        # Auto-publish the project so annotators can see it
        if not project.is_published:
            project.is_published = True
            # Use update to avoid triggering signal again
            sender.objects.filter(pk=project.pk).update(is_published=True)
            logger.info(f"Auto-published project {project.id}")

        # Trigger assignment
        result = AssignmentEngine.assign_annotators_to_project(project)

        if result:
            logger.info(
                f"✅ Auto-assignment completed for project {project.id}: {len(result)} annotators assigned"
            )
        else:
            logger.warning(
                f"Auto-assignment returned no results for project {project.id}"
            )

    except Exception as e:
        logger.error(
            f"Error in auto-assignment for project {project.id}: {e}", exc_info=True
        )


def auto_assign_on_task_created(sender, instance, created, **kwargs):
    """
    Signal handler triggered when a Task is saved.

    This is the MAIN trigger for auto-assignment:
    - When tasks are added to a project, trigger assignment
    - Auto-publish the project
    - Assign annotators if not already assigned
    - Distribute the task to available annotators based on overlap
    """
    # Debug: confirm signal is firing
    print(
        f"[SIGNAL DEBUG] auto_assign_on_task_created fired: task_id={instance.id}, created={created}"
    )
    logger.info(
        f"[SIGNAL] Task created signal fired: task_id={instance.id}, created={created}"
    )

    from annotators.assignment_engine import AssignmentEngine

    # Only handle newly created tasks
    if not created:
        return

    task = instance
    project = task.project

    if not project:
        return

    try:
        from annotators.models import ProjectAssignment, TaskAssignment

        # Check if project has active assignments
        active_assignments = ProjectAssignment.objects.filter(
            project=project, active=True
        ).select_related("annotator")

        # If no assignments yet, trigger project-level assignment first
        if not active_assignments.exists():
            logger.info(
                f"📋 New task {task.id} in project {project.id} - triggering auto-assignment"
            )

            # Auto-publish the project
            if not project.is_published:
                project.is_published = True
                project.save(update_fields=["is_published"])
                logger.info(f"Auto-published project {project.id}")

            # Assign annotators to the project
            AssignmentEngine.assign_annotators_to_project(project)

            # Re-check for assignments (could be newly created or existing from get_or_create)
            active_assignments = ProjectAssignment.objects.filter(
                project=project, active=True
            ).select_related("annotator")

            if active_assignments.exists():
                logger.info(
                    f"✅ Project {project.id} now has {active_assignments.count()} annotators assigned"
                )
            else:
                logger.warning(f"No annotators available for project {project.id}")
                return

        # Calculate required overlap based on number of annotators
        from annotators.adaptive_assignment_engine import AdaptiveAssignmentEngine

        required_overlap, total_annotators, _ = (
            AdaptiveAssignmentEngine.calculate_optimal_overlap(project)
        )

        logger.debug(
            f"Task {task.id}: Need {required_overlap} annotators (based on {total_annotators} total)"
        )

        # Get existing assignments for this task
        existing_assignments = set(
            TaskAssignment.objects.filter(task=task).values_list(
                "annotator_id", flat=True
            )
        )

        needed = required_overlap - len(existing_assignments)
        if needed <= 0:
            logger.debug(
                f"Task {task.id} already has {len(existing_assignments)} assignments"
            )
            return

        # Assign task to available annotators up to the required overlap
        assigned_count = 0
        for assignment in active_assignments:
            if assigned_count >= needed:
                break

            annotator = assignment.annotator

            # Check if already assigned to this annotator
            if annotator.id in existing_assignments:
                continue

            # Assign task to this annotator (no capacity check for fair overlap distribution)
            TaskAssignment.objects.create(
                annotator=annotator,
                task=task,
                status="assigned",
                amount_paid=0,  # Will be calculated on completion
            )
            logger.info(
                f"✅ Task {task.id} assigned to annotator {annotator.user.email} "
                f"({assigned_count + 1}/{required_overlap})"
            )
            assigned_count += 1
            existing_assignments.add(annotator.id)

        if assigned_count < needed:
            logger.warning(
                f"⚠️ Task {task.id}: Only {assigned_count}/{required_overlap} annotators assigned "
                f"(need more annotators)"
            )

    except Exception as e:
        logger.error(f"Error distributing task {task.id}: {e}", exc_info=True)


def auto_assign_on_tasks_imported(project_id):
    """
    Triggered after bulk task import (which bypasses post_save signals).

    This is called from:
    - data_import/api.py (sync import)
    - data_import/functions.py (async import)

    Args:
        project_id: ID of the project that received new tasks
    """
    from annotators.assignment_engine import AssignmentEngine
    from annotators.models import ProjectAssignment, TaskAssignment
    from projects.models import Project

    try:
        project = Project.objects.get(id=project_id)
        print(f"[SIGNAL DEBUG] auto_assign_on_tasks_imported for project {project_id}")
        logger.info(
            f"[SIGNAL] Processing auto-assignment for project {project_id} after bulk import"
        )

        # First ensure project has annotators assigned
        if not ProjectAssignment.objects.filter(project=project, active=True).exists():
            logger.info(
                f"No active assignments for project {project_id}, triggering assignment..."
            )
            AssignmentEngine.assign_annotators_to_project(project)

        # Get active assignments
        active_assignments = list(
            ProjectAssignment.objects.filter(
                project=project, active=True
            ).select_related("annotator")
        )

        if not active_assignments:
            logger.warning(f"No annotators available for project {project_id}")
            return

        # Calculate optimal overlap based on number of annotators
        from annotators.adaptive_assignment_engine import AdaptiveAssignmentEngine

        required_overlap, total_annotators, _ = (
            AdaptiveAssignmentEngine.calculate_optimal_overlap(project)
        )

        logger.info(
            f"📊 Project {project_id}: {total_annotators} annotators, overlap={required_overlap}"
        )

        # Get tasks that need more assignments
        from django.db.models import Count, Q

        tasks_needing_assignment = (
            project.tasks.annotate(
                current_assignments=Count(
                    "annotator_assignments",
                    filter=Q(
                        annotator_assignments__status__in=[
                            "assigned",
                            "in_progress",
                            "completed",
                        ]
                    ),
                )
            )
            .filter(current_assignments__lt=required_overlap)
            .order_by("id")
        )

        if not tasks_needing_assignment.exists():
            logger.info(f"All tasks already fully assigned for project {project_id}")
            return

        tasks_assigned = 0
        annotators = [pa.annotator for pa in active_assignments]

        # For each task, assign up to required_overlap annotators
        for task in tasks_needing_assignment:
            # Get existing assignments for this task
            existing_annotator_ids = set(
                TaskAssignment.objects.filter(task=task).values_list(
                    "annotator_id", flat=True
                )
            )

            needed = required_overlap - len(existing_annotator_ids)

            if needed <= 0:
                continue

            # Assign annotators who haven't been assigned yet
            assigned_for_task = 0
            for annotator in annotators:
                if annotator.id in existing_annotator_ids:
                    continue  # Already assigned

                if assigned_for_task >= needed:
                    break  # Task has enough assignments

                TaskAssignment.objects.create(
                    annotator=annotator,
                    task=task,
                    status="assigned",
                    amount_paid=0,
                )
                tasks_assigned += 1
                assigned_for_task += 1
                existing_annotator_ids.add(annotator.id)

        logger.info(
            f"✅ Auto-assigned {tasks_assigned} task-annotator pairs for project {project_id} "
            f"(overlap={required_overlap})"
        )

    except Project.DoesNotExist:
        logger.error(f"Project {project_id} not found")
    except Exception as e:
        logger.error(
            f"Error in auto_assign_on_tasks_imported for project {project_id}: {e}",
            exc_info=True,
        )


# ====================================================================================
# NEW SIGNALS FOR ENHANCED ASSIGNMENT WITH FIXED OVERLAP=3
# ====================================================================================


@receiver(
    post_save,
    sender="annotators.ProjectAssignment",
    dispatch_uid="auto_reassign_on_new_annotator_unique",
)
def auto_reassign_on_new_annotator(sender, instance, created, **kwargs):
    """
    Automatically reassign incomplete tasks when a new annotator is added to a project.

    This ensures that tasks waiting for more annotators (< 3) get automatically
    assigned when new annotators become available.
    """
    if not created or not instance.active:
        return  # Only trigger on new active assignments

    project = instance.project
    annotator = instance.annotator

    logger.info(
        f"🆕 New annotator {annotator.user.email} added to project {project.id}, "
        f"checking for incomplete tasks..."
    )

    # Queue reassignment job
    from annotators.tasks import reassign_incomplete_tasks_job

    try:
        reassign_incomplete_tasks_job.delay(project.id)
        logger.info(f"📋 Queued reassignment job for project {project.id}")
    except Exception as e:
        logger.error(f"Error queuing reassignment job: {e}")
        # Run synchronously as fallback
        try:
            from annotators.enhanced_assignment_engine import EnhancedAssignmentEngine

            EnhancedAssignmentEngine.reassign_incomplete_tasks(project)
        except Exception as e2:
            logger.error(f"Fallback reassignment also failed: {e2}")


# Track which assignments have been processed to avoid duplicate triggers
_processed_completions = set()


@receiver(
    post_save,
    sender="annotators.TaskAssignment",
    dispatch_uid="check_reassignment_unique",
)
def check_reassignment_on_task_completion(sender, instance, created, **kwargs):
    """
    Check for reassignment opportunities when a task is completed.

    When an annotator completes a task, they have capacity freed up.
    Check if there are incomplete tasks that need assignment.
    """
    global _processed_completions

    # Only trigger when status is completed
    if instance.status != "completed":
        return

    # Only trigger if this is a status CHANGE to completed (check update_fields)
    update_fields = kwargs.get("update_fields")
    if update_fields is not None and "status" not in update_fields:
        return  # Status wasn't changed in this save

    # Prevent duplicate processing for the same assignment in the same request
    assignment_key = f"{instance.id}_{instance.status}"
    if assignment_key in _processed_completions:
        return
    _processed_completions.add(assignment_key)

    # Clean up old entries (keep set from growing indefinitely)
    if len(_processed_completions) > 1000:
        _processed_completions = set()

    annotator = instance.annotator
    project = instance.task.project

    # Check if there are incomplete tasks
    from tasks.models import Task

    incomplete_count = (
        Task.objects.filter(project=project)
        .annotate(actual_assignments=Count("annotator_assignments"))
        .filter(actual_assignments__lt=3)  # Hard-coded overlap=3
        .count()
    )

    if incomplete_count == 0:
        logger.debug(
            f"All tasks in project {project.id} fully assigned, no reassignment needed"
        )
        return

    logger.info(
        f"📝 Annotator {annotator.user.email} completed task, {incomplete_count} incomplete tasks remain, "
        f"triggering reassignment check..."
    )

    # Queue reassignment (async to avoid blocking)
    # Skip if Redis is not available or not configured
    try:
        from annotators.tasks import reassign_incomplete_tasks_job

        reassign_incomplete_tasks_job.delay(project.id)
        logger.debug(f"✅ Queued reassignment job for project {project.id}")
    except Exception as e:
        # Redis not available or not configured - skip background task
        # This is non-critical, reassignment will happen on next manual trigger
        logger.debug(
            f"⚠️  Could not queue background reassignment (Redis unavailable): {e}"
        )
        # Don't block the request - continue without background task
        pass


# NEW: Check for consolidation when annotation is saved
@receiver(
    post_save, sender="tasks.Annotation", dispatch_uid="check_consolidation_unique"
)
def check_consolidation_on_annotation_save(sender, instance, created, **kwargs):
    """
    When an annotation is created or updated, check if task is ready for consolidation.

    This uses the adaptive overlap system - consolidation triggers when:
    - Task has reached the required number of annotations based on available annotators
    - 2 annotators → need 2 annotations
    - 3+ annotators → need 3 annotations
    """
    if not created or instance.was_cancelled:
        return

    task = instance.task
    project = task.project

    # Count non-cancelled annotations for this task
    from tasks.models import Annotation

    annotation_count = Annotation.objects.filter(task=task, was_cancelled=False).count()

    # Get adaptive required overlap
    from annotators.adaptive_assignment_engine import AdaptiveAssignmentEngine

    try:
        required_overlap, _, _ = AdaptiveAssignmentEngine.calculate_optimal_overlap(
            project
        )
    except Exception as e:
        logger.error(f"Error calculating overlap: {e}")
        return

    logger.info(
        f"📊 Task {task.id}: {annotation_count}/{required_overlap} annotations "
        f"(Project {project.id} has adaptive overlap={required_overlap})"
    )

    # Check if ready for consolidation
    if annotation_count >= required_overlap:
        logger.info(
            f"🔔 Task {task.id} ready for consolidation with {annotation_count} annotations!"
        )

        # Check if already has consensus
        from annotators.models import TaskConsensus

        try:
            consensus = TaskConsensus.objects.get(task=task)

            # Check if consolidation already completed
            if consensus.status in [
                "review_required",
                "consensus_reached",
                "finalized",
            ]:
                logger.info(
                    f"✅ Task {task.id} already consolidated (status={consensus.status})"
                )
                return

            # Consolidation started but not completed - update and retry
            logger.info(
                f"⚠️  Task {task.id} has consensus but status={consensus.status}, retriggering..."
            )
            consensus.required_annotations = required_overlap
            consensus.current_annotations = annotation_count
            consensus.status = "in_consensus"
            consensus.save()

        except TaskConsensus.DoesNotExist:
            # Create new consensus object
            consensus = TaskConsensus.objects.create(
                task=task,
                required_annotations=required_overlap,
                current_annotations=annotation_count,
                status="pending",
            )
            logger.info(f"📝 Created new consensus record for Task {task.id}")

        # Trigger consolidation directly (not through background job to avoid Redis auth issues)
        try:
            from annotators.annotation_workflow import AnnotationWorkflowService

            logger.info(f"🚀 Triggering consolidation for Task {task.id}...")
            AnnotationWorkflowService.trigger_consolidation(task, consensus)
            logger.info(f"✅ Consolidation completed for Task {task.id}")

        except Exception as e:
            logger.error(
                f"❌ Error triggering consolidation for Task {task.id}: {e}",
                exc_info=True,
            )
    else:
        remaining = required_overlap - annotation_count
        logger.info(
            f"⏳ Task {task.id} needs {remaining} more annotation(s) before consolidation"
        )


@receiver(
    post_save,
    sender="annotators.ExpertReviewTask",
    dispatch_uid="ensure_expert_assignment_unique",
)
def ensure_expert_project_assignment(sender, instance, created, **kwargs):
    """
    Ensure ExpertProjectAssignment exists when ExpertReviewTask is created.

    This allows experts to see the project in /api/projects endpoint.
    """
    if not created:
        return

    try:
        from .models import ExpertProjectAssignment

        expert = instance.expert
        project = instance.task.project

        # Check if assignment already exists
        assignment, was_created = ExpertProjectAssignment.objects.get_or_create(
            expert=expert,
            project=project,
            defaults={
                "is_active": True,
                "review_all_tasks": False,
                "sample_rate": 100,
                "priority": 10,
            },
        )

        if was_created:
            logger.info(
                f"✅ Created ExpertProjectAssignment for {expert.user.email} "
                f"on project {project.title} (ID: {project.id})"
            )
        else:
            logger.debug(
                f"ℹ️  ExpertProjectAssignment already exists for {expert.user.email} "
                f"on project {project.title}"
            )

    except Exception as e:
        logger.error(
            f"❌ Error creating ExpertProjectAssignment: {e}",
            exc_info=True,
        )






@receiver(
    post_save,
    sender="annotators.TaskAssignment",
    dispatch_uid="ensure_annotator_not_in_organization_unique",
)
def ensure_annotator_not_in_organization(sender, instance, created, **kwargs):
    """
    Safeguard: Ensure annotators are NOT members of the client organization.

    When a task is assigned, check if the annotator is an organization member.
    If so, remove them. This prevents annotators from gaining implicit organization access.
    """
    if not created:
        return

    try:
        from organizations.models import OrganizationMember

        annotator = instance.annotator
        user = annotator.user
        project = instance.task.project
        # We need to handle cases where project might be None (though unlikely for a Task)
        if not project or not project.organization:
            return

        organization = project.organization

        # Check if user is a member of this organization
        # We use filter().delete() for efficiency and to avoid exceptions if not found
        deleted_count, _ = OrganizationMember.objects.filter(
            user=user, organization=organization
        ).delete()

        if deleted_count > 0:
            logger.info(
                f"🛡️ Safeguard: Removed annotator {user.email} from organization {organization.title} "
                f"after task assignment (Project: {project.id})"
            )

    except Exception as e:
        logger.error(
            f"Error in ensure_annotator_not_in_organization: {e}", exc_info=True
        )
