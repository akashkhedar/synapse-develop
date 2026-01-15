"""
Rule Engine - Pattern Detection for Behavioral Surveillance

Defines rules that detect suspicious behavior patterns and assign risk points.
Rules are evaluated against recent telemetry events.
"""

import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import List, Optional, Callable

from django.db.models import Count, Avg
from django.utils import timezone

logger = logging.getLogger(__name__)


@dataclass
class Rule:
    """Definition of a behavioral detection rule"""

    name: str
    description: str
    risk_points: int
    check_function: Callable
    cooldown_minutes: int = 5  # Don't trigger same rule within this period


class RuleEngine:
    """
    Evaluates behavioral rules against user telemetry events.

    Usage:
        engine = RuleEngine()
        violations = engine.evaluate_user(user_id)
        for violation in violations:
            print(f"Rule: {violation['rule']}, Points: {violation['points']}")
    """

    def __init__(self):
        self.rules = self._build_rules()

    def _build_rules(self) -> List[Rule]:
        """Define all behavioral detection rules"""
        return [
            Rule(
                name="fast_navigation",
                description="User is navigating through tasks unusually fast",
                risk_points=10,
                check_function=self._check_fast_navigation,
                cooldown_minutes=5,
            ),
            Rule(
                name="excessive_zoom",
                description="Unusual amount of zooming (potential screenshot prep)",
                risk_points=20,
                check_function=self._check_excessive_zoom,
                cooldown_minutes=2,
            ),
            Rule(
                name="bot_behavior",
                description="Dwell times too short to be human",
                risk_points=50,
                check_function=self._check_bot_behavior,
                cooldown_minutes=10,
            ),
            Rule(
                name="devtools_copy",
                description="DevTools opened with copy attempts",
                risk_points=30,
                check_function=self._check_devtools_copy,
                cooldown_minutes=5,
            ),
            Rule(
                name="vm_detected",
                description="Running in virtual machine or remote desktop",
                risk_points=20,
                check_function=self._check_vm_detected,
                cooldown_minutes=60,  # Only flag once per hour
            ),
            Rule(
                name="screenshot_attempt",
                description="Print screen or screenshot key pressed",
                risk_points=40,
                check_function=self._check_screenshot_attempt,
                cooldown_minutes=1,
            ),
            Rule(
                name="copy_attempts",
                description="Multiple copy attempts detected",
                risk_points=25,
                check_function=self._check_copy_attempts,
                cooldown_minutes=5,
            ),
            Rule(
                name="context_menu_spam",
                description="Repeated right-click attempts (trying to bypass)",
                risk_points=15,
                check_function=self._check_context_menu_spam,
                cooldown_minutes=5,
            ),
            Rule(
                name="headless_browser",
                description="Headless browser detected (automation)",
                risk_points=100,
                check_function=self._check_headless_browser,
                cooldown_minutes=60,
            ),
            Rule(
                name="tab_switching",
                description="Frequent tab switching during task viewing",
                risk_points=10,
                check_function=self._check_tab_switching,
                cooldown_minutes=5,
            ),
        ]

    def evaluate_user(self, user_id: int, window_minutes: int = 10) -> List[dict]:
        """
        Evaluate all rules for a user based on recent events.

        Args:
            user_id: User to evaluate
            window_minutes: Time window to consider

        Returns:
            List of violations: [{'rule': name, 'points': int, 'data': dict}]
        """
        from .models import TelemetryEvent, RuleViolation

        violations = []
        cutoff = timezone.now() - timedelta(minutes=window_minutes)

        # Get recent events for this user
        events = TelemetryEvent.objects.filter(
            user_id=user_id, timestamp__gte=cutoff
        ).order_by("-timestamp")

        if not events.exists():
            return violations

        for rule in self.rules:
            # Check cooldown - don't trigger if recently triggered
            recent_violation = RuleViolation.objects.filter(
                user_id=user_id,
                rule_name=rule.name,
                timestamp__gte=timezone.now()
                - timedelta(minutes=rule.cooldown_minutes),
            ).exists()

            if recent_violation:
                continue

            # Evaluate the rule
            try:
                result = rule.check_function(events, user_id)
                if result:
                    violations.append(
                        {
                            "rule": rule.name,
                            "description": rule.description,
                            "points": rule.risk_points,
                            "data": result if isinstance(result, dict) else {},
                        }
                    )
            except Exception as e:
                logger.error(f"Error evaluating rule {rule.name}: {e}")

        return violations

    # ========== Rule Check Functions ==========

    def _check_fast_navigation(self, events, user_id) -> Optional[dict]:
        """Check if user is viewing images too fast (>50 per minute)"""
        one_minute_ago = timezone.now() - timedelta(minutes=1)

        view_count = events.filter(
            event_type="dwell", timestamp__gte=one_minute_ago
        ).count()

        if view_count > 50:
            return {"views_per_minute": view_count}
        return None

    def _check_excessive_zoom(self, events, user_id) -> Optional[dict]:
        """Check for excessive zoom events (>30 in 10 seconds)"""
        ten_seconds_ago = timezone.now() - timedelta(seconds=10)

        zoom_count = events.filter(
            event_type="zoom", timestamp__gte=ten_seconds_ago
        ).count()

        if zoom_count > 30:
            return {"zooms_in_10s": zoom_count}
        return None

    def _check_bot_behavior(self, events, user_id) -> Optional[dict]:
        """Check for inhuman dwell times (<200ms repeatedly)"""
        dwell_events = events.filter(event_type="dwell")[:20]

        short_dwells = 0
        for event in dwell_events:
            dwell_ms = event.value.get("duration_ms", 1000)
            if dwell_ms < 200:
                short_dwells += 1

        # If more than 80% of recent dwells are too short
        if dwell_events.count() >= 10 and short_dwells / dwell_events.count() > 0.8:
            return {"short_dwell_ratio": short_dwells / dwell_events.count()}
        return None

    def _check_devtools_copy(self, events, user_id) -> Optional[dict]:
        """Check for DevTools + copy attempt combination"""
        five_minutes_ago = timezone.now() - timedelta(minutes=5)

        devtools_open = events.filter(
            event_type="devtools", timestamp__gte=five_minutes_ago
        ).exists()

        copy_attempts = events.filter(
            event_type="copy", timestamp__gte=five_minutes_ago
        ).count()

        if devtools_open and copy_attempts > 0:
            return {"devtools": True, "copy_attempts": copy_attempts}
        return None

    def _check_vm_detected(self, events, user_id) -> Optional[dict]:
        """Check if VM/RDP was detected"""
        vm_events = events.filter(event_type="vm_detected")[:1]

        if vm_events.exists():
            return {"vm_detected": True, "data": vm_events[0].value}
        return None

    def _check_screenshot_attempt(self, events, user_id) -> Optional[dict]:
        """Check for print screen key presses"""
        one_minute_ago = timezone.now() - timedelta(minutes=1)

        screenshot_count = events.filter(
            event_type="printscreen", timestamp__gte=one_minute_ago
        ).count()

        if screenshot_count > 0:
            return {"screenshot_attempts": screenshot_count}
        return None

    def _check_copy_attempts(self, events, user_id) -> Optional[dict]:
        """Check for multiple copy attempts"""
        five_minutes_ago = timezone.now() - timedelta(minutes=5)

        copy_count = events.filter(
            event_type="copy", timestamp__gte=five_minutes_ago
        ).count()

        if copy_count >= 5:
            return {"copy_attempts": copy_count}
        return None

    def _check_context_menu_spam(self, events, user_id) -> Optional[dict]:
        """Check for repeated right-click attempts"""
        one_minute_ago = timezone.now() - timedelta(minutes=1)

        context_count = events.filter(
            event_type="contextmenu", timestamp__gte=one_minute_ago
        ).count()

        if context_count >= 10:
            return {"context_menu_attempts": context_count}
        return None

    def _check_headless_browser(self, events, user_id) -> Optional[dict]:
        """Check if headless browser was detected"""
        headless_events = events.filter(event_type="headless")[:1]

        if headless_events.exists():
            return {"headless": True, "data": headless_events[0].value}
        return None

    def _check_tab_switching(self, events, user_id) -> Optional[dict]:
        """Check for frequent tab switching"""
        one_minute_ago = timezone.now() - timedelta(minutes=1)

        blur_count = events.filter(
            event_type="blur", timestamp__gte=one_minute_ago
        ).count()

        if blur_count >= 20:
            return {"tab_switches": blur_count}
        return None


# Global instance
rule_engine = RuleEngine()
