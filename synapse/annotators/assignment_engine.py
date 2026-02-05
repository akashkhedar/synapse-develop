from django.db import transaction, models
from django.db.models import Q, Count, Avg, F, Case, When, Value, FloatField
from django.conf import settings
from django.utils import timezone
from projects.models import Project, ProjectMember
from .models import AnnotatorProfile, ProjectAssignment, TaskAssignment, TrustLevel
import logging
import random
from datetime import timedelta
from decimal import Decimal

logger = logging.getLogger(__name__)


MAX_TASKS_IN_PROGRESS = getattr(settings, "ANNOTATOR_MAX_ACTIVE_TASKS", 10)

# Capacity limits based on trust level (increased for better testing and real-world usage)
CAPACITY_LIMITS = {
    "new": 50,
    "junior": 100,
    "regular": 150,
    "senior": 200,
    "expert": 300,
}


# CONSTANTS FOR ASSIGNMENT SYSTEM
REQUIRED_OVERLAP = 3  # Hard-coded: Always require 3 annotators per task
MAX_ASSIGNMENT_ATTEMPTS = 100  # Prevent infinite loops


class AssignmentEngine:
    """
    Enhanced assignment algorithm for matching annotators to projects and tasks
    with intelligent scoring and multiple strategies

    KEY FEATURES:
    - Hard-coded overlap = 3 (always 3 annotators per task)
    - Smart rotating distribution across available annotators
    - Capacity-aware assignment (respects workload limits)
    - Partial assignment handling (holds incomplete tasks)
    - Auto-reassignment when new annotators become available
    - Consolidation trigger when task reaches 3 annotations
    """

    @staticmethod
    def calculate_assignment_score(annotator, project):
        """
        Calculate assignment score for an annotator-project pair

        Score = Skill_Match (35%) + Trust_Level (25%) + Availability (20%) +
                Performance_History (15%) + Cost_Efficiency (5%)

        Returns: float score 0-100
        """
        scores = {
            "skill_match": AssignmentEngine._calculate_skill_match(annotator, project)
            * 0.35,
            "trust_level": AssignmentEngine._calculate_trust_score(annotator, project)
            * 0.25,
            "availability": AssignmentEngine._calculate_availability_score(annotator)
            * 0.20,
            "performance": AssignmentEngine._calculate_performance_score(
                annotator, project
            )
            * 0.15,
            "cost_efficiency": AssignmentEngine._calculate_cost_efficiency(annotator)
            * 0.05,
        }

        total_score = sum(scores.values())

        logger.debug(
            f"Assignment score for {annotator.user.email} -> {project.title}: "
            f"{total_score:.2f} (breakdown: {scores})"
        )

        return total_score

    @staticmethod
    def _calculate_skill_match(annotator, project):
        """Calculate skill matching score (0-100)"""
        score = 0

        try:
            # Get project requirements
            required_skills = getattr(project, "required_skills", []) or []
            annotator_skills = annotator.skills or []

            if not required_skills:
                # No specific requirements, all annotators match
                return 100

            # Check annotation type match (required)
            # This would come from label config analysis
            annotation_type = AssignmentEngine._extract_annotation_type(project)
            if annotation_type in annotator_skills:
                score += 40  # Base score for type match
            else:
                return 0  # Disqualified if missing main skill

            # Check additional skills
            if required_skills:
                matched_skills = len(set(required_skills) & set(annotator_skills))
                skill_percentage = (matched_skills / len(required_skills)) * 60
                score += skill_percentage
            else:
                score += 60  # No additional requirements

        except Exception as e:
            logger.warning(f"Error calculating skill match: {e}")
            score = 50  # Default moderate score

        return min(score, 100)

    @staticmethod
    def _calculate_trust_score(annotator, project):
        """Calculate trust level score (0-100)"""
        try:
            trust_level = annotator.trust_level
            level = trust_level.level

            # Base scores by level
            level_scores = {
                "new": 60,
                "junior": 70,
                "regular": 80,
                "senior": 90,
                "expert": 100,
            }

            base_score = level_scores.get(level, 60)

            # Check minimum trust requirement
            min_trust = getattr(project, "min_trust_level", None)
            if min_trust:
                levels_order = ["new", "junior", "regular", "senior", "expert"]
                if levels_order.index(level) < levels_order.index(min_trust):
                    return 0  # Disqualified

            # Adjust for fraud flags
            if trust_level.fraud_flags > 0:
                base_score -= trust_level.fraud_flags * 10

            return max(0, min(base_score, 100))

        except TrustLevel.DoesNotExist:
            return 50  # New annotator, moderate score

    @staticmethod
    def _calculate_availability_score(annotator):
        """Calculate availability score (0-100)"""
        score = 0

        try:
            # Check if accepting work
            if not getattr(annotator, "is_accepting_work", True):
                return 0

            # Current workload (50 points)
            active_tasks = TaskAssignment.objects.filter(
                annotator=annotator, status__in=["assigned", "in_progress"]
            ).count()

            try:
                trust_level = annotator.trust_level.level
                max_capacity = CAPACITY_LIMITS.get(trust_level, 10)
            except:
                max_capacity = 10

            capacity_score = (
                (1 - active_tasks / max_capacity) * 50 if max_capacity > 0 else 0
            )
            score += max(0, capacity_score)

            # Recent activity (30 points)
            if annotator.last_active:
                days_since_active = (timezone.now() - annotator.last_active).days
                recency_score = max(0, (7 - days_since_active) / 7) * 30
                score += recency_score
            else:
                score += 15  # Moderate score for new annotators

            # Preferred hours (20 points)
            preferred_hours = getattr(annotator, "preferred_hours_per_week", 20)
            if preferred_hours >= 20:
                score += 20
            else:
                score += (preferred_hours / 20) * 20

        except Exception as e:
            logger.warning(f"Error calculating availability: {e}")
            score = 50

        return min(score, 100)

    @staticmethod
    def _calculate_performance_score(annotator, project):
        """Calculate performance history score (0-100)"""
        score = 0

        try:
            # Overall accuracy (40%)
            accuracy_score = float(annotator.accuracy_score or 0)
            score += accuracy_score * 0.4

            # Completion rate (30%)
            completed = TaskAssignment.objects.filter(
                annotator=annotator, status="completed"
            ).count()
            assigned = TaskAssignment.objects.filter(annotator=annotator).count()

            completion_rate = (completed / assigned * 100) if assigned > 0 else 80
            score += completion_rate * 0.3

            # Quality consistency (30%)
            # Lower rejection rate = higher score
            rejection_rate = float(annotator.rejection_rate or 0)
            consistency_score = max(0, 100 - rejection_rate * 2)
            score += consistency_score * 0.3

        except Exception as e:
            logger.warning(f"Error calculating performance: {e}")
            score = 50

        return min(score, 100)

    @staticmethod
    def _calculate_cost_efficiency(annotator):
        """Calculate cost efficiency score (0-100)"""
        try:
            # Safely get or create trust level
            if hasattr(annotator, "trust_level"):
                trust_level = annotator.trust_level
            else:
                from .models import TrustLevel

                trust_level, _ = TrustLevel.objects.get_or_create(annotator=annotator)

            multiplier = float(trust_level.multiplier)
            accuracy = float(annotator.accuracy_score or 70)

            # Quality per cost ratio
            quality_per_cost = accuracy / multiplier if multiplier > 0 else accuracy

            # Normalize to 0-100 range
            score = min(quality_per_cost, 100)

            return score

        except Exception as e:
            logger.warning(f"Error calculating cost efficiency: {e}")
            return 50

    @staticmethod
    def _extract_annotation_type(project):
        """Extract annotation type from project label config"""
        try:
            # Simple extraction - can be enhanced
            label_config = project.label_config or ""

            if "RectangleLabels" in label_config or "Rectangle" in label_config:
                return "Object Detection"
            elif "PolygonLabels" in label_config:
                return "Polygon"
            elif "Choices" in label_config:
                return "Image Classification"
            elif "Labels" in label_config and "Text" in label_config:
                return "Named Entity Recognition"
            else:
                return "default"

        except Exception as e:
            logger.warning(f"Error extracting annotation type: {e}")
            return "default"

    @staticmethod
    def assign_annotators_to_project(project, num_annotators=None, required_overlap=1):
        """
        Assign annotators to a project using intelligent scoring

        Args:
            project: Project instance
            num_annotators: Number of annotators to assign (auto-calculated if None)
            required_overlap: Number of annotators per task

        Returns:
            List of ProjectAssignment instances
        """
        print(
            f"[AssignmentEngine] assign_annotators_to_project called for project {project.id}"
        )

        # Get all approved, active annotators
        available_annotators = AnnotatorProfile.objects.filter(
            status="approved",
            user__is_active=True,
        ).select_related("user", "trust_level")

        print(
            f"[AssignmentEngine] Initial available annotators (approved & active): {available_annotators.count()}"
        )

        # Filter by project requirements
        available_annotators = AssignmentEngine._filter_by_requirements(
            available_annotators, project
        )

        print(
            f"[AssignmentEngine] After requirements filter: {available_annotators.count()}"
        )

        # Calculate scores for each annotator
        annotator_scores = []
        for annotator in available_annotators:
            score = AssignmentEngine.calculate_assignment_score(annotator, project)
            print(f"[AssignmentEngine] Annotator {annotator.user.email} score: {score}")
            if score > 0:  # Only include qualified annotators
                annotator_scores.append((annotator, score))

        # Sort by score (highest first)
        annotator_scores.sort(key=lambda x: x[1], reverse=True)
        print(f"[AssignmentEngine] Annotators with score > 0: {len(annotator_scores)}")

        # Determine how many annotators to assign
        if num_annotators is None:
            num_annotators = AssignmentEngine._calculate_optimal_annotator_count(
                project, required_overlap
            )

        # Handle case where we have fewer annotators than needed
        available_count = len(annotator_scores)
        if available_count < required_overlap:
            logger.warning(
                f"Project {project.id} requires {required_overlap} annotators per task, "
                f"but only {available_count} annotators available. "
                f"Tasks will be assigned to all available annotators."
            )
            # Assign all available annotators
            num_annotators = available_count
        else:
            # Get max annotators from project settings (handle None)
            max_annotators = getattr(project, "max_annotators", None)
            if max_annotators is None:
                max_annotators = 1000  # Default value: Allow wide distribution
            num_annotators = min(num_annotators, max_annotators, available_count)

        # Ensure at least 1 annotator if any are available
        if available_count > 0:
            num_annotators = max(1, num_annotators)

        # Assign top-scoring annotators
        assignments = []
        for annotator, score in annotator_scores[:num_annotators]:
            # IMPORTANT: Add annotator as project member so they can see the project in UI
            ProjectMember.objects.get_or_create(
                user=annotator.user, project=project, defaults={"enabled": True}
            )

            assignment, created = ProjectAssignment.objects.get_or_create(
                project=project,
                annotator=annotator,
                defaults={
                    "role": "annotator",
                    "active": True,
                    "assigned_by": "system_intelligent",
                },
            )
            if created:
                assignments.append(assignment)
                logger.info(
                    f"Assigned annotator {annotator.user.email} to project {project.id} "
                    f"with score {score:.2f}"
                )

        # Ensure project is published so annotators can see it
        if assignments and not project.is_published:
            project.is_published = True
            project.save(update_fields=["is_published"])
            logger.info(f"Auto-published project {project.id} for annotator visibility")

        return assignments

    @staticmethod
    def _filter_by_requirements(annotators, project):
        """Filter annotators by project requirements"""
        # Note: is_accepting_work field removed as it doesn't exist in model
        # All approved annotators are considered available

        # Check minimum trust level
        min_trust = getattr(project, "min_trust_level", None)
        if min_trust and min_trust != "new":
            levels_order = ["new", "junior", "regular", "senior", "expert"]
            min_index = levels_order.index(min_trust)
            allowed_levels = levels_order[min_index:]
            annotators = annotators.filter(trust_level__level__in=allowed_levels)

        # Filter out suspended or high fraud flags (but allow annotators without trust_level)
        annotators = annotators.filter(
            models.Q(trust_level__isnull=True)
            | models.Q(trust_level__fraud_flags__lt=3, trust_level__is_suspended=False)
        )

        # Check quality requirements
        quality_req = getattr(project, "quality_requirement", 0) or 0
        if quality_req >= 0.9:  # high quality
            annotators = annotators.filter(
                accuracy_score__gte=90,
                trust_level__level__in=["regular", "senior", "expert"],
            )
        elif quality_req >= 0.95:  # critical quality
            annotators = annotators.filter(
                accuracy_score__gte=95, trust_level__level__in=["senior", "expert"]
            )

        return annotators

    @staticmethod
    def _calculate_optimal_annotator_count(project, required_overlap):
        """
        Calculate optimal number of annotators for a project.

        Returns all available annotators (no artificial limit).
        The distribution algorithm will handle rotation intelligently.
        """
        task_count = project.tasks.count()

        # For small projects with few tasks, limit to required_overlap
        if task_count < 10:
            optimal_count = required_overlap
        else:
            # For larger projects, use all available annotators for better distribution
            # The rotating algorithm will distribute tasks intelligently
            optimal_count = 1000  # High limit - will be capped by actual available count

        logger.info(
            f"Optimal annotator count for project {project.id}: {optimal_count} "
            f"(tasks: {task_count}, required_overlap: {required_overlap})"
        )

        return optimal_count

    @staticmethod
    def assign_next_task_to_annotator(project, annotator, required_overlap=None):
        """
        Assign next task to annotator using project's assignment strategy

        Strategies:
        - round_robin: Fair distribution
        - performance: Better performers get more tasks
        - skill_match: Match task complexity to annotator level
        - consensus: Ensure required overlap
        """
        if required_overlap is None:
            required_overlap = getattr(project, "required_overlap", 1)

        # Check annotator capacity
        capacity_info = AssignmentEngine.check_annotator_capacity(annotator)
        if capacity_info["at_capacity"]:
            logger.info(
                f"Annotator {annotator.user.email} at capacity ({capacity_info['current']}/{capacity_info['maximum']})"
            )
            return None

        # Get assignment strategy
        strategy = getattr(project, "assignment_strategy", "round_robin")

        if strategy == "round_robin":
            return AssignmentEngine._round_robin_assignment(
                project, annotator, required_overlap
            )
        elif strategy == "performance":
            return AssignmentEngine._performance_based_assignment(
                project, annotator, required_overlap
            )
        elif strategy == "skill_match":
            return AssignmentEngine._skill_matched_assignment(
                project, annotator, required_overlap
            )
        elif strategy == "consensus":
            return AssignmentEngine._consensus_assignment(
                project, annotator, required_overlap
            )
        else:
            return AssignmentEngine._round_robin_assignment(
                project, annotator, required_overlap
            )

    @staticmethod
    def _round_robin_assignment(project, annotator, required_overlap):
        """Round-robin: Fair distribution across all annotators"""
        already_assigned = TaskAssignment.objects.filter(
            annotator=annotator,
            task__project=project,
        ).values_list("task_id", flat=True)

        with transaction.atomic():
            task = (
                project.tasks.exclude(id__in=already_assigned)
                .annotate(assignments_count=Count("annotator_assignments"))
                .filter(assignments_count__lt=required_overlap)
                .select_for_update(skip_locked=True)
                .order_by(
                    Case(
                        When(priority="critical", then=Value(1)),
                        When(priority="high", then=Value(2)),
                        When(priority="medium", then=Value(3)),
                        When(priority="low", then=Value(4)),
                        default=Value(3),
                        output_field=FloatField(),
                    ),
                    "id",
                )
                .first()
            )

            if not task:
                return None

            return AssignmentEngine._create_task_assignment(annotator, task, project)

    @staticmethod
    def _performance_based_assignment(project, annotator, required_overlap):
        """Performance-based: High performers get priority on important tasks"""
        # Check if annotator is high performer
        is_high_performer = (
            annotator.accuracy_score >= 85
            and annotator.trust_level.level in ["regular", "senior", "expert"]
        )

        already_assigned = TaskAssignment.objects.filter(
            annotator=annotator,
            task__project=project,
        ).values_list("task_id", flat=True)

        with transaction.atomic():
            queryset = (
                project.tasks.exclude(id__in=already_assigned)
                .annotate(assignments_count=Count("annotator_assignments"))
                .filter(assignments_count__lt=required_overlap)
                .select_for_update(skip_locked=True)
            )

            if is_high_performer:
                # High performers get high-priority and complex tasks first
                task = (
                    queryset.filter(
                        Q(priority__in=["critical", "high"])
                        | Q(complexity__in=["high", "very_high"])
                    )
                    .order_by("-priority", "id")
                    .first()
                )

                if not task:
                    # Fall back to any task
                    task = queryset.order_by("id").first()
            else:
                # Regular performers get standard tasks
                task = (
                    queryset.exclude(Q(priority="critical") | Q(complexity="very_high"))
                    .order_by("id")
                    .first()
                )

            if not task:
                return None

            return AssignmentEngine._create_task_assignment(annotator, task, project)

    @staticmethod
    def _skill_matched_assignment(project, annotator, required_overlap):
        """Skill-matched: Match task complexity to annotator trust level"""
        trust_level = annotator.trust_level.level

        # Map trust levels to allowed complexity
        complexity_mapping = {
            "new": ["very_low", "low"],
            "junior": ["very_low", "low", "medium"],
            "regular": ["low", "medium", "high"],
            "senior": ["medium", "high", "very_high"],
            "expert": ["high", "very_high"],
        }

        allowed_complexities = complexity_mapping.get(trust_level, ["medium"])

        already_assigned = TaskAssignment.objects.filter(
            annotator=annotator,
            task__project=project,
        ).values_list("task_id", flat=True)

        with transaction.atomic():
            task = (
                project.tasks.exclude(id__in=already_assigned)
                .annotate(assignments_count=Count("annotator_assignments"))
                .filter(
                    assignments_count__lt=required_overlap,
                )
                .filter(
                    Q(complexity__in=allowed_complexities)
                    | Q(complexity__isnull=True)  # Allow unclassified tasks
                )
                .select_for_update(skip_locked=True)
                .order_by("id")
                .first()
            )

            if not task:
                return None

            return AssignmentEngine._create_task_assignment(annotator, task, project)

    @staticmethod
    def _consensus_assignment(project, annotator, required_overlap):
        """Consensus: Ensure multiple annotators per task"""
        # Prioritize tasks that need more annotators for consensus
        already_assigned = TaskAssignment.objects.filter(
            annotator=annotator,
            task__project=project,
        ).values_list("task_id", flat=True)

        with transaction.atomic():
            # First, try to find tasks that already have partial assignments
            # (to complete consensus requirements)
            task = (
                project.tasks.exclude(id__in=already_assigned)
                .annotate(assignments_count=Count("annotator_assignments"))
                .filter(assignments_count__gt=0, assignments_count__lt=required_overlap)
                .select_for_update(skip_locked=True)
                .order_by("-assignments_count", "id")
                .first()
            )

            if not task:
                # Fall back to new tasks
                task = (
                    project.tasks.exclude(id__in=already_assigned)
                    .annotate(assignments_count=Count("annotator_assignments"))
                    .filter(assignments_count__lt=required_overlap)
                    .select_for_update(skip_locked=True)
                    .order_by("id")
                    .first()
                )

            if not task:
                return None

            return AssignmentEngine._create_task_assignment(annotator, task, project)

    @staticmethod
    def _create_task_assignment(annotator, task, project):
        """Create a task assignment and update counters"""

        # IMPORTANT: Automatically add annotator as project member so they can see the project in UI
        ProjectMember.objects.get_or_create(
            user=annotator.user, project=project, defaults={"enabled": True}
        )

        # Ensure project is published so annotators can see it
        if not project.is_published:
            project.is_published = True
            project.save(update_fields=["is_published"])
            logger.info(f"Auto-published project {project.id} for annotator visibility")

        assignment = TaskAssignment.objects.create(
            annotator=annotator,
            task=task,
            status="assigned",
        )

        # Update assignment count on task
        task.assignment_count = F("assignment_count") + 1
        task.save(update_fields=["assignment_count"])

        # Update project assignment counters
        ProjectAssignment.objects.filter(
            project=project,
            annotator=annotator,
        ).update(assigned_tasks=F("assigned_tasks") + 1)

        logger.info(f"Assigned task {task.id} to annotator {annotator.user.email}")

        return assignment

    @staticmethod
    def check_annotator_capacity(annotator):
        """Check annotator's current capacity"""
        try:
            trust_level = annotator.trust_level.level
            max_tasks = CAPACITY_LIMITS.get(trust_level, 10)
        except:
            max_tasks = 10

        # Allow custom limit from profile
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
    def bulk_assign_tasks(project, annotator, batch_size=5, required_overlap=1):
        assignments = []

        for _ in range(batch_size):
            assignment = AssignmentEngine.assign_next_task_to_annotator(
                project,
                annotator,
                required_overlap=required_overlap,
            )
            if not assignment:
                break
            assignments.append(assignment)

        return assignments

    @staticmethod
    def distribute_tasks_intelligently(project, annotators, required_overlap=3):
        """
        Intelligently distribute tasks with rotating assignment pattern.

        Algorithm:
        - If annotators <= required_overlap: Assign ALL tasks to ALL annotators
        - If annotators > required_overlap: Rotate annotators across tasks
          Example with 5 annotators, overlap=3:
            Task 1 → A1, A2, A3
            Task 2 → A2, A3, A4
            Task 3 → A3, A4, A5
            Task 4 → A4, A5, A1
            Task 5 → A5, A1, A2
        - Respects capacity limits: Skip annotators at capacity
        - If all annotators at capacity: Hold remaining tasks for later assignment

        Args:
            project: Project instance
            annotators: List of AnnotatorProfile instances (already sorted by score)
            required_overlap: Number of annotators per task (default 3)

        Returns:
            Dict with assignment statistics
        """
        if not annotators:
            logger.warning(f"No annotators available for project {project.id}")
            return {"assigned_tasks": 0, "annotators_used": 0}

        # Use project's required_overlap if not specified
        if required_overlap == 1:  # Default parameter
            required_overlap = getattr(project, "required_overlap", 3)

        logger.info(
            f"Distributing tasks with required_overlap={required_overlap} "
            f"across {len(annotators)} annotators: "
            f"{[a.user.email for a in annotators]}"
        )

        # Get all tasks that need more assignments
        all_tasks = list(
            project.tasks.annotate(assignments_count=Count("annotator_assignments"))
            .filter(assignments_count__lt=required_overlap)
            .order_by("id")
        )

        if not all_tasks:
            logger.info(f"No tasks to assign for project {project.id}")
            return {"assigned_tasks": 0, "annotators_used": 0}

        logger.info(f"Found {len(all_tasks)} tasks needing assignment")

        # Track annotator capacities
        annotator_capacities = {}
        for annotator in annotators:
            capacity_info = AssignmentEngine.check_annotator_capacity(annotator)
            annotator_capacities[annotator.id] = {
                "annotator": annotator,
                "current": capacity_info["current"],
                "maximum": capacity_info["maximum"],
                "available": capacity_info["available"],
            }

        total_assignments = 0
        annotators_used = set()
        tasks_fully_assigned = 0

        # Determine strategy based on annotator count
        num_annotators = len(annotators)

        if num_annotators <= required_overlap:
            # Strategy 1: Assign ALL tasks to ALL annotators (e.g., 50-50-50)
            logger.info(
                f"Using ALL-TO-ALL strategy: {num_annotators} annotators <= {required_overlap} required"
            )

            with transaction.atomic():
                for task in all_tasks:
                    # Get already assigned annotators
                    already_assigned = set(
                        TaskAssignment.objects.filter(task=task).values_list(
                            "annotator_id", flat=True
                        )
                    )

                    assigned_to_task = len(already_assigned)
                    needed = task.target_assignment_count - assigned_to_task

                    if needed <= 0:
                        continue

                    # Try to assign to ALL available annotators
                    for annotator in annotators:
                        if annotator.id in already_assigned:
                            continue

                        capacity = annotator_capacities[annotator.id]
                        if capacity["available"] <= 0:
                            # Refresh capacity
                            capacity_info = AssignmentEngine.check_annotator_capacity(
                                annotator
                            )
                            capacity["available"] = capacity_info["available"]
                            if capacity["available"] <= 0:
                                continue

                        # Create assignment
                        try:
                            assignment = AssignmentEngine._create_task_assignment(
                                annotator, task, project
                            )
                            if assignment:
                                total_assignments += 1
                                assigned_to_task += 1
                                annotators_used.add(annotator.id)
                                capacity["available"] -= 1
                                capacity["current"] += 1
                        except Exception as e:
                            logger.error(
                                f"Error assigning task {task.id} to {annotator.user.email}: {e}"
                            )

                    if assigned_to_task >= task.target_assignment_count:
                        tasks_fully_assigned += 1
        else:
            # Strategy 2: Rotating assignment across annotators
            logger.info(
                f"Using ROTATING strategy: {num_annotators} annotators > {required_overlap} required"
            )

            # Start rotation from index 0
            rotation_index = 0

            with transaction.atomic():
                for task_idx, task in enumerate(all_tasks):
                    # Get already assigned annotators
                    already_assigned = set(
                        TaskAssignment.objects.filter(task=task).values_list(
                            "annotator_id", flat=True
                        )
                    )

                    assigned_to_task = len(already_assigned)
                    needed = task.target_assignment_count - assigned_to_task

                    if needed <= 0:
                        tasks_fully_assigned += 1
                        continue

                    # Try to assign required_overlap annotators using rotation
                    attempts = 0
                    max_attempts = num_annotators * 2  # Prevent infinite loop

                    while (
                        assigned_to_task < task.target_assignment_count
                        and attempts < max_attempts
                    ):
                        # Get next annotator in rotation
                        annotator = annotators[rotation_index % num_annotators]
                        rotation_index += 1
                        attempts += 1

                        # Skip if already assigned
                        if annotator.id in already_assigned:
                            continue

                        # Check capacity
                        capacity = annotator_capacities[annotator.id]
                        if capacity["available"] <= 0:
                            # Refresh capacity
                            capacity_info = AssignmentEngine.check_annotator_capacity(
                                annotator
                            )
                            capacity["available"] = capacity_info["available"]
                            if capacity["available"] <= 0:
                                continue

                        # Create assignment
                        try:
                            assignment = AssignmentEngine._create_task_assignment(
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
                                    f"({assigned_to_task}/{task.target_assignment_count})"
                                )
                        except Exception as e:
                            logger.error(
                                f"Error assigning task {task.id} to {annotator.user.email}: {e}"
                            )

                    if assigned_to_task >= task.target_assignment_count:
                        tasks_fully_assigned += 1
                        # Trigger consolidation check
                        AssignmentEngine._trigger_consolidation_if_ready(task)
                        logger.debug(
                            f"✅ Task {task.id} FULLY assigned ({assigned_to_task}/{task.target_assignment_count})"
                        )
                    elif assigned_to_task > 0:
                        tasks_partially_assigned += 1
                        logger.warning(
                            f"⚠️ Task {task.id} PARTIALLY assigned ({assigned_to_task}/{task.target_assignment_count}) - "
                            f"waiting for more annotators or capacity"
                        )
                    else:
                        tasks_waiting += 1
                        logger.warning(
                            f"⏸️ Task {task.id} NOT assigned (0/{task.target_assignment_count}) - "
                            f"all annotators at capacity"
                        )

        logger.info(
            f"📈 Task distribution complete:\n"
            f"  - Total tasks: {len(all_tasks)}\n"
            f"  - Assignments created: {total_assignments}\n"
            f"  - Annotators used: {len(annotators_used)}\n"
            f"  - Fully assigned (3/3): {tasks_fully_assigned}\n"
            f"  - Partially assigned (<3): {tasks_partially_assigned}\n"
            f"  - Waiting (0): {tasks_waiting}"
        )

        # Mark incomplete tasks for monitoring
        incomplete_count = tasks_partially_assigned + tasks_waiting
        if incomplete_count > 0:
            logger.warning(
                f"🔔 {incomplete_count} tasks need additional annotators. "
                f"Will auto-assign when new annotators become available."
            )

        return {
            "assigned_tasks": len(all_tasks),
            "total_assignments": total_assignments,
            "annotators_used": len(annotators_used),
            "tasks_fully_assigned": tasks_fully_assigned,
            "tasks_partially_assigned": tasks_partially_assigned,
            "tasks_waiting": tasks_waiting,
            "incomplete_tasks": incomplete_count,
        }

    @staticmethod
    def reassign_incomplete_tasks(project):
        """Reassign tasks that have been idle for too long"""
        stale_threshold_assigned = timezone.now() - timedelta(hours=48)
        stale_threshold_in_progress = timezone.now() - timedelta(hours=24)

        stale_assignments = TaskAssignment.objects.filter(
            Q(
                task__project=project,
                status="assigned",
                assigned_at__lt=stale_threshold_assigned,
            )
            | Q(
                task__project=project,
                status="in_progress",
                started_at__lt=stale_threshold_in_progress,
            )
        )

        reassigned = 0

        for assignment in stale_assignments:
            # Mark as skipped
            assignment.status = "skipped"
            assignment.save(update_fields=["status"])

            # Decrease assignment count
            assignment.task.assignment_count = F("assignment_count") - 1
            assignment.task.save(update_fields=["assignment_count"])

            # Find replacement annotator
            replacement = (
                ProjectAssignment.objects.filter(project=project, active=True)
                .exclude(annotator=assignment.annotator)
                .select_related("annotator")
                .first()
            )

            if replacement:
                new_assignment = AssignmentEngine.assign_next_task_to_annotator(
                    project,
                    replacement.annotator,
                )
                if new_assignment:
                    reassigned += 1
                    logger.info(
                        f"Reassigned stale task {assignment.task.id} from "
                        f"{assignment.annotator.user.email} to {replacement.annotator.user.email}"
                    )

        return reassigned

    @staticmethod
    def balance_workload(project):
        """Rebalance task assignments if distribution is uneven"""
        annotators = list(
            ProjectAssignment.objects.filter(
                project=project, active=True
            ).select_related("annotator")
        )

        if len(annotators) < 2:
            return 0

        # Calculate average load
        total_tasks = sum(a.assigned_tasks for a in annotators)
        avg_load = total_tasks / len(annotators)

        # Find overloaded and underloaded annotators
        overloaded = [a for a in annotators if a.assigned_tasks > avg_load * 1.5]
        underloaded = [a for a in annotators if a.assigned_tasks < avg_load * 0.5]

        if not overloaded or not underloaded:
            return 0

        rebalanced = 0

        for overloaded_assignment in overloaded:
            # Get unstarted tasks
            excess_tasks = TaskAssignment.objects.filter(
                annotator=overloaded_assignment.annotator,
                status="assigned",
                task__project=project,
            ).order_by("-assigned_at")[:5]

            for task_assignment in excess_tasks:
                if underloaded:
                    new_annotator_assignment = underloaded[0]

                    # Check capacity
                    capacity = AssignmentEngine.check_annotator_capacity(
                        new_annotator_assignment.annotator
                    )
                    if capacity["at_capacity"]:
                        underloaded.pop(0)
                        continue

                    # Reassign
                    task_assignment.status = "skipped"
                    task_assignment.save()

                    TaskAssignment.objects.create(
                        annotator=new_annotator_assignment.annotator,
                        task=task_assignment.task,
                        status="assigned",
                    )

                    # Update counters
                    overloaded_assignment.assigned_tasks = F("assigned_tasks") - 1
                    overloaded_assignment.save(update_fields=["assigned_tasks"])

                    new_annotator_assignment.assigned_tasks = F("assigned_tasks") + 1
                    new_annotator_assignment.save(update_fields=["assigned_tasks"])

                    rebalanced += 1

                    logger.info(
                        f"Rebalanced task {task_assignment.task.id} from "
                        f"{overloaded_assignment.annotator.user.email} to "
                        f"{new_annotator_assignment.annotator.user.email}"
                    )

        return rebalanced

    @staticmethod
    def auto_assign_on_project_publish(project):
        """Auto-assign annotators and tasks when project is published"""
        logger.info(f"Auto-assigning annotators for project {project.id}")

        # Check if auto-assignment is enabled
        if not getattr(project, "auto_assign", True):
            logger.info(f"Auto-assignment disabled for project {project.id}")
            return []

        # Get required overlap
        required_overlap = getattr(project, "required_overlap", 1)

        # Assign annotators to project
        assignments = AssignmentEngine.assign_annotators_to_project(
            project, required_overlap=required_overlap
        )

        if not assignments:
            logger.warning(f"No annotators available for project {project.id}")
            return []

        # Use improved task distribution algorithm
        AssignmentEngine.distribute_tasks_intelligently(
            project,
            [a.annotator for a in assignments],
            required_overlap=required_overlap,
        )

        logger.info(
            f"Auto-assignment complete for project {project.id}: "
            f"{len(assignments)} annotators assigned with intelligent task distribution"
        )

        return assignments

    @staticmethod
    def calculate_assignment_metrics(project):
        """Calculate metrics for assignment effectiveness"""
        assignments = TaskAssignment.objects.filter(task__project=project)

        total = assignments.count()
        if total == 0:
            return {
                "task_completion_rate": 0,
                "avg_time_to_completion": 0,
                "quality_score": 0,
                "active_annotators": 0,
            }

        completed = assignments.filter(status="completed").count()
        completion_rate = (completed / total * 100) if total > 0 else 0

        # Average completion time
        completed_with_time = assignments.filter(
            status="completed", completed_at__isnull=False, assigned_at__isnull=False
        )

        if completed_with_time.exists():
            times = [
                (a.completed_at - a.assigned_at).total_seconds() / 3600
                for a in completed_with_time
            ]
            avg_time = sum(times) / len(times)
        else:
            avg_time = 0

        # Quality score
        quality_assignments = assignments.filter(quality_score__isnull=False)
        avg_quality = (
            quality_assignments.aggregate(Avg("quality_score"))["quality_score__avg"]
            or 0
        )

        # Active annotators
        active_annotators = ProjectAssignment.objects.filter(
            project=project, active=True
        ).count()

        return {
            "task_completion_rate": round(completion_rate, 2),
            "avg_time_to_completion": round(avg_time, 2),
            "quality_score": round(float(avg_quality), 2),
            "active_annotators": active_annotators,
            "total_assignments": total,
            "completed_assignments": completed,
        }


# =============================================================================
# DYNAMIC OVERLAP ASSIGNMENT SYSTEM
# =============================================================================
# This section implements the new algorithm that dynamically adjusts overlap
# based on available annotators:
# - 0 annotators: Hold tasks
# - 1-2 annotators: Overlap = annotator count
# - 3+ annotators: Overlap = 3 (max)
# =============================================================================

# Constants for assignment system
ASSIGNMENT_TIMEOUT_HOURS = 48  # How long before assignment times out
INACTIVITY_THRESHOLD_DAYS = 7  # Mark annotator inactive after this many days
MAX_OVERLAP = 3  # Maximum overlap (hard limit)
# Trust level priority for ranking (higher = better priority)
TRUST_LEVEL_PRIORITY = {
    "expert": 5,
    "senior": 4,
    "regular": 3,
    "junior": 2,
    "new": 1,
}

MIN_OVERLAP = 1  # Minimum overlap when annotators exist


class DynamicAssignmentEngine:
    """
    Dynamic assignment engine that adjusts overlap based on available annotators.
    
    This implements the three main cases:
    1. No annotators (0): Hold tasks
    2. Limited annotators (1-2): Adjust overlap to match count
    3. Sufficient annotators (3+): Use max overlap of 3
    
    Distribution Strategy (3+ annotators):
    - Annotators are ranked by trust level (expert > senior > regular > junior > new)
    - Tasks are distributed across ALL eligible annotators (not just top 3)
    - Higher trust annotators get priority but work is balanced for speed
    - This ensures quality while achieving faster completion
    """
    
    @classmethod
    def get_eligible_annotators(cls, project, sort_by_trust=True):
        """
        Get all annotators eligible for this project.
        
        Eligibility Criteria:
        1. Status = 'approved'
        2. User is active
        3. Not suspended (fraud_flags < 3)
        4. Has available capacity
        5. Active for assignments (not marked inactive)
        6. Has not already annotated ALL tasks in the project
        
        Note: Trust level is NOT checked (clients cannot configure this)
        
        Args:
            project: Project instance
            sort_by_trust: If True, sort by trust level (higher first)
            
        Returns:
            List of AnnotatorProfile instances that are eligible, sorted by trust level
        """
        from .models import AnnotatorProfile, TrustLevel
        
        # Base query: approved, active users who are active for assignments
        eligible = AnnotatorProfile.objects.filter(
            status='approved',
            user__is_active=True,
            is_active_for_assignments=True,
        ).select_related('user', 'trust_level')
        
        # Exclude suspended annotators (fraud_flags >= 3 or is_suspended)
        eligible = eligible.filter(
            models.Q(trust_level__isnull=True) |
            models.Q(trust_level__fraud_flags__lt=3, trust_level__is_suspended=False)
        )
        
        # Convert to list for capacity filtering
        eligible_list = list(eligible)
        
        # Filter by capacity - only include annotators with available capacity
        eligible_with_capacity = []
        for annotator in eligible_list:
            capacity_info = AssignmentEngine.check_annotator_capacity(annotator)
            if not capacity_info['at_capacity']:
                eligible_with_capacity.append(annotator)
        
        # Filter out annotators who have already been assigned to ALL tasks
        # (they have no more tasks to work on in this project)
        total_tasks = project.tasks.count()
        if total_tasks > 0:
            final_eligible = []
            for annotator in eligible_with_capacity:
                assigned_count = TaskAssignment.objects.filter(
                    annotator=annotator,
                    task__project=project,
                ).count()
                if assigned_count < total_tasks:
                    final_eligible.append(annotator)
            result = final_eligible
        else:
            result = eligible_with_capacity
        
        # Sort by trust level if requested (higher priority first)
        if sort_by_trust:
            result = cls._sort_by_trust_level(result)
        
        return result
    
    @classmethod
    def _sort_by_trust_level(cls, annotators):
        """
        Sort annotators by trust level (higher trust = higher priority).
        
        Priority order: expert > senior > regular > junior > new
        
        Args:
            annotators: List of AnnotatorProfile instances
            
        Returns:
            Sorted list with highest trust first
        """
        def get_priority(annotator):
            try:
                level = annotator.trust_level.level if annotator.trust_level else "new"
            except:
                level = "new"
            return TRUST_LEVEL_PRIORITY.get(level, 1)
        
        return sorted(annotators, key=get_priority, reverse=True)
    
    @classmethod
    def calculate_effective_overlap(cls, eligible_count):
        """
        Calculate the effective overlap based on available annotators.
        
        Rules:
        - If eligible_count == 0: Return None (hold tasks)
        - If eligible_count < 3: Return eligible_count
        - If eligible_count >= 3: Return 3 (max overlap)
        
        Args:
            eligible_count: Number of eligible annotators
            
        Returns:
            int or None: Effective overlap, or None if should hold
        """
        if eligible_count == 0:
            return None  # Signal to hold tasks
        
        # Effective overlap = min(available, max_overlap)
        return min(eligible_count, MAX_OVERLAP)
    
    @classmethod
    @transaction.atomic
    def assign_tasks_with_dynamic_overlap(cls, project):
        """
        Main assignment algorithm with dynamic overlap.
        
        Steps:
        1. Get eligible annotators
        2. Calculate effective overlap
        3. Handle the three cases
        4. Update task target_assignment_count
        5. Distribute tasks fairly
        
        Args:
            project: Project instance
            
        Returns:
            dict with assignment results
        """
        from tasks.models import Task
        
        logger.info(f"[DynamicAssignment] Starting for project {project.id}")
        
        # Step 1: Get eligible annotators
        eligible = cls.get_eligible_annotators(project)
        eligible_count = len(eligible)
        
        logger.info(f"[DynamicAssignment] Found {eligible_count} eligible annotators")
        
        # CASE 1: No eligible annotators - hold all tasks
        if eligible_count == 0:
            logger.warning(
                f"[DynamicAssignment] No eligible annotators for project {project.id}. "
                "Tasks will be held."
            )
            return {
                'status': 'waiting',
                'message': 'No eligible annotators available. Tasks on hold.',
                'eligible_count': 0,
                'effective_overlap': None,
                'assigned_count': 0,
                'tasks_pending': project.tasks.count(),
            }
        
        # Step 2: Calculate effective overlap
        effective_overlap = cls.calculate_effective_overlap(eligible_count)
        
        logger.info(
            f"[DynamicAssignment] Effective overlap: {effective_overlap} "
            f"(from {eligible_count} annotators)"
        )
        
        # Step 3: Update task target_assignment_count for tasks that need it
        # Only update tasks that have a higher target than current effective overlap
        # Never reduce target below current active assignments
        tasks_updated = cls._update_task_overlaps(project, effective_overlap)
        
        # Step 4: Distribute tasks based on case
        if eligible_count < MAX_OVERLAP:
            # CASE 2: Limited annotators (1-2)
            # Assign all unassigned tasks to all available annotators
            assigned_count = cls._assign_all_to_all(project, eligible, effective_overlap)
            status = 'partial'
            message = f"Limited annotators ({eligible_count}). Overlap set to {effective_overlap}."
        else:
            # CASE 3: Sufficient annotators (3+)
            # Use rotation to distribute tasks fairly
            assigned_count = cls._distribute_with_rotation(project, eligible, effective_overlap)
            status = 'complete'
            message = f"Full overlap ({effective_overlap}) with {eligible_count} annotators."
        
        # Calculate pending tasks
        tasks_needing_assignment = Task.objects.filter(
            project=project,
        ).annotate(
            active_assignments=Count(
                'annotator_assignments',
                filter=models.Q(annotator_assignments__status__in=['assigned', 'in_progress', 'completed'])
            )
        ).filter(
            active_assignments__lt=models.F('target_assignment_count')
        ).count()
        
        result = {
            'status': status,
            'message': message,
            'eligible_count': eligible_count,
            'effective_overlap': effective_overlap,
            'assigned_count': assigned_count,
            'tasks_updated': tasks_updated,
            'tasks_pending': tasks_needing_assignment,
        }
        
        logger.info(f"[DynamicAssignment] Complete: {result}")
        return result
    
    @classmethod
    def _update_task_overlaps(cls, project, effective_overlap):
        """
        Update task target_assignment_count based on effective overlap.
        
        Only updates tasks where:
        - Current target is different from effective overlap
        - Current active assignments < effective overlap
        
        Never reduces target below current active assignments.
        """
        from tasks.models import Task
        
        updated = 0
        tasks = project.tasks.all()
        
        for task in tasks:
            active_count = task.annotator_assignments.filter(
                status__in=['assigned', 'in_progress', 'completed']
            ).count()
            
            # Don't reduce below current active assignments
            new_target = max(effective_overlap, active_count)
            
            if task.target_assignment_count != new_target:
                task.target_assignment_count = new_target
                task.save(update_fields=['target_assignment_count'])
                updated += 1
        
        if updated > 0:
            logger.info(
                f"[DynamicAssignment] Updated target_assignment_count for {updated} tasks "
                f"to {effective_overlap}"
            )
        
        return updated
    
    @classmethod
    def _assign_all_to_all(cls, project, annotators, effective_overlap):
        """
        Assign ALL tasks to ALL available annotators.
        
        Used when annotators <= effective_overlap.
        Each annotator gets assigned to every task they haven't been assigned to yet.
        
        Returns count of new assignments created.
        """
        from tasks.models import Task
        
        assignments_created = 0
        
        tasks = project.tasks.all()
        
        for task in tasks:
            # Get already assigned annotators for this task
            already_assigned_ids = set(
                TaskAssignment.objects.filter(task=task).values_list('annotator_id', flat=True)
            )
            
            # Count active assignments
            active_count = TaskAssignment.objects.filter(
                task=task,
                status__in=['assigned', 'in_progress', 'completed']
            ).count()
            
            # Check if task needs more assignments
            if active_count >= task.target_assignment_count:
                continue
            
            needed = task.target_assignment_count - active_count
            
            for annotator in annotators:
                if needed <= 0:
                    break
                    
                if annotator.id in already_assigned_ids:
                    continue
                
                # Check if annotator can work on this task
                can_work, reason = cls._can_annotator_work_on_task(annotator, task)
                if not can_work:
                    logger.debug(f"Annotator {annotator.id} cannot work on task {task.id}: {reason}")
                    continue
                
                # Check capacity limit based on trust level
                capacity = AssignmentEngine.check_annotator_capacity(annotator)
                if capacity['at_capacity']:
                    logger.debug(
                        f"Annotator {annotator.id} at capacity ({capacity['current']}/{capacity['maximum']})"
                    )
                    continue
                
                # Create the assignment
                try:
                    assignment = cls._safe_create_assignment(annotator, task, project)
                    if assignment:
                        assignments_created += 1
                        needed -= 1
                        already_assigned_ids.add(annotator.id)
                except Exception as e:
                    logger.error(f"Error creating assignment: {e}")
        
        return assignments_created
    
    @classmethod
    def _distribute_with_rotation(cls, project, annotators, effective_overlap):
        """
        Distribute tasks using priority-weighted rotation.
        
        Used when annotators > effective_overlap (3+).
        
        Strategy:
        - Annotators are pre-sorted by trust level (expert > senior > regular > junior > new)
        - For each task, we select annotators in priority order
        - But we also consider current workload to balance speed
        - Higher trust annotators get priority but work spreads across ALL annotators
        
        This ensures:
        - Quality: Higher trust annotators work on more tasks
        - Speed: Work is distributed across all annotators for faster completion
        - Balance: No single annotator gets overwhelmed
        
        Returns count of new assignments created.
        """
        from tasks.models import Task
        
        assignments_created = 0
        
        # Get tasks needing assignment
        tasks = list(
            project.tasks.annotate(
                active_count=Count(
                    'annotator_assignments',
                    filter=models.Q(annotator_assignments__status__in=['assigned', 'in_progress', 'completed'])
                )
            ).filter(
                active_count__lt=models.F('target_assignment_count')
            ).order_by('id')
        )
        
        if not tasks:
            return 0
        
        # Build annotator list (already sorted by trust level)
        annotator_list = list(annotators)
        num_annotators = len(annotator_list)
        
        # Track current assignments per annotator for load balancing
        annotator_load = {a.id: 0 for a in annotator_list}
        
        for task in tasks:
            # Get already assigned annotators for this task
            already_assigned_ids = set(
                TaskAssignment.objects.filter(task=task).values_list('annotator_id', flat=True)
            )
            
            active_count = task.active_count
            needed = task.target_assignment_count - active_count
            
            # Get candidates sorted by priority score
            # Score = trust_priority * 10 - current_load (higher = better)
            # This prioritizes high trust but balances workload
            candidates = []
            for annotator in annotator_list:
                if annotator.id in already_assigned_ids:
                    continue
                
                # Check if can work and has capacity
                can_work, _ = cls._can_annotator_work_on_task(annotator, task)
                if not can_work:
                    continue
                
                capacity = AssignmentEngine.check_annotator_capacity(annotator)
                if capacity['at_capacity']:
                    continue
                
                # Calculate priority score
                try:
                    level = annotator.trust_level.level if annotator.trust_level else "new"
                except:
                    level = "new"
                trust_priority = TRUST_LEVEL_PRIORITY.get(level, 1)
                
                # Score balances trust priority with workload
                # Multiply trust by 10 to make it dominant, subtract load for balance
                score = (trust_priority * 10) - annotator_load.get(annotator.id, 0)
                
                candidates.append((annotator, score))
            
            # Sort candidates by score (higher = better)
            candidates.sort(key=lambda x: x[1], reverse=True)
            
            # Assign to top candidates
            for annotator, score in candidates[:needed]:
                try:
                    assignment = cls._safe_create_assignment(annotator, task, project)
                    if assignment:
                        assignments_created += 1
                        annotator_load[annotator.id] = annotator_load.get(annotator.id, 0) + 1
                        needed -= 1
                except Exception as e:
                    logger.error(f"Error creating assignment: {e}")
        
        # Log distribution summary
        if assignments_created > 0:
            load_summary = {
                a.user.email: annotator_load[a.id] 
                for a in annotator_list if annotator_load[a.id] > 0
            }
            logger.info(
                f"[DynamicAssignment] Distributed {assignments_created} assignments. "
                f"Load distribution: {load_summary}"
            )
        
        return assignments_created
    
    @classmethod
    def _can_annotator_work_on_task(cls, annotator, task):
        """
        Check if annotator can work on a specific task.
        
        Prevents:
        - Duplicate assignments
        - Re-annotation of already annotated tasks
        
        Returns:
            tuple: (can_work: bool, reason: str or None)
        """
        from tasks.models import Annotation
        
        # Check if they already have ANY annotation on this task
        existing_annotation = Annotation.objects.filter(
            task=task,
            completed_by=annotator.user
        ).exists()
        
        if existing_annotation:
            return False, "Annotator already has annotation on this task"
        
        # Check if they had a completed assignment
        completed_assignment = TaskAssignment.objects.filter(
            task=task,
            annotator=annotator,
            status='completed'
        ).exists()
        
        if completed_assignment:
            return False, "Annotator already completed this task"
        
        return True, None
    
    @classmethod
    @transaction.atomic
    def _safe_create_assignment(cls, annotator, task, project):
        """
        Safely create a task assignment with proper locking.
        
        Uses database-level locking to prevent race conditions.
        """
        from tasks.models import Task as TaskModel
        
        # Lock the task row to prevent concurrent assignments
        task = TaskModel.objects.select_for_update().get(id=task.id)
        
        # Double-check assignment doesn't exist
        if TaskAssignment.objects.filter(task=task, annotator=annotator).exists():
            logger.debug(f"Assignment already exists for task {task.id}, annotator {annotator.id}")
            return None
        
        # Check if task is fully covered
        current = task.annotator_assignments.filter(
            status__in=['assigned', 'in_progress', 'completed']
        ).count()
        
        if current >= task.target_assignment_count:
            logger.debug(f"Task {task.id} is fully covered ({current}/{task.target_assignment_count})")
            return None
        
        # Create the assignment using existing helper
        assignment = AssignmentEngine._create_task_assignment(annotator, task, project)
        
        return assignment
    
    @classmethod
    def handle_assignment_timeout(cls, assignment):
        """
        Handle assignment timeout with activity-based logic.
        
        Logic:
        1. If annotator was active since assignment: Extend timer
        2. If annotator inactive for > INACTIVITY_THRESHOLD_DAYS: Mark inactive, release all
        3. Otherwise: Release just this assignment
        
        Args:
            assignment: TaskAssignment instance
        """
        annotator = assignment.annotator
        now = timezone.now()
        
        # Check if annotator has been active since assignment was created
        if annotator.last_active and annotator.last_active > assignment.assigned_at:
            # Annotator is active, just hasn't reached this task yet
            # Reset the timer by updating assigned_at
            assignment.assigned_at = now
            assignment.save(update_fields=['assigned_at'])
            logger.info(
                f"[Timeout] Extended timeout for active annotator {annotator.id} on task {assignment.task_id}"
            )
            return 'extended'
        
        # Check for prolonged inactivity
        inactivity_cutoff = now - timedelta(days=INACTIVITY_THRESHOLD_DAYS)
        
        if not annotator.last_active or annotator.last_active < inactivity_cutoff:
            # Annotator hasn't been active for too long
            logger.warning(
                f"[Timeout] Marking annotator {annotator.id} as inactive due to prolonged absence "
                f"(last active: {annotator.last_active})"
            )
            cls._mark_annotator_inactive(annotator)
            cls._release_all_pending_assignments(annotator)
            return 'marked_inactive'
        
        # Normal timeout - release just this assignment
        cls._release_assignment(assignment)
        
        # Trigger reassignment for this task
        cls._trigger_task_reassignment(assignment.task)
        
        return 'released'
    
    @classmethod
    def _mark_annotator_inactive(cls, annotator):
        """Mark annotator as inactive - they won't receive new tasks until login"""
        annotator.mark_inactive()
        logger.info(f"[Inactive] Annotator {annotator.id} marked as inactive")
    
    @classmethod
    def _release_all_pending_assignments(cls, annotator):
        """Release all pending assignments for an annotator"""
        pending = TaskAssignment.objects.filter(
            annotator=annotator,
            status__in=['assigned', 'in_progress']
        )
        
        count = pending.count()
        
        for assignment in pending:
            cls._release_assignment(assignment)
            cls._trigger_task_reassignment(assignment.task)
        
        logger.info(f"[Inactive] Released {count} pending assignments for annotator {annotator.id}")
    
    @classmethod
    def _release_assignment(cls, assignment):
        """Release a single assignment"""
        assignment.status = 'expired'
        assignment.save(update_fields=['status'])
        
        # Decrement task counter
        from django.db.models import F
        assignment.task.assignment_count = F('assignment_count') - 1
        assignment.task.save(update_fields=['assignment_count'])
    
    @classmethod
    def _trigger_task_reassignment(cls, task):
        """Trigger reassignment for a single task"""
        project = task.project
        eligible = cls.get_eligible_annotators(project)
        
        if not eligible:
            logger.warning(f"[Reassign] No eligible annotators for task {task.id}")
            return
        
        # Get already assigned annotators
        already_assigned_ids = set(
            TaskAssignment.objects.filter(
                task=task,
                status__in=['assigned', 'in_progress', 'completed']
            ).values_list('annotator_id', flat=True)
        )
        
        # Find available annotator
        for annotator in eligible:
            if annotator.id in already_assigned_ids:
                continue
            
            can_work, _ = cls._can_annotator_work_on_task(annotator, task)
            if not can_work:
                continue
            
            capacity = AssignmentEngine.check_annotator_capacity(annotator)
            if capacity['at_capacity']:
                continue
            
            # Create assignment
            try:
                cls._safe_create_assignment(annotator, task, project)
                logger.info(f"[Reassign] Reassigned task {task.id} to annotator {annotator.id}")
                return
            except Exception as e:
                logger.error(f"[Reassign] Error reassigning task {task.id}: {e}")
        
        logger.warning(f"[Reassign] Could not find available annotator for task {task.id}")
    
    @classmethod
    def check_and_process_timeouts(cls, project=None):
        """
        Check for timed out assignments and process them.
        
        Args:
            project: Optional - only check assignments for this project
        """
        timeout_cutoff = timezone.now() - timedelta(hours=ASSIGNMENT_TIMEOUT_HOURS)
        
        queryset = TaskAssignment.objects.filter(
            status='assigned',
            assigned_at__lt=timeout_cutoff
        ).select_related('annotator', 'task', 'task__project')
        
        if project:
            queryset = queryset.filter(task__project=project)
        
        count = 0
        for assignment in queryset:
            cls.handle_assignment_timeout(assignment)
            count += 1
        
        if count > 0:
            logger.info(f"[Timeout] Processed {count} timed out assignments")
        
        return count
    
    @classmethod
    def on_annotator_approved(cls, annotator):
        """
        Called when an annotator is approved.
        Checks for projects that need more annotators and assigns if eligible.
        """
        from projects.models import Project
        
        logger.info(f"[NewAnnotator] Checking work for newly approved annotator {annotator.id}")
        
        # Find published projects
        projects = Project.objects.filter(is_published=True)
        
        assignments_made = 0
        for project in projects:
            # Check if annotator is eligible for this project
            eligible = cls.get_eligible_annotators(project)
            if annotator not in eligible:
                continue
            
            # Run assignment for this project
            result = cls.assign_tasks_with_dynamic_overlap(project)
            assignments_made += result.get('assigned_count', 0)
        
        logger.info(
            f"[NewAnnotator] Annotator {annotator.id} assigned to {assignments_made} tasks"
        )
        return assignments_made
    
    @classmethod
    def on_annotator_suspended(cls, annotator):
        """
        Called when an annotator is suspended.
        Releases their pending assignments and reassigns them.
        """
        logger.info(f"[Suspended] Processing suspended annotator {annotator.id}")
        cls._release_all_pending_assignments(annotator)
    
    @classmethod
    def on_task_completed(cls, assignment):
        """
        Called when an annotator completes a task assignment.
        Checks if more work is available for this annotator.
        """
        project = assignment.task.project
        annotator = assignment.annotator
        
        # Update last active
        annotator.update_last_active()
        
        # Check for more work
        capacity = AssignmentEngine.check_annotator_capacity(annotator)
        if capacity['at_capacity']:
            return
        
        # Try to assign next task
        eligible = cls.get_eligible_annotators(project)
        if annotator in eligible:
            result = cls.assign_tasks_with_dynamic_overlap(project)
            logger.info(
                f"[TaskComplete] Post-completion assignment for annotator {annotator.id}: "
                f"{result.get('assigned_count', 0)} new tasks"
            )
