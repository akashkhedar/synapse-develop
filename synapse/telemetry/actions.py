"""
Action Engine - Automated Response System

Takes actions based on user risk levels:
- Medium: Log warning, notify admins
- High: Force visibility, rate limit
- Critical: Force logout, freeze account
"""

import logging
from typing import Optional, List
from datetime import datetime

from django.utils import timezone
from django.contrib.auth import logout
from django.db import transaction

logger = logging.getLogger(__name__)


class ActionEngine:
    """
    Executes automated actions based on risk levels.

    Action Thresholds:
        50+: Medium - Log and notify
        75+: High - Enhanced monitoring
        100+: Critical - Force logout, freeze account
    """

    # Risk thresholds for actions
    THRESHOLD_NOTIFY = 50
    THRESHOLD_ENHANCED = 75
    THRESHOLD_CRITICAL = 100

    def evaluate_and_act(self, user_id: int, profile=None) -> List[dict]:
        """
        Evaluate user risk and take appropriate actions.

        Args:
            user_id: User to evaluate
            profile: Optional UserRiskProfile (will fetch if not provided)

        Returns:
            List of actions taken
        """
        from .models import UserRiskProfile, SecurityAuditLog
        from .scoring import risk_scorer

        if profile is None:
            profile = risk_scorer.get_or_create_profile(user_id)

        actions_taken = []

        # Critical threshold - immediate action
        if profile.risk_score >= self.THRESHOLD_CRITICAL:
            actions = self._handle_critical(profile)
            actions_taken.extend(actions)

        # High threshold - enhanced monitoring
        elif profile.risk_score >= self.THRESHOLD_ENHANCED:
            actions = self._handle_high(profile)
            actions_taken.extend(actions)

        # Medium threshold - notify admins
        elif profile.risk_score >= self.THRESHOLD_NOTIFY:
            actions = self._handle_medium(profile)
            actions_taken.extend(actions)

        # Log all actions to audit vault
        for action in actions_taken:
            self._log_action(profile.user_id, action)

        return actions_taken

    def _handle_medium(self, profile) -> List[dict]:
        """Handle medium risk level"""
        actions = []

        # Log warning
        logger.warning(
            f"MEDIUM RISK: User {profile.user_id} has risk score {profile.risk_score}. "
            f"Triggered rules: {profile.triggered_rules}"
        )

        actions.append(
            {
                "type": "log_warning",
                "level": "medium",
                "message": f"User reached medium risk threshold",
            }
        )

        # Notify admins (async)
        self._notify_admins(profile, "medium")
        actions.append(
            {
                "type": "notify_admins",
                "level": "medium",
            }
        )

        return actions

    def _handle_high(self, profile) -> List[dict]:
        """Handle high risk level"""
        actions = []

        logger.warning(
            f"HIGH RISK: User {profile.user_id} has risk score {profile.risk_score}. "
            f"Enhanced monitoring activated."
        )

        actions.append(
            {
                "type": "enhanced_monitoring",
                "level": "high",
                "message": "Enhanced monitoring activated",
            }
        )

        # Notify admins urgently
        self._notify_admins(profile, "high")
        actions.append(
            {
                "type": "notify_admins",
                "level": "high",
                "urgent": True,
            }
        )

        return actions

    def _handle_critical(self, profile) -> List[dict]:
        """Handle critical risk level - take immediate action"""
        actions = []

        logger.critical(
            f"CRITICAL RISK: User {profile.user_id} has risk score {profile.risk_score}. "
            f"Freezing account!"
        )

        # Freeze the account
        if not profile.is_frozen:
            self._freeze_account(profile)
            actions.append(
                {
                    "type": "freeze_account",
                    "level": "critical",
                    "message": "Account frozen due to suspicious behavior",
                }
            )

        # Force logout all sessions
        self._force_logout(profile.user_id)
        actions.append(
            {
                "type": "force_logout",
                "level": "critical",
            }
        )

        # Notify admins immediately
        self._notify_admins(profile, "critical")
        actions.append(
            {
                "type": "notify_admins",
                "level": "critical",
                "urgent": True,
            }
        )

        return actions

    def _freeze_account(self, profile):
        """Freeze a user account"""
        with transaction.atomic():
            profile.is_frozen = True
            profile.frozen_at = timezone.now()
            profile.frozen_reason = (
                f"Automatic freeze: Risk score {profile.risk_score} exceeded critical threshold. "
                f"Triggered rules: {', '.join(profile.triggered_rules)}"
            )
            profile.save()

            # Also deactivate the user
            user = profile.user
            user.is_active = False
            user.save(update_fields=["is_active"])

            logger.critical(f"Account frozen: user_id={profile.user_id}")

    def _force_logout(self, user_id: int):
        """Force logout user from all sessions"""
        try:
            from django.contrib.sessions.models import Session
            from django.contrib.auth import get_user_model

            User = get_user_model()
            user = User.objects.get(pk=user_id)

            # Delete all sessions for this user
            # This is a simplified approach - production might use session backend
            sessions = Session.objects.filter(expire_date__gte=timezone.now())
            for session in sessions:
                data = session.get_decoded()
                if data.get("_auth_user_id") == str(user_id):
                    session.delete()

            logger.warning(f"Force logged out user: {user_id}")
        except Exception as e:
            logger.error(f"Failed to force logout user {user_id}: {e}")

    def _notify_admins(self, profile, level: str):
        """Notify admin users about risk event"""
        try:
            from django.contrib.auth import get_user_model
            from django.core.mail import send_mail
            from django.conf import settings

            User = get_user_model()

            # Get admin emails
            admins = User.objects.filter(is_staff=True, is_active=True)
            admin_emails = [u.email for u in admins if u.email]

            if not admin_emails:
                logger.warning("No admin emails found for notification")
                return

            subject = f"[{level.upper()}] Security Alert: User {profile.user_id}"
            message = (
                f"Security Alert\n"
                f"==============\n\n"
                f"Level: {level.upper()}\n"
                f"User ID: {profile.user_id}\n"
                f"Risk Score: {profile.risk_score}\n"
                f"Triggered Rules: {', '.join(profile.triggered_rules)}\n"
                f"Time: {timezone.now()}\n\n"
                f"Please review the user's activity in the admin panel."
            )

            # Send async if possible, otherwise log
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    admin_emails,
                    fail_silently=True,
                )
            except Exception:
                logger.info(f"Admin notification: {subject}")

        except Exception as e:
            logger.error(f"Failed to notify admins: {e}")

    def _log_action(self, user_id: int, action: dict):
        """Log action to audit vault"""
        from .models import SecurityAuditLog

        try:
            log = SecurityAuditLog(
                log_type="action",
                user_id=user_id,
                summary=f"Action: {action['type']} (level: {action.get('level', 'unknown')})",
            )
            log.set_payload(action)
            log.save()
        except Exception as e:
            logger.error(f"Failed to log action: {e}")

    def unfreeze_account(self, user_id: int, actor_id: int, reason: str):
        """
        Unfreeze a user account (admin action).

        Args:
            user_id: User to unfreeze
            actor_id: Admin performing the action
            reason: Reason for unfreezing
        """
        from .models import UserRiskProfile, SecurityAuditLog
        from django.contrib.auth import get_user_model

        User = get_user_model()

        with transaction.atomic():
            profile = UserRiskProfile.objects.get(user_id=user_id)

            # Unfreeze the profile
            profile.is_frozen = False
            profile.risk_score = 0  # Reset risk score
            profile.triggered_rules = []
            profile.save()

            # Reactivate the user
            user = User.objects.get(pk=user_id)
            user.is_active = True
            user.save(update_fields=["is_active"])

            # Log the action
            log = SecurityAuditLog(
                log_type="unfreeze",
                user_id=user_id,
                actor_id=actor_id,
                summary=f"Account unfrozen by admin {actor_id}: {reason}",
            )
            log.set_payload(
                {
                    "reason": reason,
                    "previous_score": profile.risk_score,
                }
            )
            log.save()

            logger.info(f"Account unfrozen: user_id={user_id} by admin={actor_id}")


# Global instance
action_engine = ActionEngine()
