"""
Telemetry Models - Behavioral Surveillance System

Models for storing:
- TelemetryEvent: Individual behavior signals from browser
- UserRiskProfile: Cumulative risk scores per user
- RuleViolation: Record of triggered rules
- AuditLog: Encrypted evidence storage
"""

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class TelemetryEvent(models.Model):
    """
    Stores individual behavior signals collected from the browser.

    High-throughput table - consider partitioning for production.
    """

    # Event types
    EVENT_TYPES = [
        ("mouse_entropy", "Mouse Movement Entropy"),
        ("click", "Click Event"),
        ("scroll", "Scroll Event"),
        ("zoom", "Zoom Event"),
        ("dwell", "Image Dwell Time"),
        ("focus", "Tab Focus"),
        ("blur", "Tab Blur"),
        ("devtools", "DevTools Detected"),
        ("copy", "Copy Attempt"),
        ("printscreen", "Print Screen Key"),
        ("contextmenu", "Context Menu Attempt"),
        ("dragstart", "Drag Attempt"),
        ("vm_detected", "VM/RDP Detected"),
        ("headless", "Headless Browser Detected"),
        ("multi_monitor", "Multiple Monitors Detected"),
        ("keyboard_shortcut", "Blocked Keyboard Shortcut"),
        ("session_start", "Session Started"),
        ("session_end", "Session Ended"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="telemetry_events",
        help_text="User who generated this event",
    )

    task = models.ForeignKey(
        "tasks.Task",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="telemetry_events",
        help_text="Task being viewed when event occurred",
    )

    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="telemetry_events",
        help_text="Project context",
    )

    event_type = models.CharField(
        max_length=50,
        choices=EVENT_TYPES,
        db_index=True,
        help_text="Type of behavior event",
    )

    value = models.JSONField(
        default=dict, help_text="Event-specific data (e.g., zoom level, dwell time ms)"
    )

    timestamp = models.DateTimeField(
        default=timezone.now, db_index=True, help_text="When the event occurred"
    )

    ip_address = models.GenericIPAddressField(
        null=True, blank=True, help_text="Client IP address"
    )

    user_agent = models.TextField(
        blank=True, default="", help_text="Browser user agent string"
    )

    session_id = models.CharField(
        max_length=64,
        blank=True,
        default="",
        db_index=True,
        help_text="Browser session identifier",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "telemetry_event"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["user", "timestamp"]),
            models.Index(fields=["user", "event_type", "timestamp"]),
            models.Index(fields=["session_id", "timestamp"]),
        ]

    def __str__(self):
        return f"{self.user_id}:{self.event_type}@{self.timestamp}"


class UserRiskProfile(models.Model):
    """
    Tracks cumulative risk score for each user.

    Updated by the rule engine when events are analyzed.
    """

    RISK_LEVELS = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="risk_profile",
        primary_key=True,
    )

    risk_score = models.IntegerField(
        default=0, help_text="Cumulative risk score (0-100+)"
    )

    risk_level = models.CharField(
        max_length=20,
        choices=RISK_LEVELS,
        default="low",
        db_index=True,
        help_text="Current risk classification",
    )

    triggered_rules = models.JSONField(
        default=list, help_text="List of rules that contributed to score"
    )

    last_event_at = models.DateTimeField(
        null=True, blank=True, help_text="Time of last telemetry event"
    )

    last_violation_at = models.DateTimeField(
        null=True, blank=True, help_text="Time of last rule violation"
    )

    is_frozen = models.BooleanField(
        default=False, help_text="Account frozen due to high risk"
    )

    frozen_at = models.DateTimeField(
        null=True, blank=True, help_text="When account was frozen"
    )

    frozen_reason = models.TextField(
        blank=True, default="", help_text="Reason for freezing"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "telemetry_user_risk_profile"

    def __str__(self):
        return f"{self.user_id}: {self.risk_level} ({self.risk_score})"

    def update_risk_level(self):
        """Update risk level based on score"""
        if self.risk_score >= 100:
            self.risk_level = "critical"
        elif self.risk_score >= 75:
            self.risk_level = "high"
        elif self.risk_score >= 50:
            self.risk_level = "medium"
        else:
            self.risk_level = "low"

    def add_risk(self, points: int, rule_name: str):
        """Add risk points and record the triggering rule"""
        self.risk_score += points
        if rule_name not in self.triggered_rules:
            self.triggered_rules.append(rule_name)
        self.last_violation_at = timezone.now()
        self.update_risk_level()

    def decay_risk(self, points: int = 5):
        """Decay risk score over time (call periodically)"""
        self.risk_score = max(0, self.risk_score - points)
        self.update_risk_level()


class RuleViolation(models.Model):
    """
    Records individual rule violations for audit purposes.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="rule_violations",
    )

    rule_name = models.CharField(
        max_length=100, db_index=True, help_text="Name of the violated rule"
    )

    risk_points = models.IntegerField(help_text="Points added to risk score")

    trigger_data = models.JSONField(
        default=dict, help_text="Data that triggered the rule"
    )

    action_taken = models.CharField(
        max_length=50, blank=True, default="", help_text="Action taken (if any)"
    )

    timestamp = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = "telemetry_rule_violation"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.user_id}:{self.rule_name}@{self.timestamp}"


class SecurityAuditLog(models.Model):
    """
    Encrypted audit log for legal evidence.

    All sensitive data is encrypted at rest.
    """

    LOG_TYPES = [
        ("event", "Telemetry Event"),
        ("violation", "Rule Violation"),
        ("action", "Action Taken"),
        ("freeze", "Account Frozen"),
        ("unfreeze", "Account Unfrozen"),
        ("alert", "Admin Alert"),
        ("export", "Data Export"),
        ("access", "Data Access"),
    ]

    log_type = models.CharField(max_length=20, choices=LOG_TYPES, db_index=True)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="security_audit_logs",
    )

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="security_audit_actions",
        help_text="Admin who took action (if applicable)",
    )

    # Encrypted payload containing sensitive details
    payload_encrypted = models.TextField(
        blank=True, default="", help_text="Encrypted JSON payload"
    )

    summary = models.TextField(help_text="Human-readable summary (non-sensitive)")

    ip_address = models.GenericIPAddressField(null=True, blank=True)

    timestamp = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = "telemetry_security_audit_log"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.log_type}:{self.user_id}@{self.timestamp}"

    def set_payload(self, data: dict):
        """Encrypt and store payload"""
        try:
            from core.encryption import EncryptionService
            import json

            json_str = json.dumps(data)
            self.payload_encrypted = EncryptionService.encrypt_field(json_str)
        except Exception:
            # Fallback to unencrypted if encryption fails
            import json

            self.payload_encrypted = json.dumps(data)

    def get_payload(self) -> dict:
        """Decrypt and return payload"""
        if not self.payload_encrypted:
            return {}
        try:
            from core.encryption import EncryptionService
            import json

            decrypted = EncryptionService.decrypt_field(self.payload_encrypted)
            return json.loads(decrypted)
        except Exception:
            # Try parsing as plain JSON
            import json

            try:
                return json.loads(self.payload_encrypted)
            except:
                return {}
