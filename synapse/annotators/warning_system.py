"""
Warning System Service v2.0

Monitors annotator accuracy and issues tiered warnings based on rolling accuracy.
Uses the last N honeypots (rolling window) to determine warning level.

Warning Tiers:
1. Soft Warning (70%): Coaching email, no penalty
2. Formal Warning (60%): Recorded warning, supervisor notified  
3. Final Warning (50%): Last chance, possible reduced assignments
4. Suspension (40%): Account suspended from new assignments

Warnings are based on ROLLING accuracy (recent performance), not lifetime.
This allows annotators to recover quickly from poor performance.
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, Dict, Any, Tuple

from django.db import transaction
from django.db.models import F
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

from .models import AnnotatorProfile, TrustLevel, AnnotatorWarning
from .honeypot_constants import (
    WARNING_THRESHOLDS,
    WARNING_COOLDOWN_DAYS,
    ROLLING_WINDOW_SIZE,
)

logger = logging.getLogger(__name__)


class WarningLevel:
    """Warning level constants."""
    HEALTHY = 'healthy'
    SOFT_WARNING = 'soft_warning'
    FORMAL_WARNING = 'formal_warning'
    FINAL_WARNING = 'final_warning'
    SUSPENDED = 'suspended'
    
    @classmethod
    def get_severity(cls, level: str) -> int:
        """Get numeric severity for comparison."""
        severity_map = {
            cls.HEALTHY: 0,
            cls.SOFT_WARNING: 1,
            cls.FORMAL_WARNING: 2,
            cls.FINAL_WARNING: 3,
            cls.SUSPENDED: 4,
        }
        return severity_map.get(level, 0)


class WarningSystem:
    """
    System for monitoring and warning annotators about quality issues.
    
    Uses rolling accuracy (recent performance) to determine warning level.
    Issues tiered warnings with email notifications.
    """
    
    # Email templates
    EMAIL_TEMPLATES = {
        WarningLevel.SOFT_WARNING: {
            'subject': 'Quality Feedback: Opportunities for Improvement',
            'body': '''
Dear {name},

We noticed your recent annotation accuracy has dropped to {accuracy:.1f}%.

This is a friendly reminder to review the annotation guidelines and take 
extra care with your submissions. Quality is important to us and our clients.

If you need help or have questions about any annotation types, please don't 
hesitate to reach out to your project supervisor.

Key tips:
- Take your time with each annotation
- When uncertain, refer to the project guidelines
- Use the skip option if a task is unclear

This is not a formal warning - just an opportunity to improve.

Best regards,
The Quality Assurance Team
            ''',
        },
        WarningLevel.FORMAL_WARNING: {
            'subject': 'Formal Warning: Quality Below Standards',
            'body': '''
Dear {name},

Your recent annotation accuracy has dropped to {accuracy:.1f}%, which is 
below our acceptable threshold of {threshold}%.

This is a FORMAL WARNING. Please take immediate steps to improve your 
annotation quality:

1. Review the project annotation guidelines carefully
2. Take additional time to ensure accuracy
3. If confused about any annotation type, contact your supervisor

Your performance is being monitored. Continued quality issues may result 
in reduced assignments or suspension.

Warning Details:
- Current Rolling Accuracy: {accuracy:.1f}%
- Required Minimum: {threshold}%
- Warning Count: {warning_count}

Please respond to this email acknowledging that you've received this warning.

Regards,
The Quality Assurance Team
            ''',
        },
        WarningLevel.FINAL_WARNING: {
            'subject': 'FINAL WARNING: Immediate Improvement Required',
            'body': '''
Dear {name},

This is your FINAL WARNING.

Your annotation accuracy has dropped to {accuracy:.1f}%, well below the 
acceptable threshold. Despite previous warnings, your quality has not improved.

IMMEDIATE ACTION REQUIRED:
- Stop current work and review ALL project guidelines
- Contact your supervisor before continuing any annotations
- Only resume work when you are confident in the requirements

Further quality issues WILL result in suspension from the platform.

Warning Details:
- Current Rolling Accuracy: {accuracy:.1f}%
- Required Minimum: {threshold}%
- Total Warnings Issued: {warning_count}

This is your last opportunity to improve before suspension.

Regards,
The Quality Assurance Team
            ''',
        },
        WarningLevel.SUSPENDED: {
            'subject': 'Account Suspended: Quality Standards Not Met',
            'body': '''
Dear {name},

Your annotator account has been SUSPENDED due to persistent quality issues.

Despite multiple warnings, your annotation accuracy remains at {accuracy:.1f}%, 
which is unacceptable for our platform standards.

What this means:
- You will not receive new task assignments
- Current tasks may be reassigned to other annotators
- Your account is under review

If you believe this is in error or wish to appeal, please contact 
support@synapse.ai with your case.

Suspension Details:
- Final Accuracy: {accuracy:.1f}%
- Minimum Required: {threshold}%
- Total Warnings Received: {warning_count}

Regards,
The Quality Assurance Team
            ''',
        },
    }
    
    @classmethod
    def check_and_warn(
        cls,
        profile: AnnotatorProfile,
        trust_level: TrustLevel
    ) -> Optional[AnnotatorWarning]:
        """
        Check annotator's rolling accuracy and issue warning if needed.
        
        Args:
            profile: The annotator's profile
            trust_level: The trust level with rolling accuracy
            
        Returns:
            AnnotatorWarning if a new warning was issued, None otherwise
        """
        rolling_accuracy = float(trust_level.rolling_accuracy or 0)
        
        # Skip if not enough honeypots evaluated yet
        if profile.total_honeypots_evaluated < 5:
            logger.debug(
                f"Skipping warning check for {profile.user.email}: "
                f"only {profile.total_honeypots_evaluated} honeypots evaluated"
            )
            return None
        
        # Determine current warning level
        current_level = cls._determine_warning_level(rolling_accuracy)
        
        if current_level == WarningLevel.HEALTHY:
            logger.debug(f"{profile.user.email} is in healthy accuracy range")
            return None
        
        # Check if we should issue a warning
        should_warn, reason = cls._should_issue_warning(
            profile, trust_level, current_level
        )
        
        if not should_warn:
            logger.debug(f"Skipping warning for {profile.user.email}: {reason}")
            return None
        
        # Issue the warning
        return cls._issue_warning(profile, trust_level, current_level)
    
    @classmethod
    def _determine_warning_level(cls, rolling_accuracy: float) -> str:
        """Determine warning level based on rolling accuracy."""
        if rolling_accuracy >= WARNING_THRESHOLDS['healthy'] * 100:
            return WarningLevel.HEALTHY
        elif rolling_accuracy >= WARNING_THRESHOLDS['soft_warning'] * 100:
            return WarningLevel.SOFT_WARNING
        elif rolling_accuracy >= WARNING_THRESHOLDS['formal_warning'] * 100:
            return WarningLevel.FORMAL_WARNING
        elif rolling_accuracy >= WARNING_THRESHOLDS['final_warning'] * 100:
            return WarningLevel.FINAL_WARNING
        else:  # Below suspension threshold
            return WarningLevel.SUSPENDED
    
    @classmethod
    def _should_issue_warning(
        cls,
        profile: AnnotatorProfile,
        trust_level: TrustLevel,
        current_level: str
    ) -> Tuple[bool, str]:
        """
        Check if a warning should be issued.
        
        Returns:
            (should_warn, reason) tuple
        """
        # Get most recent warning
        last_warning = AnnotatorWarning.objects.filter(
            annotator=profile
        ).order_by('-created_at').first()
        
        if not last_warning:
            # First warning - always issue
            return True, "First warning"
        
        # Check cooldown period
        cooldown_end = last_warning.created_at + timedelta(
            days=WARNING_COOLDOWN_DAYS
        )
        
        if timezone.now() < cooldown_end:
            # Within cooldown - only escalate if severity increased
            last_severity = WarningLevel.get_severity(last_warning.warning_type)
            current_severity = WarningLevel.get_severity(current_level)
            
            if current_severity > last_severity:
                return True, "Escalating warning level"
            else:
                return False, f"Within cooldown period (ends {cooldown_end})"
        
        # Past cooldown - issue if still in warning range
        return True, "Cooldown period passed"
    
    @classmethod
    @transaction.atomic
    def _issue_warning(
        cls,
        profile: AnnotatorProfile,
        trust_level: TrustLevel,
        warning_level: str
    ) -> AnnotatorWarning:
        """
        Issue a warning to the annotator.
        
        Creates warning record and sends notification email.
        """
        rolling_accuracy = float(trust_level.rolling_accuracy or 0)
        
        # Get warning count
        warning_count = AnnotatorWarning.objects.filter(
            annotator=profile
        ).count() + 1
        
        # Create warning record
        warning = AnnotatorWarning.objects.create(
            annotator=profile,
            warning_type=warning_level,
            accuracy_at_warning=Decimal(str(rolling_accuracy)),
            message=f"Rolling accuracy dropped to {rolling_accuracy:.1f}%",
            acknowledged=False,
        )
        
        logger.warning(
            f"Issued {warning_level} to {profile.user.email}: "
            f"accuracy={rolling_accuracy:.1f}%"
        )
        
        # Send email notification
        cls._send_warning_email(
            profile,
            warning_level,
            rolling_accuracy,
            warning_count
        )
        
        # If suspended, update trust level
        if warning_level == WarningLevel.SUSPENDED:
            cls._suspend_annotator(profile, trust_level)
        
        return warning
    
    @classmethod
    def _send_warning_email(
        cls,
        profile: AnnotatorProfile,
        warning_level: str,
        accuracy: float,
        warning_count: int
    ):
        """Send warning email to annotator."""
        template = cls.EMAIL_TEMPLATES.get(warning_level)
        if not template:
            logger.error(f"No email template for warning level: {warning_level}")
            return
        
        # Get threshold for this level
        threshold_key = warning_level.replace('_warning', '')
        if warning_level == WarningLevel.SUSPENDED:
            threshold_key = 'suspension'
        threshold = WARNING_THRESHOLDS.get(threshold_key, 0.5) * 100
        
        # Format email
        user = profile.user
        name = user.first_name or user.email.split('@')[0]
        
        subject = template['subject']
        body = template['body'].format(
            name=name,
            accuracy=accuracy,
            threshold=threshold,
            warning_count=warning_count,
        )
        
        try:
            send_mail(
                subject=subject,
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            
            # Update warning record with email sent
            AnnotatorWarning.objects.filter(
                annotator=profile,
                warning_type=warning_level,
            ).update(email_sent=True)
            
            logger.info(f"Sent {warning_level} email to {user.email}")
            
        except Exception as e:
            logger.error(f"Failed to send warning email to {user.email}: {e}")
    
    @classmethod
    def _suspend_annotator(cls, profile: AnnotatorProfile, trust_level: TrustLevel):
        """
        Suspend an annotator from receiving new assignments.
        
        This is done by setting can_receive_assignments to False.
        """
        # Mark as suspended on trust level
        trust_level.can_receive_assignments = False
        trust_level.save(update_fields=['can_receive_assignments'])
        
        logger.warning(
            f"SUSPENDED annotator {profile.user.email} from assignments"
        )
        
        # TODO: Optionally reassign their current pending tasks
    
    @classmethod
    def check_recovery(cls, profile: AnnotatorProfile, trust_level: TrustLevel) -> bool:
        """
        Check if a previously warned annotator has recovered.
        
        If rolling accuracy returns to healthy levels and they were suspended,
        consider lifting the suspension (may require manual review).
        
        Returns:
            True if recovery detected
        """
        rolling_accuracy = float(trust_level.rolling_accuracy or 0)
        healthy_threshold = WARNING_THRESHOLDS['healthy'] * 100
        
        if rolling_accuracy >= healthy_threshold:
            # Check if they were suspended
            last_warning = AnnotatorWarning.objects.filter(
                annotator=profile,
                warning_type=WarningLevel.SUSPENDED,
            ).order_by('-created_at').first()
            
            if last_warning and not trust_level.can_receive_assignments:
                logger.info(
                    f"Recovery detected for {profile.user.email}: "
                    f"accuracy improved to {rolling_accuracy:.1f}%"
                )
                
                # For now, just log it. Manual review may be required.
                # Auto-unsuspension could be a future feature.
                return True
        
        return False
    
    @classmethod
    def get_warning_summary(cls, profile: AnnotatorProfile) -> Dict[str, Any]:
        """Get summary of warnings for an annotator."""
        warnings = AnnotatorWarning.objects.filter(
            annotator=profile
        ).order_by('-created_at')
        
        return {
            'total_warnings': warnings.count(),
            'soft_warnings': warnings.filter(
                warning_type=WarningLevel.SOFT_WARNING
            ).count(),
            'formal_warnings': warnings.filter(
                warning_type=WarningLevel.FORMAL_WARNING
            ).count(),
            'final_warnings': warnings.filter(
                warning_type=WarningLevel.FINAL_WARNING
            ).count(),
            'suspensions': warnings.filter(
                warning_type=WarningLevel.SUSPENDED
            ).count(),
            'latest_warning': warnings.first(),
            'is_suspended': warnings.filter(
                warning_type=WarningLevel.SUSPENDED
            ).exists() and not profile.trustlevels.first().can_receive_assignments
            if hasattr(profile, 'trustlevels') else False,
        }
    
    @classmethod
    def acknowledge_warning(cls, warning: AnnotatorWarning) -> bool:
        """
        Mark a warning as acknowledged by the annotator.
        
        Returns:
            True if acknowledgement was recorded
        """
        if warning.acknowledged:
            return False
        
        warning.acknowledged = True
        warning.acknowledged_at = timezone.now()
        warning.save(update_fields=['acknowledged', 'acknowledged_at'])
        
        logger.info(
            f"Warning {warning.id} acknowledged by {warning.annotator.user.email}"
        )
        
        return True
