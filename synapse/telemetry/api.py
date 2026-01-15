"""
Telemetry API - High-Throughput Event Ingestion

Provides /api/telemetry endpoint for browser behavior signals.
"""

import logging
from datetime import datetime

from django.conf import settings
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import UserRateThrottle

logger = logging.getLogger(__name__)


class TelemetryRateThrottle(UserRateThrottle):
    """Rate limit telemetry to prevent abuse"""

    rate = "60/minute"  # 60 events per minute per user


@method_decorator(csrf_exempt, name="dispatch")
class TelemetryIngestAPI(APIView):
    """
    High-throughput endpoint for ingesting telemetry events.

    POST /api/telemetry

    Request body:
    {
        "events": [
            {
                "type": "zoom",
                "value": {"level": 4.8},
                "timestamp": 1715609033,
                "task_id": 9923
            },
            ...
        ]
    }

    Or single event:
    {
        "type": "copy",
        "value": {},
        "timestamp": 1715609033
    }
    """

    permission_classes = [AllowAny]  # Allow anonymous but only save for authenticated
    throttle_classes = [TelemetryRateThrottle]

    # Valid event types
    VALID_EVENT_TYPES = {
        "mouse_entropy",
        "click",
        "scroll",
        "zoom",
        "dwell",
        "focus",
        "blur",
        "devtools",
        "copy",
        "printscreen",
        "contextmenu",
        "dragstart",
        "vm_detected",
        "headless",
        "multi_monitor",
        "keyboard_shortcut",
        "session_start",
        "session_end",
    }

    def post(self, request):
        """Ingest telemetry events"""
        from .models import TelemetryEvent
        from .rules import rule_engine
        from .scoring import risk_scorer
        from .actions import action_engine

        user = request.user

        # Silently accept but don't save for anonymous users
        if not user.is_authenticated:
            return Response(
                {"status": "ok", "received": 0},
                status=status.HTTP_200_OK,
            )

        data = request.data

        # Handle both single event and batch
        if "events" in data:
            events_data = data["events"]
        else:
            events_data = [data]

        if not events_data:
            return Response(
                {"error": "No events provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Limit batch size
        max_batch = 50
        events_data = events_data[:max_batch]

        # Get client info
        ip_address = self._get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")[:500]
        session_id = request.session.session_key or ""

        # Create events
        events_to_create = []
        for event_data in events_data:
            event_type = event_data.get("type", "")

            if event_type not in self.VALID_EVENT_TYPES:
                continue  # Skip invalid event types

            # Helper to convert JS timestamp to datetime
            ts = event_data.get("timestamp")
            timestamp = timezone.now()  # Default to now if parsing fails
            if ts:
                try:
                    # ts is usually in milliseconds
                    if ts > 1000000000000:
                        ts = ts / 1000.0
                    timestamp = datetime.fromtimestamp(ts, tz=dt_timezone.utc)
                except Exception:
                    pass  # Keep default timestamp if parsing fails

            # Truncate string fields to fit DB constraints
            event_type = str(event_data.get("type", "unknown"))[:50]
            session_id = str(event_data.get("session_id", ""))[:64]

            if event_type not in self.VALID_EVENT_TYPES:
                continue  # Skip invalid event types

            # Validate FKs - only set if they are integers
            raw_task_id = event_data.get("task_id")
            raw_project_id = event_data.get("project_id")

            final_task_id = None
            final_project_id = None

            # Store original IDs in value if they are not valid FKs later
            value_data = event_data.get("value", {})
            if isinstance(value_data, dict):
                # Ensure we don't overwrite existing data
                value_data = value_data.copy()
            else:
                value_data = {"raw_value": value_data}

            # Simple integer check first - we can do a DB check for the whole batch if needed
            # But for now, safely handling non-integers is a good first step.
            # Given the error is "Key (task_id)=(1) is not present", it IS an integer but doesn't exist.
            # So we MUST check existence if we want to be safe, or just catch the error.
            # Checking existence for every event might be slow.
            # For the annotator test specifically, we know these are "virtual" tasks.
            # Let's fallback to checking if it's a valid ID in the respective tables.

            try:
                if raw_task_id and str(raw_task_id).isdigit():
                    t_id = int(raw_task_id)
                    if Task.objects.filter(id=t_id).exists():
                        final_task_id = t_id
                    else:
                        value_data["skipped_task_id"] = raw_task_id
                elif raw_task_id:
                    value_data["skipped_task_id"] = raw_task_id
            except Exception:
                pass

            try:
                if raw_project_id and str(raw_project_id).isdigit():
                    p_id = int(raw_project_id)
                    if Project.objects.filter(id=p_id).exists():
                        final_project_id = p_id
                    else:
                        value_data["skipped_project_id"] = raw_project_id
                elif raw_project_id:
                    value_data["skipped_project_id"] = raw_project_id
            except Exception:
                pass

            events_to_create.append(
                TelemetryEvent(
                    user=user if request.user.is_authenticated else None,
                    event_type=event_type,
                    value=value_data,
                    timestamp=timestamp,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    session_id=session_id,
                    project_id=final_project_id,
                    task_id=final_task_id,
                )
            )
        # Bulk create events
        if events_to_create:
            TelemetryEvent.objects.bulk_create(events_to_create)

            # Update last event time
            profile = risk_scorer.get_or_create_profile(user.id)
            profile.last_event_at = timezone.now()
            profile.save(update_fields=["last_event_at"])

            # Run rule engine (async in production, inline for now)
            violations = rule_engine.evaluate_user(user.id)

            if violations:
                # Process violations and update risk score
                profile = risk_scorer.process_violations(user.id, violations)

                # Take actions if needed
                actions = action_engine.evaluate_and_act(user.id, profile)

                if actions:
                    logger.info(f"Actions taken for user {user.id}: {actions}")

        return Response(
            {
                "status": "ok",
                "received": len(events_to_create),
            },
            status=status.HTTP_201_CREATED,
        )

    def _get_client_ip(self, request) -> str:
        """Extract client IP from request"""
        x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded:
            return x_forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "")


class UserRiskAPI(APIView):
    """
    API for viewing user risk profile (admin only).

    GET /api/telemetry/risk/<user_id>
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, user_id=None):
        """Get risk profile for a user"""
        from .scoring import risk_scorer

        # Only staff can view other users' risk
        if user_id and user_id != request.user.id:
            if not request.user.is_staff:
                return Response(
                    {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
                )
        else:
            user_id = request.user.id

        summary = risk_scorer.get_user_risk_summary(user_id)
        return Response(summary)


class HighRiskUsersAPI(APIView):
    """
    API for listing high-risk users (admin only).

    GET /api/telemetry/high-risk
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List all high-risk users"""
        from .scoring import risk_scorer

        if not request.user.is_staff:
            return Response(
                {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        min_level = request.query_params.get("level", "high")
        profiles = risk_scorer.get_high_risk_users(min_level)

        data = [
            {
                "user_id": p.user_id,
                "email": p.user.email if hasattr(p, "user") else None,
                "risk_score": p.risk_score,
                "risk_level": p.risk_level,
                "is_frozen": p.is_frozen,
                "triggered_rules": p.triggered_rules,
                "last_violation": p.last_violation_at,
            }
            for p in profiles
        ]

        return Response(
            {
                "count": len(data),
                "users": data,
            }
        )


class UnfreezeUserAPI(APIView):
    """
    API for unfreezing a user account (admin only).

    POST /api/telemetry/unfreeze/<user_id>
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        """Unfreeze a user account"""
        from .actions import action_engine

        if not request.user.is_staff:
            return Response(
                {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        reason = request.data.get("reason", "Admin action")

        try:
            action_engine.unfreeze_account(
                user_id=user_id, actor_id=request.user.id, reason=reason
            )
            return Response({"status": "ok", "message": "User unfrozen"})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
