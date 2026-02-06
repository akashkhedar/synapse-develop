"""
Accuracy Tracker Service v2.0

Maintains DUAL accuracy tracking for annotators:
1. LIFETIME ACCURACY on AnnotatorProfile.accuracy_score
   - Calculated from ALL honeypots ever evaluated
   - Provides fair long-term assessment
   - Used for overall quality metrics

2. ROLLING ACCURACY on TrustLevel.rolling_accuracy
   - Calculated from LAST N honeypots (window size)
   - Provides responsive recent performance view
   - Used for warning decisions

This dual approach balances:
- Fairness (lifetime doesn't punish long-term good performers)
- Responsiveness (rolling catches recent quality drops)
"""

import logging
from collections import deque
from decimal import Decimal
from typing import Optional, Dict, Any, List

from django.db import transaction
from django.db.models import Avg, F
from django.utils import timezone

from .models import (
    AnnotatorProfile,
    TrustLevel,
    HoneypotAssignment,
    AccuracyHistory,
)
from .honeypot_constants import ROLLING_WINDOW_SIZE
from .warning_system import WarningSystem

logger = logging.getLogger(__name__)


class AccuracyTracker:
    """
    Tracks and updates annotator accuracy metrics.
    
    Maintains both lifetime and rolling accuracy for fair assessment
    while remaining responsive to quality changes.
    """
    
    @classmethod
    @transaction.atomic
    def record_evaluation(
        cls,
        profile: AnnotatorProfile,
        trust_level: TrustLevel,
        accuracy_score: float,
        passed: bool
    ) -> Dict[str, Any]:
        """
        Record a honeypot evaluation result and update accuracies.
        
        Args:
            profile: The annotator's profile
            trust_level: The project-specific trust level
            accuracy_score: The accuracy from this evaluation (0-100)
            passed: Whether the evaluation passed tolerance
            
        Returns:
            Dict with updated accuracy metrics
        """
        old_lifetime = float(profile.accuracy_score or 0)
        old_rolling = float(trust_level.rolling_accuracy or 0)
        old_count = profile.total_honeypots_evaluated or 0
        
        # Update lifetime accuracy (incremental average)
        new_lifetime = cls._calculate_new_lifetime_accuracy(
            current_accuracy=old_lifetime,
            current_count=old_count,
            new_score=accuracy_score
        )
        
        # Update rolling accuracy (last N honeypots)
        new_rolling = cls._calculate_new_rolling_accuracy(
            profile=profile,
            new_score=accuracy_score
        )
        
        # Save updates to profile
        profile.accuracy_score = Decimal(str(round(new_lifetime, 2)))
        profile.total_honeypots_evaluated = old_count + 1
        profile.save(update_fields=['accuracy_score', 'total_honeypots_evaluated'])
        
        # Save updates to trust level
        trust_level.rolling_accuracy = Decimal(str(round(new_rolling, 2)))
        trust_level.save(update_fields=['rolling_accuracy'])
        
        logger.info(
            f"Updated accuracy for {profile.user.email}: "
            f"lifetime={old_lifetime:.1f}→{new_lifetime:.1f}%, "
            f"rolling={old_rolling:.1f}→{new_rolling:.1f}%"
        )
        
        # Check if warning should be issued (based on rolling accuracy)
        warning = WarningSystem.check_and_warn(profile, trust_level)
        
        return {
            'lifetime_accuracy': new_lifetime,
            'rolling_accuracy': new_rolling,
            'total_evaluated': old_count + 1,
            'previous_lifetime': old_lifetime,
            'previous_rolling': old_rolling,
            'warning_issued': warning is not None,
            'warning_level': warning.warning_type if warning else None,
        }
    
    @classmethod
    def _calculate_new_lifetime_accuracy(
        cls,
        current_accuracy: float,
        current_count: int,
        new_score: float
    ) -> float:
        """
        Calculate new lifetime accuracy using incremental average.
        
        Formula: new_avg = (old_avg * old_count + new_value) / (old_count + 1)
        
        This avoids needing to recalculate from all historical data.
        """
        if current_count == 0:
            return new_score
        
        total = current_accuracy * current_count + new_score
        return total / (current_count + 1)
    
    @classmethod
    def _calculate_new_rolling_accuracy(
        cls,
        profile: AnnotatorProfile,
        new_score: float
    ) -> float:
        """
        Calculate rolling accuracy from last N honeypot evaluations.
        
        Queries the most recent ROLLING_WINDOW_SIZE evaluated honeypots
        and calculates their average accuracy.
        """
        # Get recent evaluated honeypots for this profile
        recent_scores = list(
            HoneypotAssignment.objects.filter(
                annotator=profile,
                status='evaluated',
                accuracy_score__isnull=False,
            )
            .order_by('-submitted_at')
            .values_list('accuracy_score', flat=True)
            [:ROLLING_WINDOW_SIZE - 1]  # Leave room for new score
        )
        
        # Add the new score
        all_scores = [new_score] + [float(s) for s in recent_scores]
        
        # Calculate average of available scores (up to window size)
        scores_for_average = all_scores[:ROLLING_WINDOW_SIZE]
        
        if not scores_for_average:
            return new_score
        
        return sum(scores_for_average) / len(scores_for_average)
    
    @classmethod
    def recalculate_lifetime_accuracy(cls, profile: AnnotatorProfile) -> float:
        """
        Recalculate lifetime accuracy from all historical data.
        
        Use this for data consistency checks or after data corrections.
        Normally, incremental updates are used for efficiency.
        """
        result = HoneypotAssignment.objects.filter(
            annotator=profile,
            status='evaluated',
            accuracy_score__isnull=False,
        ).aggregate(
            avg_score=Avg('accuracy_score'),
            total_count=Count('id')
        )
        
        avg_score = result['avg_score'] or 0
        total_count = result['total_count'] or 0
        
        # Update profile
        profile.accuracy_score = Decimal(str(round(float(avg_score), 2)))
        profile.total_honeypots_evaluated = total_count
        profile.save(update_fields=['accuracy_score', 'total_honeypots_evaluated'])
        
        logger.info(
            f"Recalculated lifetime accuracy for {profile.user.email}: "
            f"{avg_score:.2f}% from {total_count} evaluations"
        )
        
        return float(avg_score)
    
    @classmethod
    def recalculate_rolling_accuracy(
        cls,
        profile: AnnotatorProfile,
        trust_level: TrustLevel
    ) -> float:
        """
        Recalculate rolling accuracy from recent data.
        
        Use this for data consistency checks or after data corrections.
        """
        result = HoneypotAssignment.objects.filter(
            annotator=profile,
            status='evaluated',
            accuracy_score__isnull=False,
        ).order_by('-submitted_at')[:ROLLING_WINDOW_SIZE].aggregate(
            avg_score=Avg('accuracy_score')
        )
        
        avg_score = result['avg_score'] or 0
        
        trust_level.rolling_accuracy = Decimal(str(round(float(avg_score), 2)))
        trust_level.save(update_fields=['rolling_accuracy'])
        
        logger.info(
            f"Recalculated rolling accuracy for {profile.user.email}: "
            f"{avg_score:.2f}%"
        )
        
        return float(avg_score)
    
    @classmethod
    def snapshot_daily_accuracy(cls, profile: AnnotatorProfile):
        """
        Create a daily snapshot of accuracy metrics for historical tracking.
        
        Called by a scheduled job to maintain accuracy history.
        """
        # Get current trust levels
        trust_level = TrustLevel.objects.filter(
            annotator=profile
        ).order_by('-last_accuracy_update').first()
        
        AccuracyHistory.objects.create(
            annotator=profile,
            date=timezone.now().date(),
            lifetime_accuracy=profile.accuracy_score or Decimal('0'),
            rolling_accuracy=trust_level.rolling_accuracy if trust_level else Decimal('0'),
            honeypots_evaluated=profile.total_honeypots_evaluated or 0,
        )
        
        logger.debug(
            f"Created daily accuracy snapshot for {profile.user.email}"
        )
    
    @classmethod
    def get_accuracy_trend(
        cls,
        profile: AnnotatorProfile,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get accuracy trend over the specified number of days.
        
        Returns list of daily snapshots for trend analysis.
        """
        from_date = timezone.now().date() - timezone.timedelta(days=days)
        
        history = AccuracyHistory.objects.filter(
            annotator=profile,
            date__gte=from_date,
        ).order_by('date').values(
            'date',
            'lifetime_accuracy',
            'rolling_accuracy',
            'honeypots_evaluated',
        )
        
        return list(history)
    
    @classmethod
    def get_accuracy_summary(cls, profile: AnnotatorProfile) -> Dict[str, Any]:
        """
        Get comprehensive accuracy summary for an annotator.
        """
        # Get current trust level
        trust_level = TrustLevel.objects.filter(
            annotator=profile
        ).order_by('-last_accuracy_update').first()
        
        # Get warning summary
        warning_summary = WarningSystem.get_warning_summary(profile)
        
        # Get recent trend (last 7 days)
        recent_trend = cls.get_accuracy_trend(profile, days=7)
        
        # Calculate trend direction
        trend = 'stable'
        if len(recent_trend) >= 2:
            first = float(recent_trend[0].get('rolling_accuracy', 0))
            last = float(recent_trend[-1].get('rolling_accuracy', 0))
            if last > first + 5:
                trend = 'improving'
            elif last < first - 5:
                trend = 'declining'
        
        return {
            'lifetime_accuracy': float(profile.accuracy_score or 0),
            'rolling_accuracy': float(trust_level.rolling_accuracy or 0) if trust_level else 0,
            'total_honeypots': profile.total_honeypots_evaluated or 0,
            'rolling_window_size': ROLLING_WINDOW_SIZE,
            'trend': trend,
            'warnings': warning_summary,
        }


# Missing import for recalculation method
from django.db.models import Count
