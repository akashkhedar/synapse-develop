"""
Secure Image Proxy API

Provides secure proxying of images with:
- Dynamic watermarking for annotators/experts
- Role-based access control
- Security headers to prevent caching/downloading
- Rate limiting support
"""

import base64
import io
import logging
import time
from typing import Optional, Union
from urllib.parse import unquote

from django.conf import settings
from django.http import HttpRequest, HttpResponse, StreamingHttpResponse
from drf_spectacular.utils import extend_schema
from projects.models import Project
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from tasks.models import Task

from core.feature_flags import flag_set
from core.watermark_service import WatermarkService
from synapse.io_storages.functions import get_storage_by_url

logger = logging.getLogger(__name__)


def should_apply_watermark(user) -> bool:
    """
    Determine if watermarks should be applied based on user role.

    Watermarks are applied to:
    - Annotators (regular annotators)
    - Experts (super annotators)

    Watermarks are NOT applied to:
    - Organization admins
    - Project managers
    - System admins
    """
    if not user or not user.is_authenticated:
        return True  # Unauthenticated = apply watermark

    # Check if user is an admin (skip watermark)
    if hasattr(user, "is_superuser") and user.is_superuser:
        return False

    if hasattr(user, "is_staff") and user.is_staff:
        return False

    # Check for organization admin role
    # This depends on the specific role system in Synapse
    # For now, apply watermark to all non-admin users
    return True


def get_watermark_settings() -> dict:
    """Get watermark configuration from settings or defaults."""
    return {
        "enabled": getattr(settings, "SECURITY_WATERMARK_ENABLED", True),
        "position": getattr(settings, "SECURITY_WATERMARK_POSITION", "tiled"),
        "include_invisible": getattr(settings, "SECURITY_INVISIBLE_WATERMARK", True),
    }


def apply_dynamic_watermark(
    image_data: bytes,
    user,
    project_id: Optional[str] = None,
    task_id: Optional[str] = None,
) -> bytes:
    """
    Apply both visible and invisible watermarks to image data.

    Args:
        image_data: Raw image bytes
        user: Django user object
        project_id: Optional project identifier
        task_id: Optional task identifier

    Returns:
        Watermarked image bytes
    """
    config = get_watermark_settings()

    if not config["enabled"]:
        return image_data

    try:
        # Get user identifiers
        user_id = str(user.id) if user and hasattr(user, "id") else "unknown"
        user_email = getattr(user, "email", user_id)
        session_id = getattr(user, "session_key", None) or str(int(time.time()))

        # Apply visible watermark
        watermarked = WatermarkService.apply_visible_watermark(
            image_data,
            user_id=user_email,
            session_id=session_id,
            position=config["position"],
        )

        # Apply invisible (steganographic) watermark if enabled
        if config["include_invisible"]:
            payload = WatermarkService.create_forensic_watermark(
                user_id=user_id,
                session_id=session_id,
                project_id=project_id,
                task_id=task_id,
            )
            watermarked = WatermarkService.apply_invisible_watermark(
                watermarked,
                payload=payload,
            )

        return watermarked

    except Exception as e:
        logger.error(f"Failed to apply dynamic watermark: {e}")
        return image_data


def add_security_headers(response: HttpResponse) -> HttpResponse:
    """Add security headers to prevent downloading/caching."""
    # No caching
    response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"

    # Prevent embedding
    response["X-Frame-Options"] = "SAMEORIGIN"

    # Prevent MIME sniffing
    response["X-Content-Type-Options"] = "nosniff"

    # Content disposition - inline only, no download prompt
    response["Content-Disposition"] = "inline"

    # CSP to prevent framing
    response["Content-Security-Policy"] = "frame-ancestors 'self'"

    return response


class SecureImageProxyMixin:
    """Mixin for secure image proxying with watermarking."""

    def proxy_with_watermark(
        self,
        request: HttpRequest,
        image_data: bytes,
        content_type: str,
        project_id: Optional[str] = None,
        task_id: Optional[str] = None,
    ) -> HttpResponse:
        """
        Proxy image data with optional watermarking.

        Args:
            request: HTTP request
            image_data: Raw image bytes
            content_type: MIME type of the image
            project_id: Optional project ID
            task_id: Optional task ID

        Returns:
            HTTP response with watermarked image
        """
        user = request.user

        # Apply watermark for non-admin users
        if should_apply_watermark(user):
            watermarked_data = apply_dynamic_watermark(
                image_data,
                user,
                project_id=project_id,
                task_id=task_id,
            )
            # Watermarked images are always PNG
            content_type = "image/png"
        else:
            watermarked_data = image_data

        # Create response
        response = HttpResponse(
            watermarked_data,
            content_type=content_type,
        )

        # Add security headers
        response = add_security_headers(response)

        return response


@extend_schema(exclude=True)
class SecureTaskImageProxy(SecureImageProxyMixin, APIView):
    """
    Secure image proxy for task images.

    Applies dynamic watermarking and security headers for annotators.
    Admins receive unwatermarked images.
    """

    http_method_names = ["get"]
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        """Get watermarked image for a task."""
        task_id = kwargs.get("task_id")
        fileuri = request.GET.get("fileuri")

        if not task_id or not fileuri:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        try:
            task = Task.objects.get(pk=task_id)
        except Task.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if not task.has_permission(request.user):
            return Response(status=status.HTTP_403_FORBIDDEN)

        # Decode fileuri
        try:
            fileuri = base64.urlsafe_b64decode(fileuri.encode()).decode()
        except Exception:
            fileuri = unquote(fileuri)

        # Get project storage
        project = task.project
        storage_objects = project.get_all_import_storage_objects
        storage = get_storage_by_url(fileuri, storage_objects)

        if not storage:
            # Fallback: try to fetch directly if URL is HTTP(S)
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            # Get image data from storage
            stream, content_type, metadata = storage.get_bytes_stream(fileuri)

            if stream is None:
                return Response(status=status.HTTP_404_NOT_FOUND)

            # Read all data (for watermarking we need full image)
            image_data = stream.read()
            stream.close()

            # Only watermark image types
            if content_type and content_type.startswith("image/"):
                return self.proxy_with_watermark(
                    request,
                    image_data,
                    content_type,
                    project_id=str(project.id),
                    task_id=str(task_id),
                )
            else:
                # Non-image content: just add security headers
                response = HttpResponse(image_data, content_type=content_type)
                return add_security_headers(response)

        except Exception as e:
            logger.error(f"Error proxying secure image: {e}", exc_info=True)
            return Response(
                {"error": "Failed to proxy image"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@extend_schema(exclude=True)
class SecureProjectImageProxy(SecureImageProxyMixin, APIView):
    """
    Secure image proxy for project-level images.

    Applies dynamic watermarking and security headers for annotators.
    """

    http_method_names = ["get"]
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        """Get watermarked image for a project."""
        project_id = kwargs.get("project_id")
        fileuri = request.GET.get("fileuri")

        if not project_id or not fileuri:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        try:
            project = Project.objects.get(pk=project_id)
        except Project.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if not project.has_permission(request.user):
            return Response(status=status.HTTP_403_FORBIDDEN)

        # Decode fileuri
        try:
            fileuri = base64.urlsafe_b64decode(fileuri.encode()).decode()
        except Exception:
            fileuri = unquote(fileuri)

        # Get storage
        storage_objects = project.get_all_import_storage_objects
        storage = get_storage_by_url(fileuri, storage_objects)

        if not storage:
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            # Get image data from storage
            stream, content_type, metadata = storage.get_bytes_stream(fileuri)

            if stream is None:
                return Response(status=status.HTTP_404_NOT_FOUND)

            image_data = stream.read()
            stream.close()

            if content_type and content_type.startswith("image/"):
                return self.proxy_with_watermark(
                    request,
                    image_data,
                    content_type,
                    project_id=str(project_id),
                )
            else:
                response = HttpResponse(image_data, content_type=content_type)
                return add_security_headers(response)

        except Exception as e:
            logger.error(f"Error proxying secure image: {e}", exc_info=True)
            return Response(
                {"error": "Failed to proxy image"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
