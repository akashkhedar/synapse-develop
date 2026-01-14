"""
Honeypot Management API endpoints.

Provides CRUD operations for honeypot tasks and project configuration.
"""

import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers
from django.shortcuts import get_object_or_404

from projects.models import Project
from tasks.models import Task
from .models import HoneypotTask
from .honeypot_service import HoneypotService

logger = logging.getLogger(__name__)


class HoneypotTaskSerializer(serializers.ModelSerializer):
    """Serializer for HoneypotTask model"""

    task_id = serializers.IntegerField(source="task.id", read_only=True)
    task_data = serializers.SerializerMethodField()
    pass_rate = serializers.SerializerMethodField()

    class Meta:
        model = HoneypotTask
        fields = [
            "id",
            "task_id",
            "task_data",
            "ground_truth",
            "tolerance",
            "is_active",
            "times_shown",
            "times_passed",
            "times_failed",
            "pass_rate",
            "created_at",
        ]
        read_only_fields = ["times_shown", "times_passed", "times_failed", "created_at"]

    def get_task_data(self, obj):
        return obj.task.data if obj.task else None

    def get_pass_rate(self, obj):
        if obj.times_shown == 0:
            return None
        return round((obj.times_passed / obj.times_shown) * 100, 1)


class HoneypotCreateSerializer(serializers.Serializer):
    """Serializer for creating a honeypot"""

    task_id = serializers.IntegerField(required=True)
    ground_truth = serializers.JSONField(required=True)
    tolerance = serializers.FloatField(required=False, default=0.8)

    def validate_task_id(self, value):
        project_id = self.context.get("project_id")
        if not Task.objects.filter(id=value, project_id=project_id).exists():
            raise serializers.ValidationError("Task not found in this project")
        return value

    def validate_tolerance(self, value):
        if not 0 <= value <= 1:
            raise serializers.ValidationError("Tolerance must be between 0 and 1")
        return value


class HoneypotConfigSerializer(serializers.Serializer):
    """Serializer for project honeypot configuration"""

    honeypot_enabled = serializers.BooleanField(required=False)
    honeypot_injection_rate = serializers.FloatField(required=False)
    honeypot_min_interval = serializers.IntegerField(required=False)
    honeypot_failure_threshold = serializers.IntegerField(required=False)

    def validate_honeypot_injection_rate(self, value):
        if not 0 <= value <= 1:
            raise serializers.ValidationError("Injection rate must be between 0 and 1")
        return value

    def validate_honeypot_min_interval(self, value):
        if value < 1:
            raise serializers.ValidationError("Minimum interval must be at least 1")
        return value

    def validate_honeypot_failure_threshold(self, value):
        if value < 1:
            raise serializers.ValidationError("Failure threshold must be at least 1")
        return value


class ProjectHoneypotsAPI(APIView):
    """
    List and create honeypot tasks for a project.

    GET /api/projects/{project_id}/honeypots/
    POST /api/projects/{project_id}/honeypots/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        """List all honeypot tasks for a project"""
        project = get_object_or_404(Project, id=project_id)

        # Check permission
        if not project.has_permission(request.user):
            return Response(
                {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        honeypots = (
            HoneypotTask.objects.filter(task__project=project)
            .select_related("task")
            .order_by("-created_at")
        )

        # Filter by active status if specified
        active_only = request.query_params.get("active")
        if active_only == "true":
            honeypots = honeypots.filter(is_active=True)
        elif active_only == "false":
            honeypots = honeypots.filter(is_active=False)

        serializer = HoneypotTaskSerializer(honeypots, many=True)

        return Response(
            {
                "count": honeypots.count(),
                "honeypots": serializer.data,
            }
        )

    def post(self, request, project_id):
        """Create a new honeypot task"""
        project = get_object_or_404(Project, id=project_id)

        # Check permission
        if not project.has_permission(request.user):
            return Response(
                {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        serializer = HoneypotCreateSerializer(
            data=request.data, context={"project_id": project_id}
        )

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        task = Task.objects.get(id=serializer.validated_data["task_id"])

        honeypot = HoneypotService.create_honeypot(
            task=task,
            ground_truth=serializer.validated_data["ground_truth"],
            tolerance=serializer.validated_data.get("tolerance", 0.8),
            created_by=request.user,
        )

        return Response(
            HoneypotTaskSerializer(honeypot).data, status=status.HTTP_201_CREATED
        )


class ProjectHoneypotDetailAPI(APIView):
    """
    Get, update, or delete a specific honeypot task.

    GET /api/projects/{project_id}/honeypots/{honeypot_id}/
    PUT /api/projects/{project_id}/honeypots/{honeypot_id}/
    DELETE /api/projects/{project_id}/honeypots/{honeypot_id}/
    """

    permission_classes = [IsAuthenticated]

    def get_honeypot(self, project_id, honeypot_id, user):
        """Get honeypot with permission check"""
        project = get_object_or_404(Project, id=project_id)

        if not project.has_permission(user):
            return None, Response(
                {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        honeypot = get_object_or_404(
            HoneypotTask, id=honeypot_id, task__project=project
        )

        return honeypot, None

    def get(self, request, project_id, honeypot_id):
        """Get honeypot details"""
        honeypot, error = self.get_honeypot(project_id, honeypot_id, request.user)
        if error:
            return error

        return Response(HoneypotTaskSerializer(honeypot).data)

    def put(self, request, project_id, honeypot_id):
        """Update a honeypot"""
        honeypot, error = self.get_honeypot(project_id, honeypot_id, request.user)
        if error:
            return error

        # Update allowed fields
        if "ground_truth" in request.data:
            honeypot.ground_truth = request.data["ground_truth"]
        if "tolerance" in request.data:
            tolerance = request.data["tolerance"]
            if not 0 <= tolerance <= 1:
                return Response(
                    {"error": "Tolerance must be between 0 and 1"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            honeypot.tolerance = tolerance
        if "is_active" in request.data:
            honeypot.is_active = request.data["is_active"]

        honeypot.save()

        return Response(HoneypotTaskSerializer(honeypot).data)

    def delete(self, request, project_id, honeypot_id):
        """Delete a honeypot"""
        honeypot, error = self.get_honeypot(project_id, honeypot_id, request.user)
        if error:
            return error

        honeypot.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class ProjectHoneypotStatsAPI(APIView):
    """
    Get honeypot statistics for a project.

    GET /api/projects/{project_id}/honeypots/stats/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        """Get honeypot statistics"""
        project = get_object_or_404(Project, id=project_id)

        if not project.has_permission(request.user):
            return Response(
                {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        stats = HoneypotService.get_honeypot_stats(project)

        return Response(stats)


class ProjectHoneypotConfigAPI(APIView):
    """
    Get or update honeypot configuration for a project.

    GET /api/projects/{project_id}/honeypot-config/
    PUT /api/projects/{project_id}/honeypot-config/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        """Get honeypot configuration"""
        project = get_object_or_404(Project, id=project_id)

        if not project.has_permission(request.user):
            return Response(
                {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        return Response(
            {
                "honeypot_enabled": getattr(project, "honeypot_enabled", True),
                "honeypot_injection_rate": float(
                    getattr(project, "honeypot_injection_rate", 0.1)
                ),
                "honeypot_min_interval": getattr(project, "honeypot_min_interval", 5),
                "honeypot_failure_threshold": getattr(
                    project, "honeypot_failure_threshold", 3
                ),
            }
        )

    def put(self, request, project_id):
        """Update honeypot configuration"""
        project = get_object_or_404(Project, id=project_id)

        if not project.has_permission(request.user):
            return Response(
                {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        serializer = HoneypotConfigSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Update fields
        update_fields = []
        for field, value in serializer.validated_data.items():
            if hasattr(project, field):
                setattr(project, field, value)
                update_fields.append(field)

        if update_fields:
            project.save(update_fields=update_fields)

        return Response(
            {
                "honeypot_enabled": project.honeypot_enabled,
                "honeypot_injection_rate": float(project.honeypot_injection_rate),
                "honeypot_min_interval": project.honeypot_min_interval,
                "honeypot_failure_threshold": project.honeypot_failure_threshold,
            }
        )


class ProjectHoneypotBulkCreateAPI(APIView):
    """
    Bulk create honeypot tasks.

    POST /api/projects/{project_id}/honeypots/bulk/
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, project_id):
        """Create multiple honeypots at once"""
        project = get_object_or_404(Project, id=project_id)

        if not project.has_permission(request.user):
            return Response(
                {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        honeypots_data = request.data.get("honeypots", [])

        if not honeypots_data:
            return Response(
                {"error": "No honeypots provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        created = []
        errors = []

        for i, hp_data in enumerate(honeypots_data):
            serializer = HoneypotCreateSerializer(
                data=hp_data, context={"project_id": project_id}
            )

            if serializer.is_valid():
                try:
                    task = Task.objects.get(id=serializer.validated_data["task_id"])
                    honeypot = HoneypotService.create_honeypot(
                        task=task,
                        ground_truth=serializer.validated_data["ground_truth"],
                        tolerance=serializer.validated_data.get("tolerance", 0.8),
                        created_by=request.user,
                    )
                    created.append(HoneypotTaskSerializer(honeypot).data)
                except Exception as e:
                    errors.append({"index": i, "error": str(e)})
            else:
                errors.append({"index": i, "error": serializer.errors})

        return Response(
            {
                "created_count": len(created),
                "error_count": len(errors),
                "created": created,
                "errors": errors,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_400_BAD_REQUEST,
        )
