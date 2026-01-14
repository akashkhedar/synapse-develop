"""
Security Audit Service

Logs all security-related events for monitoring and investigation.
"""

import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any

from django.conf import settings
from django.db import models
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
security_logger = logging.getLogger("security_audit")


class SecurityEventType:
    """Types of security events"""

    # Access events
    RESOURCE_ACCESS = "resource_access"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DOWNLOAD_ATTEMPT = "download_attempt"
    DOWNLOAD_BLOCKED = "download_blocked"

    # Data events
    DATA_EXPORT = "data_export"
    DATA_LEAK_SUSPECTED = "data_leak_suspected"
    WATERMARK_APPLIED = "watermark_applied"
    WATERMARK_EXTRACTED = "watermark_extracted"

    # Authentication events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    SESSION_EXPIRED = "session_expired"

    # Suspicious activity
    SUSPICIOUS_PATTERN = "suspicious_pattern"
    RATE_LIMIT_HIT = "rate_limit_hit"
    DEVTOOLS_DETECTED = "devtools_detected"
    SCREENSHOT_SUSPECTED = "screenshot_suspected"

    # Annotator specific
    HONEYPOT_FAILED = "honeypot_failed"
    TRUST_LEVEL_CHANGED = "trust_level_changed"
    ANNOTATOR_SUSPENDED = "annotator_suspended"


class SecurityAuditService:
    """
    Service for logging and querying security events.

    Usage:
        # Log access event
        SecurityAuditService.log_access(
            user=request.user,
            resource_type='task',
            resource_id='123',
            action='view'
        )

        # Log suspicious activity
        SecurityAuditService.log_suspicious(
            user=request.user,
            event_type=SecurityEventType.DEVTOOLS_DETECTED,
            details={'method': 'dimension'}
        )
    """

    @classmethod
    def log_access(
        cls,
        user,
        resource_type: str,
        resource_id: str,
        action: str,
        ip_address: str = None,
        user_agent: str = None,
        details: Dict[str, Any] = None,
    ):
        """
        Log resource access event.

        Args:
            user: User accessing the resource
            resource_type: Type of resource (task, project, annotation)
            resource_id: ID of the resource
            action: Action performed (view, edit, delete)
            ip_address: Client IP address
            user_agent: Client user agent
            details: Additional details
        """
        event = {
            "event_type": SecurityEventType.RESOURCE_ACCESS,
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": str(user.id) if user and hasattr(user, "id") else None,
            "user_email": user.email if user and hasattr(user, "email") else None,
            "resource_type": resource_type,
            "resource_id": str(resource_id),
            "action": action,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "details": details or {},
        }

        cls._log_event(event)

    @classmethod
    def log_suspicious(
        cls,
        user,
        event_type: str,
        details: Dict[str, Any] = None,
        severity: str = "warning",
        ip_address: str = None,
    ):
        """
        Log suspicious activity event.

        Args:
            user: User involved
            event_type: Type of suspicious event
            details: Event details
            severity: warning, high, critical
            ip_address: Client IP
        """
        event = {
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": str(user.id) if user and hasattr(user, "id") else None,
            "user_email": user.email if user and hasattr(user, "email") else None,
            "severity": severity,
            "ip_address": ip_address,
            "details": details or {},
        }

        cls._log_event(event, level="warning" if severity == "warning" else "error")

        # Alert on critical events
        if severity == "critical":
            cls._send_alert(event)

    @classmethod
    def log_download_attempt(
        cls,
        user,
        resource_type: str,
        resource_id: str,
        blocked: bool,
        reason: str = None,
        ip_address: str = None,
    ):
        """Log download attempt (successful or blocked)"""
        event_type = (
            SecurityEventType.DOWNLOAD_BLOCKED
            if blocked
            else SecurityEventType.DOWNLOAD_ATTEMPT
        )

        event = {
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": str(user.id) if user and hasattr(user, "id") else None,
            "user_email": user.email if user and hasattr(user, "email") else None,
            "resource_type": resource_type,
            "resource_id": str(resource_id),
            "blocked": blocked,
            "reason": reason,
            "ip_address": ip_address,
        }

        cls._log_event(event, level="warning" if blocked else "info")

    @classmethod
    def log_watermark_event(
        cls,
        user,
        action: str,  # 'applied' or 'extracted'
        resource_type: str,
        resource_id: str,
        watermark_payload: Dict[str, Any] = None,
    ):
        """Log watermark application or extraction"""
        event_type = (
            SecurityEventType.WATERMARK_APPLIED
            if action == "applied"
            else SecurityEventType.WATERMARK_EXTRACTED
        )

        event = {
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": str(user.id) if user and hasattr(user, "id") else None,
            "user_email": user.email if user and hasattr(user, "email") else None,
            "resource_type": resource_type,
            "resource_id": str(resource_id),
            "action": action,
            "watermark_payload": watermark_payload,
        }

        cls._log_event(event)

    @classmethod
    def log_honeypot_failure(
        cls,
        user,
        task_id: str,
        project_id: str,
        consecutive_failures: int,
    ):
        """Log honeypot failure event"""
        severity = "warning" if consecutive_failures < 3 else "high"

        event = {
            "event_type": SecurityEventType.HONEYPOT_FAILED,
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": str(user.id) if user and hasattr(user, "id") else None,
            "user_email": user.email if user and hasattr(user, "email") else None,
            "task_id": str(task_id),
            "project_id": str(project_id),
            "consecutive_failures": consecutive_failures,
            "severity": severity,
        }

        cls._log_event(event, level="warning")

        if consecutive_failures >= 3:
            cls._send_alert(event)

    @classmethod
    def _log_event(cls, event: Dict[str, Any], level: str = "info"):
        """Write event to security log"""
        log_message = json.dumps(event, default=str)

        if level == "error":
            security_logger.error(log_message)
        elif level == "warning":
            security_logger.warning(log_message)
        else:
            security_logger.info(log_message)

        # Also store in database if enabled
        cls._store_event(event)

    @classmethod
    def _store_event(cls, event: Dict[str, Any]):
        """Store event in database for querying"""
        try:
            # Lazy import to avoid circular dependency
            from .models import SecurityAuditLog

            SecurityAuditLog.objects.create(
                event_type=event.get("event_type"),
                user_id=event.get("user_id"),
                user_email=event.get("user_email"),
                severity=event.get("severity", "info"),
                ip_address=event.get("ip_address"),
                details=event,
            )
        except Exception as e:
            logger.debug(f"Could not store security event in DB: {e}")

    @classmethod
    def _send_alert(cls, event: Dict[str, Any]):
        """Send alert for critical security events"""
        logger.critical(f"SECURITY ALERT: {json.dumps(event, default=str)}")

        # TODO: Integrate with alerting system (email, Slack, etc.)

    @classmethod
    def get_user_events(
        cls,
        user_id: str,
        event_types: list = None,
        start_date: datetime = None,
        end_date: datetime = None,
        limit: int = 100,
    ):
        """Query security events for a user"""
        try:
            from .models import SecurityAuditLog

            queryset = SecurityAuditLog.objects.filter(user_id=user_id)

            if event_types:
                queryset = queryset.filter(event_type__in=event_types)

            if start_date:
                queryset = queryset.filter(created_at__gte=start_date)

            if end_date:
                queryset = queryset.filter(created_at__lte=end_date)

            return queryset.order_by("-created_at")[:limit]
        except Exception as e:
            logger.error(f"Failed to query security events: {e}")
            return []


# Convenience function for request-based logging
def log_request_access(request, resource_type: str, resource_id: str, action: str):
    """Helper to log access from a Django request"""
    ip = request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR", ""))
    user_agent = request.META.get("HTTP_USER_AGENT", "")

    SecurityAuditService.log_access(
        user=(
            request.user
            if hasattr(request, "user") and request.user.is_authenticated
            else None
        ),
        resource_type=resource_type,
        resource_id=resource_id,
        action=action,
        ip_address=ip.split(",")[0].strip() if ip else None,
        user_agent=user_agent,
    )
