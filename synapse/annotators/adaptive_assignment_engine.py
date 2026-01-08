"""
Adaptive Assignment Engine - Intelligent task assignment with dynamic overlap

This engine automatically adapts to:
- Number of available annotators (2 annotators → overlap=2, ≥3 → overlap=3)
- Annotator capacity and workload
- Task priority and complexity
- Annotator performance and trust level
- Availability and eligibility

Key Features:
- Dynamic overlap calculation
- Capacity-aware assignment with holding
- Smart workload distribution
- Auto-reassignment when capacity available
- Performance-based scoring
"""

import logging
from django.db.models import Count, Q, Avg, F
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


class AdaptiveAssignmentEngine:
    """
    Intelligent assignment engine that adapts to project conditions
    """

    # Capacity limits by trust level (max concurrent active assignments)
    CAPACITY_LIMITS = {
        "novice": 5,
        "intermediate": 10,
        "expert": 15,
        "master": 20,
    }

    # Minimum annotators needed for each overlap level
    MIN_ANNOTATORS_FOR_OVERLAP = {
        1: 1,  # 1 annotator → overlap=1
        2: 2,  # 2 annotators → overlap=2
        3: 3,  # 3+ annotators → overlap=3
    }

    @staticmethod
    def calculate_optimal_overlap(project):
        """
        Dynamically calculate the optimal overlap based on available annotators

        Logic:
        - 1 annotator available → overlap = 1
        - 2 annotators available → overlap = 2
        - 3+ annotators available → overlap = 3 (maximum for quality)
        """
        from annotators.models import ProjectAssignment

        # Count active annotators with available capacity
        active_annotators = (
            ProjectAssignment.objects.filter(project=project, active=True)
            .select_related("annotator")
            .all()
        )

        # Check which annotators have capacity
        available_count = 0
        for pa in active_annotators:
            if AdaptiveAssignmentEngine.has_capacity(pa.annotator, project):
                available_count += 1

        # Total annotators (including those at capacity)
        total_annotators = active_annotators.count()

        # Use the higher of available or total for overlap calculation
        # This allows assignment to queue for when capacity opens up
        annotator_count = max(available_count, total_annotators)

        if annotator_count >= 3:
            overlap = 3
        elif annotator_count == 2:
            overlap = 2
        elif annotator_count == 1:
            overlap = 1
        else:
            overlap = 1  # Default to 1 if no annotators

        logger.info(
            f"📊 Adaptive Overlap Calculation:\n"
            f"   Total annotators: {total_annotators}\n"
            f"   Available annotators: {available_count}\n"
            f"   → Optimal overlap: {overlap}"
        )

        return overlap, total_annotators, available_count

    @staticmethod
    def has_capacity(annotator, project):
        """
        Check if annotator has capacity for more assignments
        """
        from annotators.models import TaskAssignment

        # Get trust level capacity limit
        trust_level = annotator.trust_level or "novice"
        max_capacity = AdaptiveAssignmentEngine.CAPACITY_LIMITS.get(trust_level, 5)

        # Count current active assignments (assigned or in_progress)
        current_load = TaskAssignment.objects.filter(
            annotator=annotator,
            task__project=project,
            status__in=["assigned", "in_progress"],
        ).count()

        has_space = current_load < max_capacity

        if not has_space:
            logger.debug(
                f"⚠️ {annotator.user.email} at capacity: "
                f"{current_load}/{max_capacity} ({trust_level})"
            )

        return has_space

    @staticmethod
    def get_annotator_workload_score(annotator, project):
        """
        Calculate workload score (0-100, lower = less loaded)
        Used for fair distribution
        """
        from annotators.models import TaskAssignment

        trust_level = annotator.trust_level or "novice"
        max_capacity = AdaptiveAssignmentEngine.CAPACITY_LIMITS.get(trust_level, 5)

        current_load = TaskAssignment.objects.filter(
            annotator=annotator,
            task__project=project,
            status__in=["assigned", "in_progress"],
        ).count()

        # Calculate load percentage (inverted for score)
        load_percentage = (current_load / max_capacity) * 100
        workload_score = 100 - load_percentage  # Lower load = higher score

        return workload_score

    @staticmethod
    def score_annotator_for_task(annotator, task, project):
        """
        Comprehensive scoring system for annotator-task matching

        Factors:
        - Workload (30%): Fair distribution
        - Performance (25%): Quality and accuracy
        - Expertise (20%): Trust level and experience
        - Availability (15%): Recent activity
        - Task fit (10%): Task complexity vs annotator skill
        """
        from annotators.models import TaskAssignment

        score_components = {}

        # 1. Workload Score (30%) - Lower workload = higher score
        workload_score = AdaptiveAssignmentEngine.get_annotator_workload_score(
            annotator, project
        )
        score_components["workload"] = workload_score * 0.30

        # 2. Performance Score (25%) - Based on quality
        if annotator.average_quality_score:
            performance_score = annotator.average_quality_score
        else:
            performance_score = 70  # Default for new annotators
        score_components["performance"] = performance_score * 0.25

        # 3. Expertise Score (20%) - Trust level
        trust_scores = {"novice": 60, "intermediate": 75, "expert": 90, "master": 100}
        trust_level = annotator.trust_level or "novice"
        expertise_score = trust_scores.get(trust_level, 60)
        score_components["expertise"] = expertise_score * 0.20

        # 4. Availability Score (15%) - Recent activity
        recent_assignments = TaskAssignment.objects.filter(
            annotator=annotator,
            task__project=project,
            completed_at__gte=timezone.now() - timedelta(days=7),
        ).count()

        # Active in last week = higher availability
        if recent_assignments > 0:
            availability_score = 90
        else:
            availability_score = 60
        score_components["availability"] = availability_score * 0.15

        # 5. Task Fit Score (10%) - Match task complexity to skill
        task_complexity = getattr(task, "complexity_score", 50) or 50
        annotator_skill = annotator.average_quality_score or 70

        # Perfect match = skill matches complexity
        fit_difference = abs(annotator_skill - task_complexity)
        task_fit_score = 100 - fit_difference
        task_fit_score = max(50, min(100, task_fit_score))  # Clamp 50-100
        score_components["task_fit"] = task_fit_score * 0.10

        # Calculate total score
        total_score = sum(score_components.values())

        logger.debug(
            f"   {annotator.user.email}: {total_score:.1f} "
            f"(W:{score_components['workload']:.1f} "
            f"P:{score_components['performance']:.1f} "
            f"E:{score_components['expertise']:.1f} "
            f"A:{score_components['availability']:.1f} "
            f"F:{score_components['task_fit']:.1f})"
        )

        return total_score, score_components

    @staticmethod
    def adaptive_assign_project_tasks(project):
        """
        Main assignment function with adaptive overlap and intelligent distribution

        Returns:
            dict: Assignment statistics and status
        """
        from tasks.models import Task
        from annotators.models import ProjectAssignment, TaskAssignment

        logger.info(
            f"\n🚀 Starting Adaptive Assignment for Project {project.id}: {project.title}"
        )

        # 1. Calculate optimal overlap dynamically
        optimal_overlap, total_annotators, available_annotators = (
            AdaptiveAssignmentEngine.calculate_optimal_overlap(project)
        )

        if total_annotators == 0:
            logger.warning("❌ No annotators assigned to project")
            return {
                "status": "no_annotators",
                "message": "No annotators available for assignment",
            }

        # 2. Get all active annotators with their profiles
        project_assignments = ProjectAssignment.objects.filter(
            project=project, active=True
        ).select_related("annotator", "annotator__user")

        annotators = [pa.annotator for pa in project_assignments]

        # 3. Get tasks needing assignment
        tasks = (
            Task.objects.filter(project=project)
            .annotate(
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
            .order_by("priority", "id")
        )

        stats = {
            "total_tasks": tasks.count(),
            "fully_assigned": 0,
            "partially_assigned": 0,
            "pending_capacity": 0,
            "newly_assigned": 0,
            "optimal_overlap": optimal_overlap,
            "total_annotators": total_annotators,
            "available_annotators": available_annotators,
        }

        # 4. Process each task
        for task in tasks:
            assignments_needed = optimal_overlap - task.current_assignments

            if assignments_needed <= 0:
                stats["fully_assigned"] += 1
                continue

            # Find best annotators for this task
            assigned_count = AdaptiveAssignmentEngine._assign_task_to_best_annotators(
                task, annotators, assignments_needed, project
            )

            if assigned_count > 0:
                stats["newly_assigned"] += assigned_count

            if assigned_count < assignments_needed:
                if task.current_assignments + assigned_count > 0:
                    stats["partially_assigned"] += 1
                else:
                    stats["pending_capacity"] += 1

        # 5. Log summary
        logger.info(
            f"\n✅ Adaptive Assignment Complete:\n"
            f"   Optimal overlap: {optimal_overlap} (based on {total_annotators} annotators)\n"
            f"   Total tasks: {stats['total_tasks']}\n"
            f"   Fully assigned: {stats['fully_assigned']}\n"
            f"   Partially assigned: {stats['partially_assigned']}\n"
            f"   Pending capacity: {stats['pending_capacity']}\n"
            f"   New assignments: {stats['newly_assigned']}\n"
            f"   Available annotators: {available_annotators}/{total_annotators}"
        )

        # 6. Trigger consolidation for fully annotated tasks
        AdaptiveAssignmentEngine._trigger_consolidation_for_complete_tasks(
            project, optimal_overlap
        )

        return stats

    @staticmethod
    def _assign_task_to_best_annotators(task, annotators, needed_count, project):
        """
        Assign task to the best available annotators based on scoring

        Returns:
            int: Number of assignments made
        """
        from annotators.models import TaskAssignment

        # Check who is already assigned
        existing_assignments = TaskAssignment.objects.filter(task=task).values_list(
            "annotator_id", flat=True
        )

        # Score all available annotators
        annotator_scores = []

        for annotator in annotators:
            # Skip if already assigned
            if annotator.id in existing_assignments:
                continue

            # Skip if no capacity
            if not AdaptiveAssignmentEngine.has_capacity(annotator, project):
                continue

            # Calculate score
            score, components = AdaptiveAssignmentEngine.score_annotator_for_task(
                annotator, task, project
            )

            annotator_scores.append(
                {"annotator": annotator, "score": score, "components": components}
            )

        # Sort by score (highest first)
        annotator_scores.sort(key=lambda x: x["score"], reverse=True)

        # Assign to top N annotators
        assigned_count = 0
        for item in annotator_scores[:needed_count]:
            annotator = item["annotator"]

            # Create assignment
            assignment = TaskAssignment.objects.create(
                task=task,
                annotator=annotator,
                assigned_by=project.created_by,
                status="assigned",
                assigned_at=timezone.now(),
            )

            logger.info(
                f"   ✓ Assigned Task {task.id} → {annotator.user.email} "
                f"(score: {item['score']:.1f})"
            )

            assigned_count += 1

        # Log if we couldn't assign all needed
        if assigned_count < needed_count:
            remaining = needed_count - assigned_count
            logger.warning(
                f"   ⚠️ Task {task.id}: Only assigned {assigned_count}/{needed_count}. "
                f"{remaining} waiting for annotator capacity."
            )

        return assigned_count

    @staticmethod
    def _trigger_consolidation_for_complete_tasks(project, required_overlap):
        """
        Check for tasks that have reached the required overlap and trigger consolidation
        """
        from tasks.models import Task, Annotation
        from annotators.models import TaskConsensus

        # Find tasks with required number of annotations
        tasks = (
            Task.objects.filter(project=project)
            .annotate(
                annotation_count=Count(
                    "annotations", filter=Q(annotations__was_cancelled=False)
                )
            )
            .filter(annotation_count__gte=required_overlap)
        )

        consolidated_count = 0

        for task in tasks:
            # Check if already has consensus
            if TaskConsensus.objects.filter(task=task).exists():
                continue

            # Trigger consolidation
            try:
                from annotators.annotation_workflow import AnnotationWorkflowService

                logger.info(
                    f"🔔 Triggering consolidation for Task {task.id} ({task.annotation_count} annotations)"
                )
                AnnotationWorkflowService.on_all_annotations_complete(task)
                consolidated_count += 1

            except Exception as e:
                logger.error(f"❌ Error consolidating Task {task.id}: {e}")

        if consolidated_count > 0:
            logger.info(f"✅ Triggered consolidation for {consolidated_count} tasks")

    @staticmethod
    def reassign_when_capacity_available(project):
        """
        Check for pending tasks and reassign when annotators have capacity

        Call this when:
        - An annotator completes a task
        - A new annotator joins the project
        - Periodically to handle capacity changes
        """
        from tasks.models import Task

        logger.info(
            f"\n🔄 Checking for reassignment opportunities in Project {project.id}"
        )

        # Get current optimal overlap
        optimal_overlap, total_annotators, available_annotators = (
            AdaptiveAssignmentEngine.calculate_optimal_overlap(project)
        )

        if available_annotators == 0:
            logger.info("⚠️ No annotators with available capacity")
            return {"status": "no_capacity", "message": "All annotators at capacity"}

        # Find tasks that need more assignments
        tasks_needing_assignment = (
            Task.objects.filter(project=project)
            .annotate(
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
            .filter(current_assignments__lt=optimal_overlap)
            .order_by("priority", "id")
        )

        if not tasks_needing_assignment.exists():
            logger.info("✅ All tasks fully assigned")
            return {
                "status": "fully_assigned",
                "message": "No tasks need additional assignment",
            }

        # Run adaptive assignment
        return AdaptiveAssignmentEngine.adaptive_assign_project_tasks(project)

    @staticmethod
    def update_overlap_and_reassign(project):
        """
        Recalculate optimal overlap and reassign as needed

        Use this when the number of annotators changes
        """
        logger.info(f"\n🔄 Updating overlap and reassigning for Project {project.id}")

        # Calculate new optimal overlap
        new_overlap, total_annotators, available_annotators = (
            AdaptiveAssignmentEngine.calculate_optimal_overlap(project)
        )

        logger.info(
            f"📊 Updated overlap: {new_overlap} "
            f"(based on {total_annotators} annotators, {available_annotators} available)"
        )

        # Reassign with new overlap
        return AdaptiveAssignmentEngine.adaptive_assign_project_tasks(project)

    @staticmethod
    def get_project_assignment_status(project):
        """
        Get detailed status of project assignments for monitoring
        """
        from tasks.models import Task
        from annotators.models import ProjectAssignment, TaskAssignment

        optimal_overlap, total_annotators, available_annotators = (
            AdaptiveAssignmentEngine.calculate_optimal_overlap(project)
        )

        tasks = Task.objects.filter(project=project).annotate(
            num_assignments=Count("annotator_assignments"),
            num_annotations=Count(
                "annotations", filter=Q(annotations__was_cancelled=False)
            ),
        )

        fully_assigned = tasks.filter(num_assignments__gte=optimal_overlap).count()
        partially_assigned = tasks.filter(
            num_assignments__gt=0, num_assignments__lt=optimal_overlap
        ).count()
        unassigned = tasks.filter(num_assignments=0).count()

        # Annotator workload
        annotator_status = []
        for pa in ProjectAssignment.objects.filter(
            project=project, active=True
        ).select_related("annotator", "annotator__user"):
            annotator = pa.annotator
            trust_level = annotator.trust_level or "novice"
            max_capacity = AdaptiveAssignmentEngine.CAPACITY_LIMITS.get(trust_level, 5)

            current_load = TaskAssignment.objects.filter(
                annotator=annotator,
                task__project=project,
                status__in=["assigned", "in_progress"],
            ).count()

            completed = TaskAssignment.objects.filter(
                annotator=annotator, task__project=project, status="completed"
            ).count()

            annotator_status.append(
                {
                    "email": annotator.user.email,
                    "trust_level": trust_level,
                    "current_load": current_load,
                    "max_capacity": max_capacity,
                    "capacity_percent": (current_load / max_capacity) * 100,
                    "completed": completed,
                    "has_capacity": current_load < max_capacity,
                }
            )

        return {
            "project_id": project.id,
            "project_title": project.title,
            "optimal_overlap": optimal_overlap,
            "total_annotators": total_annotators,
            "available_annotators": available_annotators,
            "task_stats": {
                "total": tasks.count(),
                "fully_assigned": fully_assigned,
                "partially_assigned": partially_assigned,
                "unassigned": unassigned,
            },
            "annotator_status": annotator_status,
        }





