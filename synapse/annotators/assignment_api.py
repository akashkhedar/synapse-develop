"""
Assignment Management API endpoints for projects.

These endpoints allow clients to:
- Manually assign annotators to projects
- Trigger auto-assignment
- View assignment status and configuration
- Reassign tasks
"""

import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from projects.models import Project
from annotators.models import AnnotatorProfile, ProjectAssignment, TaskAssignment
from annotators.assignment_engine import AssignmentEngine

logger = logging.getLogger(__name__)


class ProjectAssignAnnotatorsAPI(APIView):
    """
    Manually assign specific annotators to a project.

    POST /api/projects/{project_id}/assign-annotators/

    Request body:
    {
        "annotator_ids": [1, 2, 3],
        "role": "annotator" | "reviewer"
    }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, project_id):
        project = get_object_or_404(Project, pk=project_id)

        # Check user has permission to manage this project
        if not request.user.is_superuser:
            if project.organization_id != getattr(
                request.user.active_organization, "id", None
            ):
                return Response(
                    {"error": "You don't have permission to manage this project"},
                    status=status.HTTP_403_FORBIDDEN,
                )

        annotator_ids = request.data.get("annotator_ids", [])
        role = request.data.get("role", "annotator")

        if not annotator_ids:
            return Response(
                {"error": "annotator_ids is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if role not in ["annotator", "reviewer"]:
            return Response(
                {"error": "role must be 'annotator' or 'reviewer'"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            annotators = AnnotatorProfile.objects.filter(
                id__in=annotator_ids, status="approved"
            )

            if not annotators.exists():
                return Response(
                    {"error": "No valid approved annotators found"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            assignments_created = []
            for annotator in annotators:
                assignment, created = ProjectAssignment.objects.get_or_create(
                    annotator=annotator,
                    project=project,
                    defaults={"role": role, "active": True},
                )
                if created:
                    assignments_created.append(
                        {
                            "annotator_id": annotator.id,
                            "annotator_email": annotator.user.email,
                            "role": role,
                        }
                    )

            return Response(
                {
                    "success": True,
                    "message": f"Assigned {len(assignments_created)} annotators to project",
                    "assignments": assignments_created,
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            logger.error(f"Error assigning annotators to project {project_id}: {e}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProjectAutoAssignAPI(APIView):
    """
    Trigger automatic assignment for a project.

    POST /api/projects/{project_id}/auto-assign/

    Request body (optional):
    {
        "count": 5,  # Number of annotators to assign (optional)
        "strategy": "score_based" | "round_robin" | "random"
    }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, project_id):
        project = get_object_or_404(Project, pk=project_id)

        # Check permission
        if not request.user.is_superuser:
            if project.organization_id != getattr(
                request.user.active_organization, "id", None
            ):
                return Response(
                    {"error": "You don't have permission to manage this project"},
                    status=status.HTTP_403_FORBIDDEN,
                )

        count = request.data.get("count")
        strategy = request.data.get("strategy", "score_based")

        try:
            # Use the assignment engine
            result = AssignmentEngine.assign_annotators_to_project(
                project=project, count=count, strategy=strategy
            )

            return Response(
                {
                    "success": True,
                    "message": "Auto-assignment triggered successfully",
                    "result": result,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error in auto-assignment for project {project_id}: {e}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProjectAssignmentStatusAPI(APIView):
    """
    Get the current assignment status for a project.

    GET /api/projects/{project_id}/assignment-status/

    Returns:
    - Number of assigned annotators
    - Assignment details
    - Task distribution stats
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        project = get_object_or_404(Project, pk=project_id)

        try:
            # Get project assignments
            assignments = ProjectAssignment.objects.filter(
                project=project, active=True
            ).select_related("annotator", "annotator__user")

            # Get task assignment stats
            task_stats = {}
            for assignment in assignments:
                annotator_id = assignment.annotator.id
                task_counts = (
                    TaskAssignment.objects.filter(
                        annotator=assignment.annotator, task__project=project
                    )
                    .values("status")
                    .annotate(count=models.Count("id"))
                )
                task_stats[annotator_id] = {
                    item["status"]: item["count"] for item in task_counts
                }

            return Response(
                {
                    "project_id": project_id,
                    "project_title": project.title,
                    "is_published": project.is_published,
                    "total_tasks": project.tasks.count(),
                    "total_assigned_annotators": assignments.count(),
                    "assignments": [
                        {
                            "annotator_id": a.annotator.id,
                            "annotator_email": a.annotator.user.email,
                            "annotator_name": a.annotator.user.get_full_name(),
                            "role": a.role,
                            "assigned_at": a.assigned_at.isoformat(),
                            "task_stats": task_stats.get(a.annotator.id, {}),
                        }
                        for a in assignments
                    ],
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(
                f"Error getting assignment status for project {project_id}: {e}"
            )
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProjectAssignmentConfigAPI(APIView):
    """
    Get or update assignment configuration for a project.

    GET /api/projects/{project_id}/assignment-config/
    POST /api/projects/{project_id}/assignment-config/

    Configuration includes:
    - auto_assign_enabled
    - max_annotators
    - min_trust_level
    - required_skills
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        project = get_object_or_404(Project, pk=project_id)

        return Response(
            {
                "project_id": project_id,
                "auto_assign_enabled": getattr(project, "auto_assign_enabled", True),
                "max_annotators": getattr(project, "max_annotators", None),
                "min_trust_level": getattr(project, "min_trust_level", None),
                "required_skills": getattr(project, "required_skills", []),
                "maximum_annotations": project.maximum_annotations,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request, project_id):
        project = get_object_or_404(Project, pk=project_id)

        # Check permission
        if not request.user.is_superuser:
            if project.organization_id != getattr(
                request.user.active_organization, "id", None
            ):
                return Response(
                    {"error": "You don't have permission to manage this project"},
                    status=status.HTTP_403_FORBIDDEN,
                )

        data = request.data
        updated_fields = []

        if "auto_assign_enabled" in data:
            project.auto_assign_enabled = data["auto_assign_enabled"]
            updated_fields.append("auto_assign_enabled")

        if "max_annotators" in data:
            project.max_annotators = data["max_annotators"]
            updated_fields.append("max_annotators")

        if "min_trust_level" in data:
            project.min_trust_level = data["min_trust_level"]
            updated_fields.append("min_trust_level")

        if "required_skills" in data:
            project.required_skills = data["required_skills"]
            updated_fields.append("required_skills")

        if updated_fields:
            try:
                project.save(update_fields=updated_fields)
            except Exception:
                # Some fields might not exist on the model, save without update_fields
                project.save()

        return Response(
            {
                "success": True,
                "message": "Assignment configuration updated",
                "updated_fields": updated_fields,
            },
            status=status.HTTP_200_OK,
        )


class ProjectReassignTasksAPI(APIView):
    """
    Reassign tasks within a project.

    POST /api/projects/{project_id}/reassign-tasks/

    Actions:
    - Reassign incomplete tasks to available annotators
    - Rebalance workload across annotators
    - Reassign tasks from specific annotator
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, project_id):
        project = get_object_or_404(Project, pk=project_id)

        # Check permission
        if not request.user.is_superuser:
            if project.organization_id != getattr(
                request.user.active_organization, "id", None
            ):
                return Response(
                    {"error": "You don't have permission to manage this project"},
                    status=status.HTTP_403_FORBIDDEN,
                )

        action = request.data.get("action", "rebalance")
        from_annotator_id = request.data.get("from_annotator_id")
        to_annotator_id = request.data.get("to_annotator_id")

        try:
            if action == "reassign_from":
                # Reassign all tasks from a specific annotator
                if not from_annotator_id:
                    return Response(
                        {
                            "error": "from_annotator_id is required for reassign_from action"
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                tasks_reassigned = TaskAssignment.objects.filter(
                    annotator_id=from_annotator_id,
                    task__project=project,
                    status__in=["assigned", "in_progress"],
                )

                if to_annotator_id:
                    # Reassign to specific annotator
                    tasks_reassigned.update(
                        annotator_id=to_annotator_id, status="assigned"
                    )
                    count = tasks_reassigned.count()
                else:
                    # Remove assignments (tasks will be unassigned)
                    count = tasks_reassigned.count()
                    tasks_reassigned.delete()

                return Response(
                    {
                        "success": True,
                        "message": f"Reassigned {count} tasks",
                        "action": action,
                    },
                    status=status.HTTP_200_OK,
                )

            elif action == "rebalance":
                # Rebalance workload across all annotators
                result = AssignmentEngine.balance_project_workload(project)

                return Response(
                    {
                        "success": True,
                        "message": "Workload rebalanced",
                        "result": result,
                    },
                    status=status.HTTP_200_OK,
                )

            elif action == "reassign_stale":
                # Reassign stale tasks (assigned but not started for a while)
                hours_threshold = request.data.get("hours_threshold", 24)
                result = AssignmentEngine.reassign_stale_tasks(project, hours_threshold)

                return Response(
                    {
                        "success": True,
                        "message": f"Reassigned stale tasks (>{hours_threshold}h)",
                        "result": result,
                    },
                    status=status.HTTP_200_OK,
                )

            else:
                return Response(
                    {"error": f"Unknown action: {action}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except Exception as e:
            logger.error(f"Error reassigning tasks for project {project_id}: {e}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# Import models for type hints
from django.db import models





