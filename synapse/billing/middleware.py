"""
API Rate Limiting Middleware for billing purposes.

Tracks API usage per organization and enforces rate limits.
Overage is billed at end of day.
"""

import logging
from django.utils import timezone
from django.http import JsonResponse

logger = logging.getLogger(__name__)


class APIRateLimitMiddleware:
    """
    Middleware to track API usage for billing.

    This middleware:
    1. Tracks all API requests by organization
    2. Categorizes requests as read/write/export
    3. Logs overage for billing

    Note: This middleware tracks usage but doesn't block requests.
    Organizations are billed for overage at end of day.
    """

    # Endpoints that count as exports
    EXPORT_PATTERNS = [
        "/api/projects/{id}/export",
        "/export/",
        "/download/",
    ]

    # Endpoints that are read operations
    READ_METHODS = ["GET", "HEAD", "OPTIONS"]

    # Endpoints that are write operations
    WRITE_METHODS = ["POST", "PUT", "PATCH", "DELETE"]

    # Paths to exclude from tracking
    EXCLUDED_PATHS = [
        "/api/health/",
        "/api/version/",
        "/static/",
        "/media/",
        "/favicon.ico",
        "/admin/",
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Track before processing
        self._track_request(request)

        # Get response
        response = self.get_response(request)

        return response

    def _track_request(self, request):
        """Track the API request for billing"""
        # Skip excluded paths
        path = request.path
        if any(path.startswith(excluded) for excluded in self.EXCLUDED_PATHS):
            return

        # Only track API requests
        if not path.startswith("/api/"):
            return

        # Get organization from request
        organization = self._get_organization(request)
        if not organization:
            return

        # Determine request type
        request_type = self._categorize_request(request)

        # Track the request
        try:
            from billing.services import APIRateLimitService

            within_limit = APIRateLimitService.track_request(organization, request_type)

            if not within_limit:
                logger.debug(
                    f"API rate limit exceeded for {organization.title}: {request_type}"
                )
        except Exception as e:
            # Don't block request if tracking fails
            logger.error(f"Error tracking API request: {e}")

    def _get_organization(self, request):
        """Get organization from the request"""
        if not hasattr(request, "user") or not request.user.is_authenticated:
            return None

        # Get active organization from user
        if hasattr(request.user, "active_organization"):
            return request.user.active_organization

        return None

    def _categorize_request(self, request):
        """Categorize request as read/write/export"""
        path = request.path.lower()
        method = request.method.upper()

        # Check for export
        if "export" in path or "download" in path:
            return "export"

        # Check method
        if method in self.READ_METHODS:
            return "read"
        elif method in self.WRITE_METHODS:
            return "write"

        return "read"


class BlockingAPIRateLimitMiddleware(APIRateLimitMiddleware):
    """
    Alternative middleware that blocks requests when limits are exceeded.

    Use this if you want to hard-block instead of allowing with overage billing.
    """

    # Multiplier for hard limit (e.g., 10x free limit before blocking)
    HARD_LIMIT_MULTIPLIER = 10

    def __call__(self, request):
        # Check if should block
        should_block, message = self._should_block(request)

        if should_block:
            return JsonResponse(
                {
                    "error": "Rate limit exceeded",
                    "message": message,
                    "retry_after": self._get_seconds_until_midnight(),
                },
                status=429,
            )

        # Track before processing
        self._track_request(request)

        # Get response
        response = self.get_response(request)

        return response

    def _should_block(self, request):
        """Check if request should be blocked"""
        # Skip non-API and excluded paths
        path = request.path
        if not path.startswith("/api/"):
            return False, None

        if any(path.startswith(excluded) for excluded in self.EXCLUDED_PATHS):
            return False, None

        # Get organization
        organization = self._get_organization(request)
        if not organization:
            return False, None

        # Get request type
        request_type = self._categorize_request(request)

        # Check rate limit
        try:
            from billing.services import APIRateLimitService

            status = APIRateLimitService.check_rate_limit(organization, request_type)

            # Calculate hard limit
            hard_limit = status["limit"] * self.HARD_LIMIT_MULTIPLIER

            if status["used"] >= hard_limit:
                return True, (
                    f"Hard rate limit exceeded. {request_type.capitalize()} requests: "
                    f"{status['used']}/{hard_limit}. Resets at midnight."
                )
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")

        return False, None

    def _get_seconds_until_midnight(self):
        """Get seconds until midnight UTC"""
        now = timezone.now()
        midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
        from datetime import timedelta

        next_midnight = midnight + timedelta(days=1)
        return int((next_midnight - now).total_seconds())





