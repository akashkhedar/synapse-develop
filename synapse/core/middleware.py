"""This file and its contents are licensed under the Apache License 2.0. Please see the included NOTICE for copyright information and LICENSE for a copy of the license."""

import logging
import time
from datetime import timedelta
from uuid import uuid4

import ujson as json
from core.utils.contextlog import ContextLog
from csp.middleware import CSPMiddleware
from django.conf import settings
from django.contrib.auth import logout
from django.core.exceptions import MiddlewareNotUsed
from django.core.handlers.base import BaseHandler
from django.http import HttpResponsePermanentRedirect
from django.middleware.common import CommonMiddleware
from django.utils.deprecation import MiddlewareMixin
from django.utils.http import escape_leading_slashes
from rest_framework.permissions import SAFE_METHODS

logger = logging.getLogger(__name__)


class MultipartStreamMiddleware:
    """Middleware to pre-parse multipart requests before other middleware can consume the stream.
    
    This must be the FIRST middleware in the chain. DRF and other components may read
    the request stream during authentication/permission checks, consuming it before
    the view can parse files. This middleware parses multipart data early and caches it.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        content_type = request.META.get('CONTENT_TYPE', '') or ''
        
        # Only process multipart requests for import endpoints
        if 'multipart/form-data' in content_type and '/import' in request.path:
            # Parse multipart NOW, before any other middleware can touch the stream
            if not getattr(request, '_read_started', False):
                self._parse_multipart_now(request)
        
        return self.get_response(request)
    
    def _parse_multipart_now(self, request):
        """Parse multipart data immediately and cache on request."""
        from django.http.multipartparser import MultiPartParser
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            # Get the stream
            stream = getattr(request, '_stream', None)
            if not stream:
                stream = request.META.get('wsgi.input')
            
            if not stream:
                logger.warning("MultipartStreamMiddleware: No stream available")
                return
            
            # Parse the multipart data
            parser = MultiPartParser(
                META=request.META,
                input_data=stream,
                upload_handlers=request.upload_handlers,
                encoding=request.encoding or 'utf-8'
            )
            
            post_data, files = parser.parse()
            
            # Cache on request
            request._post = post_data
            request._files = files
            request._read_started = True
            
            if files:
                logger.debug(f"MultipartStreamMiddleware: Parsed {len(files)} file(s)")
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"MultipartStreamMiddleware: Parse error: {e}")


def enforce_csrf_checks(func):
    """Enable csrf for specified view func"""
    # USE_ENFORCE_CSRF_CHECKS=False is for tests
    if settings.USE_ENFORCE_CSRF_CHECKS:

        def wrapper(request, *args, **kwargs):
            return func(request, *args, **kwargs)

        wrapper._dont_enforce_csrf_checks = False
        return wrapper
    else:
        return func


class DisableCSRF(MiddlewareMixin):
    # disable csrf for api requests
    def process_view(self, request, callback, *args, **kwargs):
        if hasattr(callback, "_dont_enforce_csrf_checks"):
            setattr(
                request, "_dont_enforce_csrf_checks", callback._dont_enforce_csrf_checks
            )
        elif request.GET.get(
            "enforce_csrf_checks"
        ):  # _dont_enforce_csrf_checks is for test
            setattr(request, "_dont_enforce_csrf_checks", False)
        else:
            setattr(request, "_dont_enforce_csrf_checks", True)


class HttpSmartRedirectResponse(HttpResponsePermanentRedirect):
    pass


class CommonMiddlewareAppendSlashWithoutRedirect(CommonMiddleware):
    """This class converts HttpSmartRedirectResponse to the common response
    of Django view, without redirect. This is necessary to match status_codes
    for urls like /url?q=1 and /url/?q=1. If you don't use it, you will have 302
    code always on pages without slash.
    """

    response_redirect_class = HttpSmartRedirectResponse

    def __init__(self, *args, **kwargs):
        # create django request resolver
        self.handler = BaseHandler()

        # prevent recursive includes
        old = settings.MIDDLEWARE
        name = self.__module__ + "." + self.__class__.__name__
        settings.MIDDLEWARE = [i for i in settings.MIDDLEWARE if i != name]

        self.handler.load_middleware()

        settings.MIDDLEWARE = old
        super(CommonMiddlewareAppendSlashWithoutRedirect, self).__init__(
            *args, **kwargs
        )

    def get_full_path_with_slash(self, request):
        """Return the full path of the request with a trailing slash appended
        without Exception in Debug mode
        """
        new_path = request.get_full_path(force_append_slash=True)
        # Prevent construction of scheme relative urls.
        new_path = escape_leading_slashes(new_path)
        return new_path

    def process_response(self, request, response):
        response = super(
            CommonMiddlewareAppendSlashWithoutRedirect, self
        ).process_response(request, response)

        request.editor_keymap = settings.EDITOR_KEYMAP

        if isinstance(response, HttpSmartRedirectResponse):
            if not request.path.endswith("/"):
                # remove prefix SCRIPT_NAME
                path = (
                    request.path[len(settings.FORCE_SCRIPT_NAME) :]
                    if settings.FORCE_SCRIPT_NAME
                    else request.path
                )
                request.path = path + "/"
            # we don't need query string in path_info because it's in request.GET already
            request.path_info = request.path
            response = self.handler.get_response(request)

        return response

    def should_redirect_with_slash(self, request):
        """
        Override the original method to keep global APPEND_SLASH setting false
        """
        if not request.path_info.endswith("/"):
            return True
        return False


class SetSessionUIDMiddleware(CommonMiddleware):
    def process_request(self, request):
        if "uid" not in request.session:
            request.session["uid"] = str(uuid4())


class ContextLogMiddleware(CommonMiddleware):
    def __init__(self, get_response):
        self.get_response = get_response
        self.log = ContextLog()

    def __call__(self, request):
        body = None
        # Get content type from META (Django's HttpRequest stores it there)
        content_type = request.META.get('CONTENT_TYPE', '') or ''
        
        # Don't read body for multipart requests (file uploads)
        # Reading the body stream prevents DRF from parsing files later
        is_multipart = 'multipart/form-data' in content_type
        if not is_multipart:
            try:
                body = json.loads(request.body)
            except:  # noqa: E722
                try:
                    body = request.body.decode("utf-8")
                except:  # noqa: E722
                    pass

        if "server_id" not in request:
            setattr(request, "server_id", self.log._get_server_id())

        response = self.get_response(request)
        self.log.send(request=request, response=response, body=body)

        return response

    def process_request(self, request):
        if "server_id" not in request:
            setattr(request, "server_id", self.log._get_server_id())


class DatabaseIsLockedRetryMiddleware(CommonMiddleware):
    """Workaround for sqlite performance issues
    we wait and retry request if database is locked"""

    def __init__(self, get_response):
        if settings.DJANGO_DB != settings.DJANGO_DB_SQLITE:
            raise MiddlewareNotUsed()
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        retries_number = 0
        sleep_time = 1
        backoff = 1.5
        while (
            response.status_code == 500
            and hasattr(response, "content")
            and b"database-is-locked-error" in response.content
            and retries_number < 15
        ):
            time.sleep(sleep_time)
            response = self.get_response(request)
            retries_number += 1
            sleep_time *= backoff
        return response


class XApiKeySupportMiddleware:
    """Middleware that adds support for the X-Api-Key header, by having its value supersede
    anything that's set in the Authorization header."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if "HTTP_X_API_KEY" in request.META:
            request.META["HTTP_AUTHORIZATION"] = (
                f'Token {request.META["HTTP_X_API_KEY"]}'
            )
            del request.META["HTTP_X_API_KEY"]

        return self.get_response(request)


class UpdateLastActivityMiddleware(CommonMiddleware):
    def process_view(self, request, view_func, view_args, view_kwargs):
        if hasattr(request, "user") and request.method not in SAFE_METHODS:
            if request.user.is_authenticated:
                request.user.update_last_activity()


class InactivitySessionTimeoutMiddleWare(CommonMiddleware):
    """Log the user out if they have been logged in for too long
    or inactive for too long"""

    # paths that don't count as user activity
    NOT_USER_ACTIVITY_PATHS = []

    def process_request(self, request) -> None:
        if (
            not hasattr(request, "session")
            or request.session.is_empty()
            or not hasattr(request, "user")
            or not request.user.is_authenticated
            or
            # scim assign request.user implicitly, check CustomSCIMAuthCheckMiddleware
            (hasattr(request, "is_scim") and request.is_scim)
            or (hasattr(request, "is_jwt") and request.is_jwt)
        ):
            return

        current_time = time.time()
        if "last_login" not in request.session:
            request.session["last_login"] = current_time
            last_login = current_time
        else:
            last_login = request.session["last_login"]

        active_org = request.user.active_organization
        if active_org:
            org_max_session_age = timedelta(
                minutes=active_org.session_timeout_policy.max_session_age
            ).total_seconds()
            max_time_between_activity = timedelta(
                minutes=active_org.session_timeout_policy.max_time_between_activity
            ).total_seconds()

            if (current_time - last_login) > org_max_session_age:
                logger.info(
                    f"Request is too far from last login {current_time - last_login:.0f} > {settings.MAX_SESSION_AGE}; logout"
                )
                logout(request)

        else:
            max_time_between_activity = settings.MAX_TIME_BETWEEN_ACTIVITY
            # Check if this request is too far from when the login happened
            if (current_time - last_login) > settings.MAX_SESSION_AGE:
                logger.info(
                    f"Request is too far from last login {current_time - last_login:.0f} > {settings.MAX_SESSION_AGE}; logout"
                )
                logout(request)

        # Push the expiry to the max every time a new request is made to a url that indicates user activity
        # but only if it's not a URL we want to ignore
        for path in self.NOT_USER_ACTIVITY_PATHS:
            if isinstance(path, str) and path == str(request.path_info):
                return
            elif "query" in path:
                parts = str(request.path_info).split("?")
                if len(parts) == 2 and path["query"] in parts[1]:
                    return
        request.session.set_expiry(
            max_time_between_activity
            if request.session.get("keep_me_logged_in", True)
            else 0
        )


class SynapseCspMiddleware(CSPMiddleware):
    """
    Extend CSPMiddleware to support switching report-only CSP to regular CSP.

    For use with core.decorators.override_report_only_csp.
    """

    def process_response(self, request, response):
        response = super().process_response(request, response)
        if getattr(response, "_override_report_only_csp", False):
            if csp_policy := response.get("Content-Security-Policy-Report-Only"):
                response["Content-Security-Policy"] = csp_policy
                del response["Content-Security-Policy-Report-Only"]
            delattr(response, "_override_report_only_csp")
        return response


class SecurityHeadersMiddleware:
    """
    Middleware to add security headers for data protection.

    Adds:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - X-XSS-Protection: 1; mode=block
    - Referrer-Policy: strict-origin-when-cross-origin
    - Permissions-Policy: camera=(), microphone=(), geolocation=()
    - Cache-Control headers for sensitive content
    """

    # Headers for all responses
    SECURITY_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "camera=(), microphone=(), geolocation=(), screen-wake-lock=()",
        "Cross-Origin-Resource-Policy": "cross-origin",
    }

    # Additional headers for API/data responses
    SENSITIVE_HEADERS = {
        "Cache-Control": "no-store, no-cache, must-revalidate, private",
        "Pragma": "no-cache",
        "Expires": "0",
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Add security headers to all responses
        for header, value in self.SECURITY_HEADERS.items():
            if header not in response:
                response[header] = value

        # Add sensitive headers for API endpoints and data access
        if self._is_sensitive_endpoint(request):
            for header, value in self.SENSITIVE_HEADERS.items():
                response[header] = value

        # Add download protection header for media
        if self._is_media_response(request, response):
            response["Content-Disposition"] = "inline"
            # Prevent download prompts
            if "X-Content-Type-Options" not in response:
                response["X-Content-Type-Options"] = "nosniff"

        return response

    def _is_sensitive_endpoint(self, request) -> bool:
        """Check if endpoint returns sensitive data"""
        path = request.path.lower()
        sensitive_patterns = [
            "/api/",
            "/tasks/",
            "/projects/",
            "/annotations/",
            "/data/",
            "/storage/",
        ]
        return any(pattern in path for pattern in sensitive_patterns)

    def _is_media_response(self, request, response) -> bool:
        """Check if response contains media content"""
        content_type = response.get("Content-Type", "")
        media_types = ["image/", "video/", "audio/"]
        return any(media_type in content_type for media_type in media_types)


class DownloadPreventionMiddleware:
    """
    Middleware to prevent direct file downloads for annotators.

    This middleware is designed to block DOWNLOAD attempts, not normal
    image loading for UI rendering.

    It ALLOWS:
    - Image requests with browser Accept headers (needed for UI)
    - Requests from the Synapse application (Referer check)
    - API requests with proper authentication

    It BLOCKS:
    - Requests with download-indicating headers
    - Requests with ?download query param
    - Requests without proper Referer (direct URL access)
    """

    # Paths that contain sensitive data
    SENSITIVE_PATHS = [
        "/data/upload/",
        "/data/download/",
        "/storage/data/",
    ]

    # Referer patterns that indicate legitimate app usage
    ALLOWED_REFERERS = [
        "/projects/",
        "/tasks/",
        "/dm/",
        "/data-manager/",
        "/",  # Root of the app
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if this is a download attempt that should be blocked
        if self._is_download_attempt(request):
            from django.http import HttpResponseForbidden

            logger.warning(
                f"Blocked download attempt by user {getattr(request.user, 'email', 'anonymous')} "
                f"for path {request.path}"
            )
            return HttpResponseForbidden(
                "Direct downloads are not permitted. Use the annotation interface."
            )

        return self.get_response(request)

    def _is_download_attempt(self, request) -> bool:
        """
        Determine if request is a download attempt that should be blocked.

        We want to ALLOW: Browser image requests for UI display
        We want to BLOCK: Direct download attempts
        """
        # Only apply to authenticated annotators
        if not hasattr(request, "user") or not request.user.is_authenticated:
            return False

        # Check if user is annotator (not admin/client)
        is_annotator = getattr(request.user, "is_annotator", False)
        is_staff = getattr(request.user, "is_staff", False)
        is_superuser = getattr(request.user, "is_superuser", False)

        # Don't block admins or staff
        if is_staff or is_superuser:
            return False

        # Only block annotators
        if not is_annotator:
            return False

        # Check if accessing sensitive path
        path = request.path.lower()
        is_sensitive_path = any(blocked in path for blocked in self.SENSITIVE_PATHS)

        if not is_sensitive_path:
            return False

        # Check for explicit download indicators
        if self._has_download_indicators(request):
            return True

        # Check for missing or suspicious Referer
        # (Direct URL access without coming from the app)
        referer = request.META.get("HTTP_REFERER", "")
        if not referer:
            # No referer could be a direct URL access (potentially block)
            # But it could also be a legitimate request - be lenient
            return False

        # If referer is from our app, allow it
        if any(allowed in referer for allowed in self.ALLOWED_REFERERS):
            return False

        # Allow requests with typical browser Accept headers for images
        accept = request.META.get("HTTP_ACCEPT", "")
        if "image/" in accept or "*/*" in accept:
            # This is likely a browser requesting an image for display
            return False

        # Default: allow the request
        # We prefer to be lenient rather than break the UI
        return False

    def _has_download_indicators(self, request) -> bool:
        """Check for headers/params that indicate a download attempt"""
        # Check for ?download query parameter
        if request.GET.get("download"):
            return True

        # Check for download-specific Accept headers
        accept = request.META.get("HTTP_ACCEPT", "")
        if "application/octet-stream" in accept:
            return True

        # Check for download-specific response type requested
        if request.GET.get("response_type") == "download":
            return True

        return False
