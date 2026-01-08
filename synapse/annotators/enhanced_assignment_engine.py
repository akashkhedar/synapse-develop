"""
Enhanced Assignment Engine with Hard-Coded Overlap=3

This module implements the improved task assignment system with:
1. Hard-coded overlap = 3 (always 3 annotators per task)
2. Smart rotating distribution when annotators > 3
3. Capacity-aware assignment that skips full annotators
4. Partial assignment holding for incomplete tasks
5. Auto-reassignment when new annotators become available
6. Consolidation trigger when task reaches 3 annotations
"""

from django.db import transaction, models
from django.db.models import Q, Count, Avg, F, Case, When, Value, FloatField
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import logging

from projects.models import Project, ProjectMember
from .models import (
    AnnotatorProfile,
    ProjectAssignment,
    TaskAssignment,
    TrustLevel,
    TaskConsensus,
)

logger = logging.getLogger(__name__)

# CONSTANTS
REQUIRED_OVERLAP = 3  # Hard-coded: Always 3 annotators per task
MAX_ASSIGNMENT_ATTEMPTS = 100  # Prevent infinite loops
MAX_TASKS_IN_PROGRESS = getattr(settings, "ANNOTATOR_MAX_ACTIVE_TASKS", 10)

# Capacity limits based on trust level
CAPACITY_LIMITS = {
    "new": 50,
    "junior": 100,
    "regular": 150,
    "senior": 200,
    "expert": 300,
}


class EnhancedAssignmentEngine:
    """
    Enhanced assignment engine with hard-coded overlap=3 and smart distribution.

    This replaces the standard assignment engine with improved logic.
    """

    @staticmethod
    def auto_assign_project_tasks(project):
        """
        Main entry point for auto-assigning tasks when project is published or tasks are imported.

        Steps:
        1. Assign annotators to project (using scoring)
        2. Distribute tasks with REQUIRED_OVERLAP=3 (hard-coded)
        3. Handle partial assignments
        4. Return detailed stats
        """
        logger.info(f"🚀 Starting enhanced auto-assignment for project {project.id}")

        # Step 1: Get or assign annotators to project
        from .assignment_engine import AssignmentEngine

        project_assignments = ProjectAssignment.objects.filter(
            project=project, active=True
        ).select_related("annotator", "annotator__user", "annotator__trust_level")

        if not project_assignments.exists():
            # No annotators assigned yet, use intelligent scoring
            logger.info("No annotators assigned, triggering intelligent assignment...")
            project_assignments = AssignmentEngine.assign_annotators_to_project(
                project, required_overlap=REQUIRED_OVERLAP
            )

        annotators = [pa.annotator for pa in project_assignments]

        if not annotators:
            logger.error(f"❌ No annotators available for project {project.id}")
            return {
                "success": False,
                "error": "No annotators available",
            }

        logger.info(f"📋 {len(annotators)} annotators available for assignment")

        # Step 2: Distribute tasks with hard-coded overlap=3
        result = EnhancedAssignmentEngine.distribute_tasks_with_fixed_overlap(
            project, annotators
        )

        logger.info(f"✅ Auto-assignment complete for project {project.id}")
        return result

    @staticmethod
    def distribute_tasks_with_fixed_overlap(project, annotators):
        """
        Distribute ALL tasks to annotators with FIXED OVERLAP = 3.

        Strategy:
        1. ALWAYS use overlap = 3 (hard-coded, cannot be changed)
        2. If annotators < 3: Assign ALL tasks to ALL available annotators (partial mode)
        3. If annotators >= 3: Use rotating distribution with capacity awareness
        4. Skip annotators at capacity, hold incomplete tasks
        5. Trigger consolidation when task reaches 3 annotations

        Returns:
            dict with detailed statistics
        """
        num_annotators = len(annotators)
        logger.info(
            f"🎯 FIXED OVERLAP = {REQUIRED_OVERLAP} (hard-coded, always 3 annotators per task)"
        )
        logger.info(
            f"📊 Distributing tasks for project {project.id}: {num_annotators} annotators available"
        )

        if num_annotators == 0:
            return {
                "success": False,
                "error": "No annotators available",
                "assigned_tasks": 0,
                "total_assignments": 0,
                "tasks_fully_assigned": 0,
                "tasks_partially_assigned": 0,
                "tasks_waiting": 0,
            }

        # Get all tasks
        all_tasks = list(project.tasks.order_by("id"))

        if not all_tasks:
            logger.info("No tasks found in project")
            return {
                "success": True,
                "assigned_tasks": 0,
                "total_assignments": 0,
                "tasks_fully_assigned": 0,
                "tasks_partially_assigned": 0,
                "tasks_waiting": 0,
            }

        logger.info(f"📦 Found {len(all_tasks)} tasks to assign")

        # Set target assignment count = 3 for ALL tasks
        from tasks.models import Task

        Task.objects.filter(project=project).update(
            target_assignment_count=REQUIRED_OVERLAP
        )

        # Pre-calculate annotator capacities
        annotator_capacities = {}
        for annotator in annotators:
            capacity_info = EnhancedAssignmentEngine._check_capacity(annotator)
            annotator_capacities[annotator.id] = {
                "annotator": annotator,
                "current": capacity_info["current"],
                "maximum": capacity_info["maximum"],
                "available": capacity_info["available"],
            }
            logger.debug(
                f"👤 {annotator.user.email}: {capacity_info['current']}/{capacity_info['maximum']} capacity"
            )

        # Initialize counters
        total_assignments = 0
        tasks_fully_assigned = 0
        tasks_partially_assigned = 0
        tasks_waiting = 0
        annotators_used = set()

        if num_annotators < REQUIRED_OVERLAP:
            # PARTIAL ASSIGNMENT MODE: Not enough annotators
            logger.warning(
                f"⚠️ PARTIAL ASSIGNMENT MODE: Only {num_annotators} annotators, need {REQUIRED_OVERLAP}. "
                f"Assigning ALL tasks to ALL available annotators."
            )

            result = EnhancedAssignmentEngine._assign_all_to_all(
                project, all_tasks, annotators, annotator_capacities
            )

            return result

        else:
            # ROTATING ASSIGNMENT MODE: Enough annotators for full coverage
            logger.info(
                f"🔄 ROTATING ASSIGNMENT MODE: {num_annotators} annotators, overlap={REQUIRED_OVERLAP}"
            )

            result = EnhancedAssignmentEngine._assign_with_rotation(
                project, all_tasks, annotators, annotator_capacities
            )

            return result

    @staticmethod
    def _assign_all_to_all(project, all_tasks, annotators, annotator_capacities):
        """
        Assign ALL tasks to ALL available annotators (when annotators < 3).
        Example: 50 tasks, 2 annotators → Each annotator gets all 50 tasks.
        """
        total_assignments = 0
        tasks_fully_assigned = 0
        tasks_partially_assigned = 0
        tasks_waiting = 0
        annotators_used = set()

        with transaction.atomic():
            for task in all_tasks:
                # Check existing assignments
                already_assigned = set(
                    TaskAssignment.objects.filter(task=task).values_list(
                        "annotator_id", flat=True
                    )
                )

                assigned_to_task = len(already_assigned)

                # Try to assign to ALL annotators
                for annotator in annotators:
                    if annotator.id in already_assigned:
                        continue

                    capacity = annotator_capacities[annotator.id]
                    if capacity["available"] <= 0:
                        # Refresh capacity
                        capacity_info = EnhancedAssignmentEngine._check_capacity(
                            annotator
                        )
                        capacity["available"] = capacity_info["available"]
                        if capacity["available"] <= 0:
                            continue

                    # Create assignment
                    try:
                        assignment = EnhancedAssignmentEngine._create_assignment(
                            annotator, task, project
                        )
                        if assignment:
                            total_assignments += 1
                            assigned_to_task += 1
                            annotators_used.add(annotator.id)
                            capacity["available"] -= 1
                            capacity["current"] += 1
                            already_assigned.add(annotator.id)
                    except Exception as e:
                        logger.error(f"Error assigning task {task.id}: {e}")

                # Categorize task status
                if assigned_to_task >= REQUIRED_OVERLAP:
                    tasks_fully_assigned += 1
                    EnhancedAssignmentEngine._trigger_consolidation_check(task)
                elif assigned_to_task > 0:
                    tasks_partially_assigned += 1
                else:
                    tasks_waiting += 1

        logger.info(
            f"📈 All-to-all assignment complete:\n"
            f"  - Total tasks: {len(all_tasks)}\n"
            f"  - Assignments created: {total_assignments}\n"
            f"  - Annotators used: {len(annotators_used)}\n"
            f"  - Fully assigned ({REQUIRED_OVERLAP}/{REQUIRED_OVERLAP}): {tasks_fully_assigned}\n"
            f"  - Partially assigned (<{REQUIRED_OVERLAP}): {tasks_partially_assigned}\n"
            f"  - Waiting (0): {tasks_waiting}"
        )

        incomplete = tasks_partially_assigned + tasks_waiting
        if incomplete > 0:
            logger.warning(
                f"🔔 {incomplete} tasks incomplete. Will auto-assign when more annotators available."
            )

        return {
            "success": True,
            "strategy": "all_to_all",
            "assigned_tasks": len(all_tasks),
            "total_assignments": total_assignments,
            "annotators_used": len(annotators_used),
            "tasks_fully_assigned": tasks_fully_assigned,
            "tasks_partially_assigned": tasks_partially_assigned,
            "tasks_waiting": tasks_waiting,
            "incomplete_tasks": incomplete,
        }

    @staticmethod
    def _assign_with_rotation(project, all_tasks, annotators, annotator_capacities):
        """
        Assign tasks using rotating distribution (when annotators >= 3).

        Example with 5 annotators, 50 tasks, overlap=3:
        Task 1 → A1, A2, A3
        Task 2 → A2, A3, A4
        Task 3 → A3, A4, A5
        Task 4 → A4, A5, A1
        Task 5 → A5, A1, A2
        ...and so on

        Skips annotators at capacity and holds incomplete tasks.
        """
        num_annotators = len(annotators)
        total_assignments = 0
        tasks_fully_assigned = 0
        tasks_partially_assigned = 0
        tasks_waiting = 0
        annotators_used = set()

        rotation_index = 0

        with transaction.atomic():
            for task in all_tasks:
                # Check existing assignments
                already_assigned = set(
                    TaskAssignment.objects.filter(task=task).values_list(
                        "annotator_id", flat=True
                    )
                )

                assigned_to_task = len(already_assigned)
                needed = REQUIRED_OVERLAP - assigned_to_task

                if needed <= 0:
                    tasks_fully_assigned += 1
                    continue

                # Try to assign REQUIRED_OVERLAP annotators using rotation
                attempts = 0

                while (
                    assigned_to_task < REQUIRED_OVERLAP
                    and attempts < MAX_ASSIGNMENT_ATTEMPTS
                ):
                    # Get next annotator in rotation
                    annotator = annotators[rotation_index % num_annotators]
                    rotation_index += 1
                    attempts += 1

                    # Skip if already assigned to this task
                    if annotator.id in already_assigned:
                        continue

                    # Check capacity
                    capacity = annotator_capacities[annotator.id]
                    if capacity["available"] <= 0:
                        # Try refreshing capacity
                        capacity_info = EnhancedAssignmentEngine._check_capacity(
                            annotator
                        )
                        capacity["available"] = capacity_info["available"]
                        if capacity["available"] <= 0:
                            continue  # Still at capacity, skip

                    # Create assignment
                    try:
                        assignment = EnhancedAssignmentEngine._create_assignment(
                            annotator, task, project
                        )
                        if assignment:
                            total_assignments += 1
                            assigned_to_task += 1
                            annotators_used.add(annotator.id)
                            already_assigned.add(annotator.id)
                            capacity["available"] -= 1
                            capacity["current"] += 1

                            logger.debug(
                                f"Task {task.id}: Assigned to {annotator.user.email} "
                                f"({assigned_to_task}/{REQUIRED_OVERLAP})"
                            )
                    except Exception as e:
                        logger.error(f"Error assigning task {task.id}: {e}")

                # Categorize task status
                if assigned_to_task >= REQUIRED_OVERLAP:
                    tasks_fully_assigned += 1
                    EnhancedAssignmentEngine._trigger_consolidation_check(task)
                    logger.debug(
                        f"✅ Task {task.id} FULLY assigned ({assigned_to_task}/{REQUIRED_OVERLAP})"
                    )
                elif assigned_to_task > 0:
                    tasks_partially_assigned += 1
                    logger.warning(
                        f"⚠️ Task {task.id} PARTIALLY assigned ({assigned_to_task}/{REQUIRED_OVERLAP}) - "
                        f"waiting for capacity or more annotators"
                    )
                else:
                    tasks_waiting += 1
                    logger.warning(
                        f"⏸️ Task {task.id} NOT assigned - all annotators at capacity"
                    )

        logger.info(
            f"📈 Rotating assignment complete:\n"
            f"  - Total tasks: {len(all_tasks)}\n"
            f"  - Assignments created: {total_assignments}\n"
            f"  - Annotators used: {len(annotators_used)}\n"
            f"  - Fully assigned ({REQUIRED_OVERLAP}/{REQUIRED_OVERLAP}): {tasks_fully_assigned}\n"
            f"  - Partially assigned (<{REQUIRED_OVERLAP}): {tasks_partially_assigned}\n"
            f"  - Waiting (0): {tasks_waiting}"
        )

        incomplete = tasks_partially_assigned + tasks_waiting
        if incomplete > 0:
            logger.warning(
                f"🔔 {incomplete} tasks incomplete. Will auto-assign when capacity available."
            )

        return {
            "success": True,
            "strategy": "rotating",
            "assigned_tasks": len(all_tasks),
            "total_assignments": total_assignments,
            "annotators_used": len(annotators_used),
            "tasks_fully_assigned": tasks_fully_assigned,
            "tasks_partially_assigned": tasks_partially_assigned,
            "tasks_waiting": tasks_waiting,
            "incomplete_tasks": incomplete,
        }

    @staticmethod
    def reassign_incomplete_tasks(project):
        """
        Auto-reassign tasks that don't have 3 annotators yet.

        This should be called when:
        - New annotators join the project
        - Existing annotators have capacity freed up
        - Periodically to fill gaps
        """
        logger.info(f"🔄 Checking for incomplete tasks in project {project.id}")

        # Get tasks with < 3 assignments
        from tasks.models import Task

        incomplete_tasks = (
            Task.objects.filter(project=project)
            .annotate(assignment_count_actual=Count("annotator_assignments"))
            .filter(assignment_count_actual__lt=REQUIRED_OVERLAP)
            .order_by("id")
        )

        if not incomplete_tasks.exists():
            logger.info("✅ All tasks fully assigned")
            return {"reassigned": 0, "message": "All tasks fully assigned"}

        logger.info(f"Found {incomplete_tasks.count()} incomplete tasks")

        # Get available annotators with capacity
        project_assignments = ProjectAssignment.objects.filter(
            project=project, active=True
        ).select_related("annotator", "annotator__user")

        available_annotators = []
        for pa in project_assignments:
            capacity = EnhancedAssignmentEngine._check_capacity(pa.annotator)
            if capacity["available"] > 0:
                available_annotators.append(pa.annotator)

        if not available_annotators:
            logger.warning("⚠️ No annotators with available capacity")
            return {"reassigned": 0, "message": "No annotators with capacity"}

        logger.info(f"{len(available_annotators)} annotators with capacity found")

        # Try to assign
        result = EnhancedAssignmentEngine.distribute_tasks_with_fixed_overlap(
            project, available_annotators
        )

        return {
            "reassigned": result.get("total_assignments", 0),
            "tasks_completed": result.get("tasks_fully_assigned", 0),
            "result": result,
        }

    @staticmethod
    def _create_assignment(annotator, task, project):
        """Create a task assignment and update all counters."""
        # Add annotator as project member (for UI visibility)
        ProjectMember.objects.get_or_create(
            user=annotator.user, project=project, defaults={"enabled": True}
        )

        # Ensure project is published
        if not project.is_published:
            project.is_published = True
            project.save(update_fields=["is_published"])

        # Create assignment
        assignment = TaskAssignment.objects.create(
            annotator=annotator,
            task=task,
            status="assigned",
        )

        # Update counters
        task.assignment_count = F("assignment_count") + 1
        task.save(update_fields=["assignment_count"])

        ProjectAssignment.objects.filter(
            project=project,
            annotator=annotator,
        ).update(assigned_tasks=F("assigned_tasks") + 1)

        return assignment

    @staticmethod
    def _check_capacity(annotator):
        """Check annotator's current workload capacity."""
        try:
            trust_level = annotator.trust_level.level
            max_tasks = CAPACITY_LIMITS.get(trust_level, 50)
        except:
            max_tasks = 50

        # Check custom limit
        custom_max = getattr(annotator, "max_concurrent_tasks", None)
        if custom_max:
            max_tasks = min(max_tasks, custom_max)

        active_count = TaskAssignment.objects.filter(
            annotator=annotator, status__in=["assigned", "in_progress"]
        ).count()

        return {
            "current": active_count,
            "maximum": max_tasks,
            "available": max(0, max_tasks - active_count),
            "at_capacity": active_count >= max_tasks,
        }

    @staticmethod
    def _trigger_consolidation_check(task):
        """
        Check if task has 3 annotations and trigger consolidation.

        This is called when a task reaches full assignment (3/3).
        Wait for all 3 annotators to complete, then auto-consolidate.
        """
        # Check completed annotations count
        from tasks.models import Annotation

        completed_count = Annotation.objects.filter(
            task=task, was_cancelled=False
        ).count()

        if completed_count >= REQUIRED_OVERLAP:
            logger.info(
                f"🎯 Task {task.id} has {completed_count} annotations - triggering consolidation"
            )

            # Trigger consolidation
            try:
                from .annotation_workflow import AnnotationWorkflowService

                # This will handle consolidation and quality scoring
                AnnotationWorkflowService.on_all_annotations_complete(task)

                logger.info(f"✅ Consolidation triggered for task {task.id}")
            except Exception as e:
                logger.error(f"Error triggering consolidation for task {task.id}: {e}")
        else:
            logger.debug(
                f"Task {task.id} assigned to 3 annotators, waiting for completion "
                f"({completed_count}/{REQUIRED_OVERLAP} done)"
            )





