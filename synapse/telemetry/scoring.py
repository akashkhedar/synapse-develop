"""
Risk Scoring Engine - Cumulative Risk Assessment

Manages user risk profiles and applies risk-based actions.
"""

import logging
from typing import Optional, List
from datetime import timedelta

from django.utils import timezone
from django.db import transaction

logger = logging.getLogger(__name__)


class RiskScorer:
    """
    Manages user risk scores based on rule violations.

    Risk Levels:
        0-25: Low (normal behavior)
        26-50: Medium (monitored)
        51-100: High (flagged, potential action)
        100+: Critical (immediate action)
    """

    # Risk decay: points to remove per hour of good behavior
    DECAY_RATE_PER_HOUR = 5

    # Maximum risk score
    MAX_RISK_SCORE = 200

    def get_or_create_profile(self, user_id: int):
        """Get or create a risk profile for user"""
        from .models import UserRiskProfile

        profile, created = UserRiskProfile.objects.get_or_create(
            user_id=user_id,
            defaults={
                "risk_score": 0,
                "risk_level": "low",
                "triggered_rules": [],
            },
        )

        if created:
            logger.info(f"Created risk profile for user {user_id}")

        return profile

    def add_violation(
        self, user_id: int, rule_name: str, risk_points: int, trigger_data: dict = None
    ) -> "UserRiskProfile":
        """
        Add a rule violation to user's risk profile.

        Args:
            user_id: User who violated the rule
            rule_name: Name of the violated rule
            risk_points: Points to add
            trigger_data: Data that triggered the violation

        Returns:
            Updated UserRiskProfile
        """
        from .models import UserRiskProfile, RuleViolation

        with transaction.atomic():
            profile = self.get_or_create_profile(user_id)

            # Add risk points
            profile.add_risk(risk_points, rule_name)
            profile.risk_score = min(profile.risk_score, self.MAX_RISK_SCORE)
            profile.save()

            # Record the violation
            RuleViolation.objects.create(
                user_id=user_id,
                rule_name=rule_name,
                risk_points=risk_points,
                trigger_data=trigger_data or {},
            )

            logger.warning(
                f"Risk violation: user={user_id}, rule={rule_name}, "
                f"points=+{risk_points}, total={profile.risk_score}, level={profile.risk_level}"
            )

        return profile

    def process_violations(
        self, user_id: int, violations: List[dict]
    ) -> "UserRiskProfile":
        """
        Process multiple violations at once.

        Args:
            user_id: User to process
            violations: List of {'rule': name, 'points': int, 'data': dict}

        Returns:
            Updated UserRiskProfile
        """
        profile = self.get_or_create_profile(user_id)

        for violation in violations:
            profile = self.add_violation(
                user_id=user_id,
                rule_name=violation["rule"],
                risk_points=violation["points"],
                trigger_data=violation.get("data", {}),
            )

        return profile

    def decay_risks(self, hours_since_last_event: float = 1.0):
        """
        Decay risk scores for users who have been inactive.

        Call this periodically (e.g., every hour via cron/celery)
        """
        from .models import UserRiskProfile

        decay_points = int(self.DECAY_RATE_PER_HOUR * hours_since_last_event)
        if decay_points < 1:
            return

        # Find profiles that haven't had events recently
        cutoff = timezone.now() - timedelta(hours=hours_since_last_event)

        profiles = UserRiskProfile.objects.filter(
            risk_score__gt=0, last_event_at__lt=cutoff
        )

        decayed_count = 0
        for profile in profiles:
            profile.decay_risk(decay_points)
            profile.save()
            decayed_count += 1

        if decayed_count > 0:
            logger.info(
                f"Decayed risk for {decayed_count} users by {decay_points} points"
            )

    def get_high_risk_users(self, min_level: str = "high") -> List["UserRiskProfile"]:
        """Get all users at or above a risk level"""
        from .models import UserRiskProfile

        levels = ["low", "medium", "high", "critical"]
        min_index = levels.index(min_level)
        target_levels = levels[min_index:]

        return (
            UserRiskProfile.objects.filter(risk_level__in=target_levels)
            .select_related("user")
            .order_by("-risk_score")
        )

    def get_user_risk_summary(self, user_id: int) -> dict:
        """Get a summary of user's risk status"""
        from .models import RuleViolation

        profile = self.get_or_create_profile(user_id)

        recent_violations = (
            RuleViolation.objects.filter(
                user_id=user_id, timestamp__gte=timezone.now() - timedelta(hours=24)
            )
            .values("rule_name")
            .annotate(count=models.Count("id"))
        )

        return {
            "user_id": user_id,
            "risk_score": profile.risk_score,
            "risk_level": profile.risk_level,
            "is_frozen": profile.is_frozen,
            "triggered_rules": profile.triggered_rules,
            "last_violation": profile.last_violation_at,
            "recent_violations": list(recent_violations),
        }


# Global instance
risk_scorer = RiskScorer()
