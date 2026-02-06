"""Annotator models for workforce management"""

from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone
from tasks.models import Task
from projects.models import Project
import secrets
import string
import uuid
from tasks.models import Annotation
from django.db.models import Q
from users.models import User


class AnnotatorProfile(models.Model):
    """Profile for annotators in the platform"""

    STATUS_CHOICES = [
        ("pending_verification", "Pending Email Verification"),
        ("pending_test", "Pending Test"),
        ("test_submitted", "Test Submitted"),
        ("under_review", "Under Review"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("suspended", "Suspended"),
    ]

    EXPERIENCE_CHOICES = [
        ("beginner", "Beginner"),
        ("intermediate", "Intermediate"),
        ("expert", "Expert"),
    ]

    # User relationship
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="annotator_profile"
    )

    verification_token = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )
    verification_token_created = models.DateTimeField(default=timezone.now)

    email_verified = models.BooleanField(default=False)
    status = models.CharField(max_length=32, default="pending_verification")

    # Personal Information
    phone = models.CharField(max_length=20, blank=True)
    alternate_email = models.EmailField(blank=True)
    address = models.TextField(blank=True)

    # Skills & Qualifications
    skills = models.JSONField(default=list, help_text="List of annotation skills")
    languages = models.JSONField(default=list, help_text="Languages spoken")
    experience_level = models.CharField(
        max_length=20, choices=EXPERIENCE_CHOICES, default="beginner"
    )
    bio = models.TextField(blank=True, help_text="Brief introduction")

    # Performance Metrics
    total_tasks_completed = models.IntegerField(default=0)
    accuracy_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.0,
        help_text="Cached metric, updated asynchronously",
    )
    average_time_per_task = models.IntegerField(
        default=0, help_text="Average seconds per task"
    )
    rejection_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.0, help_text="Percentage"
    )
    
    # Honeypot tracking (v2)
    total_honeypots_evaluated = models.IntegerField(
        default=0,
        help_text="Total number of honeypot evaluations (lifetime)"
    )

    # Earnings
    total_earned = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    pending_approval = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    available_balance = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.0
    )
    total_withdrawn = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    # Bank Details (will be encrypted in production)
    bank_name = models.CharField(max_length=100, blank=True)
    account_number = models.CharField(max_length=50, blank=True)
    ifsc_code = models.CharField(max_length=20, blank=True)
    account_holder_name = models.CharField(max_length=100, blank=True)
    upi_id = models.CharField(max_length=100, blank=True)

    # Timestamps
    applied_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    last_active = models.DateTimeField(null=True, blank=True)

    # Activity tracking for assignment system
    is_active_for_assignments = models.BooleanField(
        default=True,
        help_text="Whether annotator should receive new task assignments. "
                  "Set to False when annotator is inactive for extended period."
    )
    inactive_since = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When annotator was marked inactive due to prolonged absence"
    )

    # Rejection reason
    rejection_reason = models.TextField(blank=True)

    class Meta:
        db_table = "annotator_profile"
        verbose_name = "Annotator Profile"
        verbose_name_plural = "Annotator Profiles"
        ordering = ["-applied_at"]

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.status}"

    def generate_verification_token(self):
        self.verification_token = uuid.uuid4()
        self.verification_token_created = timezone.now()
        self.save(update_fields=["verification_token", "verification_token_created"])
        return self.verification_token

    def verify_email(self):
        self.email_verified = True

        if self.status == "pending_verification":
            self.status = "pending_test"

        self.save(update_fields=["email_verified", "status"])

    @property
    def can_take_test(self):
        """Check if annotator can take the test"""
        return self.email_verified and self.status == "pending_test"

    @property
    def is_active_annotator(self):
        """Check if annotator is approved and can work"""
        return self.status == "approved"

    @property
    def is_eligible_for_assignments(self):
        """Check if annotator is eligible to receive task assignments"""
        return (
            self.status == "approved" 
            and self.user.is_active 
            and self.is_active_for_assignments
        )

    def mark_inactive(self):
        """Mark annotator as inactive due to prolonged absence"""
        self.is_active_for_assignments = False
        self.inactive_since = timezone.now()
        self.save(update_fields=['is_active_for_assignments', 'inactive_since'])

    def reactivate_on_login(self):
        """Reactivate annotator when they login after being inactive"""
        if not self.is_active_for_assignments:
            self.is_active_for_assignments = True
            self.inactive_since = None
        self.last_active = timezone.now()
        self.save(update_fields=['is_active_for_assignments', 'inactive_since', 'last_active'])

    def update_last_active(self):
        """Update last activity timestamp"""
        self.last_active = timezone.now()
        self.save(update_fields=['last_active'])


class AnnotationTest(models.Model):
    """Test for new annotators"""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("submitted", "Submitted"),
        ("passed", "Passed"),
        ("failed", "Failed"),
    ]

    annotator = models.ForeignKey(
        AnnotatorProfile, on_delete=models.CASCADE, related_name="tests"
    )

    # Test Configuration
    test_type = models.CharField(max_length=50, default="general")
    test_tasks = models.JSONField(
        default=list, help_text="List of task IDs or test data"
    )
    
    # Expertise linking - which expertise this test is for
    expertise_category = models.CharField(
        max_length=100,
        blank=True,
        help_text="Selected expertise category (e.g., 'computer-vision')"
    )
    expertise_specialization = models.CharField(
        max_length=100,
        blank=True,
        help_text="Selected specialization (e.g., 'chest-x-ray')"
    )
    selected_expertise = models.JSONField(
        default=dict,
        blank=True,
        help_text="Full expertise selection data from frontend"
    )

    # Test Execution
    started_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    annotations = models.JSONField(default=dict, help_text="Annotator test results")

    # Evaluation
    evaluated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="evaluated_tests",
    )
    evaluated_at = models.DateTimeField(null=True, blank=True)

    accuracy = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    feedback = models.TextField(blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    # Detailed Scores
    scores = models.JSONField(default=dict, help_text="Detailed scoring breakdown")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "annotation_test"
        constraints = [
            models.UniqueConstraint(
                fields=["annotator"],
                condition=Q(status__in=["pending", "in_progress"]),
                name="one_active_test_per_annotator",
            )
        ]

    def __str__(self):
        return f"Test for {self.annotator.user.username} - {self.status}"


class ProjectAssignment(models.Model):
    """System-controlled assignment of annotators to projects"""

    ROLE_CHOICES = [
        ("annotator", "Annotator"),
        ("reviewer", "Reviewer"),
    ]

    # Relationships
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="annotator_assignments"
    )
    annotator = models.ForeignKey(
        AnnotatorProfile, on_delete=models.CASCADE, related_name="project_assignments"
    )

    # Assignment details
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="annotator")
    active = models.BooleanField(default=True)

    # System tracking
    assigned_by = models.CharField(max_length=50, default="system")
    assigned_at = models.DateTimeField(auto_now_add=True)

    # Performance tracking
    assigned_tasks = models.IntegerField(
        default=0,
        help_text="Cached count, updated via signals",
    )
    completed_tasks = models.IntegerField(
        default=0, help_text="Total tasks completed in this project"
    )

    class Meta:
        db_table = "project_assignment"
        verbose_name = "Project Assignment"
        verbose_name_plural = "Project Assignments"
        unique_together = ("project", "annotator")
        ordering = ["-assigned_at"]

    def __str__(self):
        return f"{self.annotator.user.email} → Project {self.project.id} ({self.role})"

    @property
    def progress(self):
        """Calculate completion progress"""
        if self.assigned_tasks == 0:
            return "not_started"
        elif self.completed_tasks >= self.assigned_tasks:
            return "completed"
        else:
            return "in_progress"


class TaskAssignment(models.Model):
    STATUS_CHOICES = [
        ("assigned", "Assigned"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("rejected", "Rejected"),
        ("skipped", "Skipped"),
    ]

    annotator = models.ForeignKey(
        AnnotatorProfile,
        on_delete=models.CASCADE,
        related_name="task_assignments",
    )
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="annotator_assignments",
    )

    annotation = models.OneToOneField(
        Annotation,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="task_assignment",
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="assigned")

    assigned_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    # Payment tracking fields for escrow system
    base_payment = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.0, help_text="Base rate × complexity"
    )
    quality_multiplier = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=1.0,
        help_text="Quality score multiplier",
    )
    trust_multiplier = models.DecimalField(
        max_digits=4, decimal_places=2, default=1.0, help_text="Trust level multiplier"
    )

    # Escrow stages (40% immediate, 40% after consensus, 20% after review)
    immediate_payment = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.0
    )
    consensus_payment = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.0
    )
    review_payment = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    immediate_released = models.BooleanField(default=False)
    consensus_released = models.BooleanField(default=False)
    review_released = models.BooleanField(default=False)

    # Quality assessment
    quality_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="0-100 quality score",
    )
    consensus_agreement = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Agreement with other annotators",
    )
    time_spent_seconds = models.IntegerField(
        default=0, help_text="Time spent on annotation"
    )

    # Ground truth accuracy (calculated after expert approval)
    ground_truth_accuracy = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Accuracy against ground truth (0-100)",
    )
    accuracy_level = models.CharField(
        max_length=20,
        blank=True,
        help_text="Accuracy classification (excellent, good, acceptable, poor, very_poor)",
    )
    accuracy_bonus_multiplier = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=1.0,
        help_text="Bonus/penalty multiplier based on accuracy",
    )

    # Flags
    is_honeypot = models.BooleanField(
        default=False, help_text="Was this a honeypot task?"
    )
    honeypot_passed = models.BooleanField(
        null=True, blank=True, help_text="Did annotator pass the honeypot?"
    )
    flagged_for_review = models.BooleanField(default=False)
    flag_reason = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "task_assignment"
        verbose_name = "Task Assignment"
        verbose_name_plural = "Task Assignments"
        unique_together = ("annotator", "task")
        ordering = ["-assigned_at"]
        indexes = [
            models.Index(fields=["annotator", "status"]),
            models.Index(fields=["task"]),
            models.Index(fields=["status", "immediate_released"]),
            models.Index(fields=["status", "consensus_released"]),
        ]

    def calculate_payment(self, base_rate):
        """Calculate payment with all multipliers"""
        self.base_payment = (
            base_rate * self.task.complexity_score
            if hasattr(self.task, "complexity_score")
            else base_rate
        )
        self.immediate_payment = self.base_payment * Decimal("0.4")  # 40%
        self.consensus_payment = self.base_payment * Decimal("0.4")  # 40%
        self.review_payment = self.base_payment * Decimal("0.2")  # 20%
        self.save(
            update_fields=[
                "base_payment",
                "immediate_payment",
                "consensus_payment",
                "review_payment",
            ]
        )

    def release_immediate_payment(self):
        """Release 40% immediate payment upon submission (Stage 1)"""
        if not self.immediate_released and self.status == "completed":
            self.immediate_released = True
            final_amount = (
                self.immediate_payment * self.quality_multiplier * self.trust_multiplier
            )
            self.amount_paid += final_amount
            # Stage 1: Add to pending_approval AND total_earned
            self.annotator.pending_approval += final_amount
            self.annotator.total_earned += final_amount
            self.annotator.save(update_fields=["pending_approval", "total_earned"])
            self.save(update_fields=["immediate_released", "amount_paid"])
            return final_amount
        return Decimal("0")

    def release_consensus_payment(self):
        """Release 40% after consensus validation (Stage 2)"""
        if not self.consensus_released and self.immediate_released:
            self.consensus_released = True
            # Calculate consensus portion only
            consensus_final = (
                self.consensus_payment * self.quality_multiplier * self.trust_multiplier
            )
            # Calculate immediate portion that was in pending
            immediate_final = (
                self.immediate_payment * self.quality_multiplier * self.trust_multiplier
            )
            self.amount_paid += consensus_final
            
            # Stage 2: Move immediate from pending to available, add consensus to both
            self.annotator.pending_approval -= immediate_final
            self.annotator.available_balance += immediate_final + consensus_final
            self.annotator.total_earned += consensus_final  # Only add consensus portion
            self.annotator.save(
                update_fields=["pending_approval", "available_balance", "total_earned"]
            )
            self.save(update_fields=["consensus_released", "amount_paid"])
            return consensus_final
        return Decimal("0")

    def release_review_payment(self):
        """Release final 20% after client payment (Stage 3)"""
        if not self.review_released and self.consensus_released:
            self.review_released = True
            review_final = (
                self.review_payment * self.quality_multiplier * self.trust_multiplier
            )
            self.amount_paid += review_final
            # Stage 3: Add review portion to available and total_earned
            self.annotator.available_balance += review_final
            self.annotator.total_earned += review_final
            self.annotator.save(update_fields=["available_balance", "total_earned"])
            self.save(update_fields=["review_released", "amount_paid"])
            return review_final
        return Decimal("0")


class TrustLevel(models.Model):
    """Trust level progression for annotators"""

    LEVEL_CHOICES = [
        ("new", "New"),
        ("junior", "Junior"),
        ("regular", "Regular"),
        ("senior", "Senior"),
        ("expert", "Expert"),
    ]

    LEVEL_MULTIPLIERS = {
        "new": Decimal("0.8"),
        "junior": Decimal("1.0"),
        "regular": Decimal("1.1"),
        "senior": Decimal("1.3"),
        "expert": Decimal("1.5"),
    }

    LEVEL_THRESHOLDS = {
        "new": {"tasks": 0, "accuracy": 0, "honeypot_rate": 0},
        "junior": {"tasks": 50, "accuracy": 70, "honeypot_rate": 80},
        "regular": {"tasks": 200, "accuracy": 80, "honeypot_rate": 90},
        "senior": {"tasks": 500, "accuracy": 90, "honeypot_rate": 95},
        "expert": {"tasks": 1000, "accuracy": 95, "honeypot_rate": 98},
    }

    annotator = models.OneToOneField(
        AnnotatorProfile, on_delete=models.CASCADE, related_name="trust_level"
    )

    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default="new")
    multiplier = models.DecimalField(
        max_digits=4, decimal_places=2, default=Decimal("0.8")
    )

    # Metrics for level calculation
    tasks_completed = models.IntegerField(default=0)
    accuracy_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    honeypot_pass_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total_honeypots = models.IntegerField(default=0)
    passed_honeypots = models.IntegerField(default=0)

    # Ground truth accuracy metrics
    ground_truth_evaluations = models.IntegerField(
        default=0, help_text="Number of times compared against ground truth"
    )
    accuracy_history = models.JSONField(
        null=True, blank=True, help_text="Recent accuracy scores"
    )
    last_accuracy_update = models.DateTimeField(null=True, blank=True)
    
    # Rolling accuracy (for warning system - based on last N honeypots)
    rolling_accuracy = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Rolling window accuracy for warning decisions"
    )

    # Fraud indicators
    fraud_flags = models.IntegerField(default=0)
    last_fraud_check = models.DateTimeField(null=True, blank=True)
    is_suspended = models.BooleanField(default=False)
    suspension_reason = models.TextField(blank=True)

    # Timestamps
    level_updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "annotator_trust_level"
        verbose_name = "Trust Level"
        verbose_name_plural = "Trust Levels"

    def __str__(self):
        return f"{self.annotator.user.email} - {self.level} ({self.multiplier}x)"

    def update_metrics(self, task_assignment):
        """Update metrics after a task completion"""
        self.tasks_completed += 1

        # Update honeypot stats
        if task_assignment.is_honeypot:
            self.total_honeypots += 1
            if task_assignment.honeypot_passed:
                self.passed_honeypots += 1
            self.honeypot_pass_rate = (
                (self.passed_honeypots / self.total_honeypots) * 100
                if self.total_honeypots > 0
                else 0
            )

        # Update accuracy (weighted average)
        if task_assignment.quality_score:
            self.accuracy_score = (
                self.accuracy_score * (self.tasks_completed - 1)
                + task_assignment.quality_score
            ) / self.tasks_completed

        self.save()
        self.check_level_upgrade()

    def check_level_upgrade(self):
        """Check if annotator qualifies for level upgrade"""
        for level_name in ["expert", "senior", "regular", "junior", "new"]:
            thresholds = self.LEVEL_THRESHOLDS[level_name]
            if (
                self.tasks_completed >= thresholds["tasks"]
                and self.accuracy_score >= thresholds["accuracy"]
                and self.honeypot_pass_rate >= thresholds["honeypot_rate"]
            ):
                if self.level != level_name:
                    self.level = level_name
                    self.multiplier = self.LEVEL_MULTIPLIERS[level_name]
                    self.save(update_fields=["level", "multiplier", "level_updated_at"])
                break

    def add_fraud_flag(self, reason):
        """Add a fraud flag"""
        self.fraud_flags += 1
        if self.fraud_flags >= 3:
            self.is_suspended = True
            self.suspension_reason = f"Multiple fraud flags: {reason}"
        self.save()


class HoneypotTask(models.Model):
    """Honeypot tasks with known ground truth for quality control"""

    task = models.OneToOneField(
        Task, on_delete=models.CASCADE, related_name="honeypot_config"
    )

    ground_truth = models.JSONField(help_text="Expected annotation result")
    tolerance = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.8,
        help_text="Minimum agreement for pass (0-1)",
    )

    # Statistics
    times_shown = models.IntegerField(default=0)
    times_passed = models.IntegerField(default=0)
    times_failed = models.IntegerField(default=0)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_honeypots",
    )

    class Meta:
        db_table = "honeypot_task"
        verbose_name = "Honeypot Task"
        verbose_name_plural = "Honeypot Tasks"

    def __str__(self):
        return f"Honeypot for Task {self.task.id}"

    def evaluate_annotation(self, annotation_result):
        """Evaluate if annotation matches ground truth within tolerance"""
        from .payment_service import PaymentService

        score = PaymentService.calculate_annotation_agreement(
            annotation_result, self.ground_truth
        )
        passed = score >= float(self.tolerance)

        self.times_shown += 1
        if passed:
            self.times_passed += 1
        else:
            self.times_failed += 1
        self.save(update_fields=["times_shown", "times_passed", "times_failed"])

        return passed, score


class PayoutRequest(models.Model):
    """Payout/withdrawal requests from annotators"""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    ]

    PAYOUT_METHOD_CHOICES = [
        ("bank_transfer", "Bank Transfer"),
        ("upi", "UPI"),
    ]

    annotator = models.ForeignKey(
        AnnotatorProfile, on_delete=models.CASCADE, related_name="payout_requests"
    )

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    payout_method = models.CharField(
        max_length=20, choices=PAYOUT_METHOD_CHOICES, default="bank_transfer"
    )

    # Bank details snapshot (frozen at request time)
    bank_details = models.JSONField(
        default=dict, help_text="Bank details at time of request"
    )

    # Processing info
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="processed_payouts",
    )
    processed_at = models.DateTimeField(null=True, blank=True)

    # Transaction reference
    transaction_id = models.CharField(max_length=100, blank=True)
    failure_reason = models.TextField(blank=True)

    # Timestamps
    requested_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "payout_request"
        verbose_name = "Payout Request"
        verbose_name_plural = "Payout Requests"
        ordering = ["-requested_at"]

    def __str__(self):
        return f"Payout ₹{self.amount} - {self.annotator.user.email} ({self.status})"

    def approve(self, admin_user, transaction_id=""):
        """Approve and process the payout"""
        if self.status != "pending":
            raise ValueError(f"Cannot approve payout in {self.status} status")

        if self.annotator.available_balance < self.amount:
            raise ValueError("Insufficient balance")

        self.status = "processing"
        self.save(update_fields=["status"])

        # Deduct from balance
        self.annotator.available_balance -= self.amount
        self.annotator.total_withdrawn += self.amount
        self.annotator.save(update_fields=["available_balance", "total_withdrawn"])

        # Mark as completed
        self.status = "completed"
        self.processed_by = admin_user
        self.processed_at = timezone.now()
        self.transaction_id = transaction_id
        self.save(
            update_fields=["status", "processed_by", "processed_at", "transaction_id"]
        )

        return True

    def reject(self, admin_user, reason):
        """Reject the payout request"""
        if self.status != "pending":
            raise ValueError(f"Cannot reject payout in {self.status} status")

        self.status = "failed"
        self.failure_reason = reason
        self.processed_by = admin_user
        self.processed_at = timezone.now()
        self.save(
            update_fields=["status", "failure_reason", "processed_by", "processed_at"]
        )

        return True

    def cancel(self):
        """Cancel payout request by annotator"""
        if self.status != "pending":
            raise ValueError(f"Cannot cancel payout in {self.status} status")

        self.status = "cancelled"
        self.save(update_fields=["status"])
        return True


class EarningsTransaction(models.Model):
    """Transaction history for annotator earnings"""

    TRANSACTION_TYPE_CHOICES = [
        ("earning", "Earning"),
        ("bonus", "Bonus"),
        ("penalty", "Penalty"),
        ("withdrawal", "Withdrawal"),
        ("adjustment", "Adjustment"),
    ]

    EARNING_STAGE_CHOICES = [
        ("immediate", "Immediate (40%)"),
        ("consensus", "Consensus (40%)"),
        ("review", "Review (20%)"),
        ("full", "Full Payment"),
    ]

    annotator = models.ForeignKey(
        AnnotatorProfile, on_delete=models.CASCADE, related_name="earnings_transactions"
    )

    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    earning_stage = models.CharField(
        max_length=20, choices=EARNING_STAGE_CHOICES, null=True, blank=True
    )

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    balance_after = models.DecimalField(max_digits=10, decimal_places=2)

    # Related objects
    task_assignment = models.ForeignKey(
        TaskAssignment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )
    payout_request = models.ForeignKey(
        PayoutRequest,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )

    description = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "earnings_transaction"
        verbose_name = "Earnings Transaction"
        verbose_name_plural = "Earnings Transactions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["annotator", "-created_at"]),
            models.Index(fields=["transaction_type"]),
        ]

    def __str__(self):
        return f"{self.annotator.user.email} - {self.transaction_type} ₹{self.amount}"


# ============================================================================
# GAMIFICATION MODELS
# ============================================================================


class AnnotatorStreak(models.Model):
    """Track daily activity streaks for bonus rewards"""

    annotator = models.OneToOneField(
        AnnotatorProfile, on_delete=models.CASCADE, related_name="streak"
    )

    # Current streak
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)

    # Weekly stats
    tasks_this_week = models.IntegerField(default=0)
    week_start_date = models.DateField(null=True, blank=True)

    # Monthly stats
    tasks_this_month = models.IntegerField(default=0)
    month_start_date = models.DateField(null=True, blank=True)

    # Streak bonuses earned
    total_streak_bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "annotator_streak"
        verbose_name = "Annotator Streak"
        verbose_name_plural = "Annotator Streaks"

    def __str__(self):
        return f"{self.annotator.user.email} - {self.current_streak} day streak"

    def record_activity(self, activity_date=None):
        """Record daily activity and update streak"""
        from datetime import date, timedelta

        today = activity_date or date.today()

        if self.last_activity_date:
            days_diff = (today - self.last_activity_date).days

            if days_diff == 0:
                # Same day, no change to streak
                return self.current_streak
            elif days_diff == 1:
                # Consecutive day, increment streak
                self.current_streak += 1
            else:
                # Streak broken
                self.current_streak = 1
        else:
            # First activity
            self.current_streak = 1

        self.last_activity_date = today
        self.longest_streak = max(self.longest_streak, self.current_streak)

        # Update weekly stats
        week_start = today - timedelta(days=today.weekday())
        if self.week_start_date != week_start:
            self.week_start_date = week_start
            self.tasks_this_week = 0
        self.tasks_this_week += 1

        # Update monthly stats
        month_start = today.replace(day=1)
        if self.month_start_date != month_start:
            self.month_start_date = month_start
            self.tasks_this_month = 0
        self.tasks_this_month += 1

        self.save()
        return self.current_streak

    def get_streak_multiplier(self):
        """Get bonus multiplier based on current streak"""
        if self.current_streak >= 30:
            return Decimal("1.25")  # 25% bonus for 30+ day streak
        elif self.current_streak >= 14:
            return Decimal("1.15")  # 15% bonus for 14+ day streak
        elif self.current_streak >= 7:
            return Decimal("1.10")  # 10% bonus for 7+ day streak
        elif self.current_streak >= 3:
            return Decimal("1.05")  # 5% bonus for 3+ day streak
        return Decimal("1.0")


class Achievement(models.Model):
    """Predefined achievements for gamification"""

    CATEGORY_CHOICES = [
        ("volume", "Volume"),
        ("quality", "Quality"),
        ("streak", "Streak"),
        ("speed", "Speed"),
        ("special", "Special"),
    ]

    TIER_CHOICES = [
        ("bronze", "Bronze"),
        ("silver", "Silver"),
        ("gold", "Gold"),
        ("platinum", "Platinum"),
        ("diamond", "Diamond"),
    ]

    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    tier = models.CharField(max_length=20, choices=TIER_CHOICES)

    # Rewards
    bonus_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    badge_icon = models.CharField(max_length=100, blank=True)

    # Unlock requirements
    requirement_type = models.CharField(
        max_length=50, help_text="e.g., tasks_completed, accuracy_score"
    )
    requirement_value = models.DecimalField(max_digits=10, decimal_places=2)

    is_active = models.BooleanField(default=True)
    is_repeatable = models.BooleanField(
        default=False, help_text="Can be earned multiple times"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "achievement"
        verbose_name = "Achievement"
        verbose_name_plural = "Achievements"
        ordering = ["category", "tier"]

    def __str__(self):
        return f"{self.name} ({self.tier})"


class AnnotatorAchievement(models.Model):
    """Track achievements earned by annotators"""

    annotator = models.ForeignKey(
        AnnotatorProfile, on_delete=models.CASCADE, related_name="achievements"
    )
    achievement = models.ForeignKey(
        Achievement, on_delete=models.CASCADE, related_name="earned_by"
    )

    # When earned
    earned_at = models.DateTimeField(auto_now_add=True)
    times_earned = models.IntegerField(default=1)

    # Bonus applied
    bonus_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        db_table = "annotator_achievement"
        verbose_name = "Annotator Achievement"
        verbose_name_plural = "Annotator Achievements"
        unique_together = ["annotator", "achievement"]

    def __str__(self):
        return f"{self.annotator.user.email} - {self.achievement.name}"


class DailyLeaderboard(models.Model):
    """Daily leaderboard for competitive gamification"""

    date = models.DateField()
    annotator = models.ForeignKey(
        AnnotatorProfile, on_delete=models.CASCADE, related_name="leaderboard_entries"
    )

    # Daily stats
    tasks_completed = models.IntegerField(default=0)
    earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quality_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # Calculated rank
    rank = models.IntegerField(null=True, blank=True)

    # Bonus for top performers
    leaderboard_bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "daily_leaderboard"
        verbose_name = "Daily Leaderboard"
        verbose_name_plural = "Daily Leaderboards"
        unique_together = ["date", "annotator"]
        ordering = ["date", "rank"]
        indexes = [
            models.Index(fields=["date", "-tasks_completed"]),
            models.Index(fields=["date", "-earnings"]),
        ]

    def __str__(self):
        return f"{self.date} - #{self.rank or '?'} {self.annotator.user.email}"


class SkillBadge(models.Model):
    """Skill badges for specific annotation types"""

    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField()

    # Requirements
    annotation_type = models.CharField(max_length=50)
    required_tasks = models.IntegerField(default=100)
    required_accuracy = models.DecimalField(max_digits=5, decimal_places=2, default=85)

    # Multiplier when working on matching tasks
    skill_multiplier = models.DecimalField(
        max_digits=4, decimal_places=2, default=Decimal("1.15")
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "skill_badge"
        verbose_name = "Skill Badge"
        verbose_name_plural = "Skill Badges"

    def __str__(self):
        return f"{self.name} ({self.annotation_type})"


class AnnotatorSkillBadge(models.Model):
    """Track skill badges earned by annotators"""

    annotator = models.ForeignKey(
        AnnotatorProfile, on_delete=models.CASCADE, related_name="skill_badges"
    )
    skill_badge = models.ForeignKey(
        SkillBadge, on_delete=models.CASCADE, related_name="holders"
    )

    # Progress
    tasks_completed = models.IntegerField(default=0)
    current_accuracy = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_earned = models.BooleanField(default=False)

    earned_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "annotator_skill_badge"
        verbose_name = "Annotator Skill Badge"
        verbose_name_plural = "Annotator Skill Badges"
        unique_together = ["annotator", "skill_badge"]

    def __str__(self):
        status = (
            "✓"
            if self.is_earned
            else f"{self.tasks_completed}/{self.skill_badge.required_tasks}"
        )
        return f"{self.annotator.user.email} - {self.skill_badge.name} ({status})"

    def update_progress(self, task_quality_score):
        """Update progress toward earning badge"""
        self.tasks_completed += 1

        # Update rolling accuracy
        self.current_accuracy = (
            self.current_accuracy * (self.tasks_completed - 1)
            + Decimal(str(task_quality_score))
        ) / self.tasks_completed

        # Check if badge is now earned
        if (
            not self.is_earned
            and self.tasks_completed >= self.skill_badge.required_tasks
            and self.current_accuracy >= self.skill_badge.required_accuracy
        ):
            self.is_earned = True
            self.earned_at = timezone.now()

        self.save()
        return self.is_earned


class BonusPool(models.Model):
    """Bonus pool for special events or high-performance rewards"""

    POOL_TYPE_CHOICES = [
        ("daily_top", "Daily Top Performers"),
        ("weekly_top", "Weekly Top Performers"),
        ("quality_bonus", "Quality Bonus Pool"),
        ("referral", "Referral Bonus"),
        ("special_event", "Special Event"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    pool_type = models.CharField(max_length=30, choices=POOL_TYPE_CHOICES)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    # Pool funds
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    amount_distributed = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Distribution rules
    distribution_rules = models.JSONField(
        default=dict, help_text="JSON rules for distribution"
    )

    # Timing
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "bonus_pool"
        verbose_name = "Bonus Pool"
        verbose_name_plural = "Bonus Pools"
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.name} - ₹{self.total_amount}"

    @property
    def remaining_amount(self):
        return self.total_amount - self.amount_distributed


class BonusDistribution(models.Model):
    """Track bonus distributions from pools"""

    pool = models.ForeignKey(
        BonusPool, on_delete=models.CASCADE, related_name="distributions"
    )
    annotator = models.ForeignKey(
        AnnotatorProfile, on_delete=models.CASCADE, related_name="bonus_distributions"
    )

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(max_length=255)

    # Context
    rank = models.IntegerField(null=True, blank=True)
    metrics = models.JSONField(
        default=dict, help_text="Performance metrics used for distribution"
    )

    distributed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "bonus_distribution"
        verbose_name = "Bonus Distribution"
        verbose_name_plural = "Bonus Distributions"
        ordering = ["-distributed_at"]

    def __str__(self):
        return f"{self.annotator.user.email} - ₹{self.amount} from {self.pool.name}"


# ============================================================================
# CONSENSUS & CONSOLIDATION MODELS
# ============================================================================


class TaskConsensus(models.Model):
    """
    Track consensus state for tasks with multiple annotators.
    Stores the consolidated "ground truth" annotation after consensus is reached.
    """

    STATUS_CHOICES = [
        ("pending", "Pending"),  # Waiting for more annotations
        ("in_consensus", "In Consensus"),  # Consensus being calculated
        ("consensus_reached", "Consensus Reached"),  # Agreement achieved
        ("conflict", "Conflict"),  # Annotators disagree significantly
        ("review_required", "Review Required"),  # Needs expert review
        ("finalized", "Finalized"),  # Ground truth established
    ]

    task = models.OneToOneField(
        Task, on_delete=models.CASCADE, related_name="consensus"
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    # Consolidated annotation result (the "ground truth")
    consolidated_result = models.JSONField(
        null=True, blank=True, help_text="The merged/consolidated annotation result"
    )

    # Consensus metrics
    required_annotations = models.IntegerField(
        default=1, help_text="Number of annotations required for consensus"
    )
    current_annotations = models.IntegerField(
        default=0, help_text="Current number of completed annotations"
    )

    # Agreement scores
    average_agreement = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Average pairwise agreement score (0-100)",
    )
    min_agreement = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Minimum pairwise agreement",
    )
    max_agreement = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximum pairwise agreement",
    )

    # Consolidation method used
    consolidation_method = models.CharField(
        max_length=50,
        blank=True,
        help_text="Method used for consolidation (voting, union, intersection, etc.)",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    consensus_reached_at = models.DateTimeField(null=True, blank=True)
    finalized_at = models.DateTimeField(null=True, blank=True)

    # Expert review
    reviewed_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_consensus",
    )
    review_notes = models.TextField(blank=True)

    class Meta:
        db_table = "task_consensus"
        verbose_name = "Task Consensus"
        verbose_name_plural = "Task Consensus Records"
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["task", "status"]),
        ]

    def __str__(self):
        return f"Consensus for Task {self.task_id}: {self.status}"

    @property
    def is_complete(self):
        """Check if all required annotations are received"""
        return self.current_annotations >= self.required_annotations

    @property
    def needs_review(self):
        """Check if consensus needs expert review"""
        return self.status in ["conflict", "review_required"]


class AnnotatorAgreement(models.Model):
    """
    Track pairwise agreement between annotators on a task.
    Used for quality scoring and payment adjustments.
    """

    task_consensus = models.ForeignKey(
        TaskConsensus, on_delete=models.CASCADE, related_name="agreements"
    )

    # The two annotators being compared
    annotator_1 = models.ForeignKey(
        AnnotatorProfile, on_delete=models.CASCADE, related_name="agreements_as_first"
    )
    annotator_2 = models.ForeignKey(
        AnnotatorProfile, on_delete=models.CASCADE, related_name="agreements_as_second"
    )

    # Their respective task assignments
    assignment_1 = models.ForeignKey(
        TaskAssignment, on_delete=models.CASCADE, related_name="agreements_as_first"
    )
    assignment_2 = models.ForeignKey(
        TaskAssignment, on_delete=models.CASCADE, related_name="agreements_as_second"
    )

    # Agreement metrics
    agreement_score = models.DecimalField(
        max_digits=5, decimal_places=2, help_text="0-100 agreement score"
    )

    # Detailed metrics by annotation type
    iou_score = models.DecimalField(
        max_digits=7,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="IoU for bounding boxes/polygons (0-100)",
    )
    label_agreement = models.DecimalField(
        max_digits=7,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Label matching score (0-100)",
    )
    position_agreement = models.DecimalField(
        max_digits=7,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Position/coordinate agreement (0-100)",
    )

    # Metadata
    annotation_type = models.CharField(max_length=50, blank=True)
    comparison_details = models.JSONField(
        default=dict, blank=True, help_text="Detailed comparison breakdown"
    )

    calculated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "annotator_agreement"
        verbose_name = "Annotator Agreement"
        verbose_name_plural = "Annotator Agreements"
        unique_together = ("task_consensus", "annotator_1", "annotator_2")
        indexes = [
            models.Index(fields=["task_consensus"]),
            models.Index(fields=["annotator_1", "agreement_score"]),
            models.Index(fields=["annotator_2", "agreement_score"]),
        ]

    def __str__(self):
        return (
            f"Agreement: {self.annotator_1.user.email} vs {self.annotator_2.user.email} "
            f"= {self.agreement_score}%"
        )


class ConsensusQualityScore(models.Model):
    """
    Track individual annotator's quality score for a consensus task.
    Compares their annotation against the consolidated ground truth.
    """

    task_consensus = models.ForeignKey(
        TaskConsensus, on_delete=models.CASCADE, related_name="quality_scores"
    )
    task_assignment = models.OneToOneField(
        TaskAssignment, on_delete=models.CASCADE, related_name="consensus_quality"
    )
    annotator = models.ForeignKey(
        AnnotatorProfile, on_delete=models.CASCADE, related_name="consensus_scores"
    )

    # Quality score against consolidated result
    quality_score = models.DecimalField(
        max_digits=5, decimal_places=2, help_text="0-100 quality score"
    )

    # Component scores
    label_accuracy = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    position_accuracy = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    completeness_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )

    # Agreement with other annotators
    avg_peer_agreement = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Average agreement with other annotators",
    )

    # Impact on payment
    quality_multiplier = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=1.0,
        help_text="Multiplier applied to consensus payment",
    )
    consensus_payment_released = models.BooleanField(default=False)
    consensus_payment_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    calculated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "consensus_quality_score"
        verbose_name = "Consensus Quality Score"
        verbose_name_plural = "Consensus Quality Scores"
        indexes = [
            models.Index(fields=["annotator", "quality_score"]),
            models.Index(fields=["task_consensus"]),
        ]

    def __str__(self):
        return f"{self.annotator.user.email} - Task {self.task_consensus.task_id}: {self.quality_score}%"


# ============================================================================
# EXPERT REVIEW MODELS
# ============================================================================


class ExpertProfile(models.Model):
    """
    Profile for expert reviewers.
    Experts are assigned by admin and review consolidated annotations.
    They use the same UI as annotators but have elevated permissions.
    """

    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("suspended", "Suspended"),
    ]

    # User relationship - an expert can also be an annotator
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="expert_profile"
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    
    # NOTE: expertise_level removed - all experts are equal
    # NOTE: expertise_areas on hold for future implementation
    expertise_areas = models.JSONField(
        default=list,
        help_text="[ON HOLD] List of annotation types expert can review",
    )

    # Performance Metrics
    total_reviews_completed = models.IntegerField(default=0)
    total_approvals = models.IntegerField(default=0)
    total_rejections = models.IntegerField(default=0)
    total_corrections = models.IntegerField(default=0)
    average_review_time = models.IntegerField(
        default=0, help_text="Average seconds per review"
    )

    # Quality Metrics
    correction_accuracy = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.0,
        help_text="How often their corrections match ground truth",
    )
    consistency_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.0,
        help_text="Consistency across similar reviews",
    )

    # Earnings
    total_earned = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    pending_payout = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    available_balance = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.0
    )
    total_withdrawn = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    # Payment Configuration (per-expert customization)
    custom_base_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Custom base rate override (if null, uses default rates)",
    )
    custom_level_multiplier = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Custom level multiplier override",
    )
    minimum_payout = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=100.0,
        help_text="Minimum payout threshold in INR",
    )

    # Payment Method
    PAYMENT_METHOD_CHOICES = [
        ("bank_transfer", "Bank Transfer"),
        ("upi", "UPI"),
        ("paypal", "PayPal"),
    ]
    payment_method = models.CharField(
        max_length=20, choices=PAYMENT_METHOD_CHOICES, default="bank_transfer"
    )

    # Bank Details (can be shared with annotator profile if exists)
    bank_details = models.JSONField(
        default=dict,
        blank=True,
        help_text="Complete bank details stored securely",
    )
    bank_name = models.CharField(max_length=100, blank=True)
    account_number = models.CharField(max_length=50, blank=True)
    ifsc_code = models.CharField(max_length=20, blank=True)
    account_holder_name = models.CharField(max_length=100, blank=True)
    upi_id = models.CharField(max_length=100, blank=True)

    # Payment Statistics
    total_payouts_count = models.IntegerField(
        default=0, help_text="Total number of payouts processed"
    )
    total_payouts_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.0, help_text="Total amount paid out"
    )
    last_payout_at = models.DateTimeField(
        null=True, blank=True, help_text="Last successful payout date"
    )
    average_review_time = models.IntegerField(
        default=0, help_text="Average review time in seconds"
    )

    # Capacity - Based on number of concurrent tasks (not daily limit)
    max_concurrent_reviews = models.IntegerField(
        default=50, help_text="Maximum concurrent review tasks this expert can have"
    )
    current_workload = models.IntegerField(
        default=0, help_text="Current number of pending reviews"
    )
    
    # Activity Tracking (for timeout and staleness handling)
    is_active_for_assignments = models.BooleanField(
        default=True,
        help_text="Whether expert is currently active for receiving new reviews"
    )
    inactive_since = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When expert was marked inactive (for timeout handling)"
    )

    # Timestamps
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="experts_assigned",
    )
    last_active = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "expert_profile"
        verbose_name = "Expert Profile"
        verbose_name_plural = "Expert Profiles"
        ordering = ["-assigned_at"]

    def __str__(self):
        return f"Expert: {self.user.email} ({self.status})"

    @property
    def approval_rate(self):
        """Calculate approval rate"""
        total = self.total_approvals + self.total_rejections
        if total == 0:
            return Decimal("0")
        return Decimal(str((self.total_approvals / total) * 100))

    @property
    def is_available(self):
        """Check if expert can accept more reviews"""
        return (
            self.status == "active" 
            and self.is_active_for_assignments
            and self.current_workload < self.max_concurrent_reviews
        )
    
    @property
    def available_capacity(self):
        """Get remaining capacity for new reviews"""
        return max(0, self.max_concurrent_reviews - self.current_workload)
    
    @property
    def is_eligible_for_assignments(self):
        """Check if expert is eligible to receive new review assignments"""
        return (
            self.status == "active"
            and self.user.is_active
            and self.is_active_for_assignments
            and self.available_capacity > 0
        )
    
    def mark_inactive(self):
        """Mark expert as inactive - won't receive new reviews until login"""
        self.is_active_for_assignments = False
        self.inactive_since = timezone.now()
        self.save(update_fields=["is_active_for_assignments", "inactive_since"])
    
    def reactivate_on_login(self):
        """Reactivate expert when they log in"""
        self.is_active_for_assignments = True
        self.inactive_since = None
        self.last_active = timezone.now()
        self.save(update_fields=["is_active_for_assignments", "inactive_since", "last_active"])
    
    def update_last_active(self):
        """Update last_active timestamp"""
        self.last_active = timezone.now()
        self.save(update_fields=["last_active"])


class ExpertProjectAssignment(models.Model):
    """
    Assign experts to projects for review.
    Experts can be assigned to specific projects or all projects.
    """

    expert = models.ForeignKey(
        ExpertProfile, on_delete=models.CASCADE, related_name="project_assignments"
    )
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="expert_assignments"
    )

    # Assignment settings
    is_active = models.BooleanField(default=True)
    review_all_tasks = models.BooleanField(
        default=False, help_text="If true, expert reviews all tasks, not just conflicts"
    )
    sample_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("100"),
        help_text="Percentage of conflict tasks to assign to this expert",
    )

    # Priority
    priority = models.IntegerField(
        default=0, help_text="Higher priority experts get tasks first"
    )

    # Stats for this project
    tasks_reviewed = models.IntegerField(default=0)
    tasks_approved = models.IntegerField(default=0)
    tasks_rejected = models.IntegerField(default=0)

    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="expert_project_assignments",
    )

    class Meta:
        db_table = "expert_project_assignment"
        verbose_name = "Expert Project Assignment"
        verbose_name_plural = "Expert Project Assignments"
        unique_together = ("expert", "project")
        ordering = ["-priority", "-assigned_at"]

    def __str__(self):
        return f"{self.expert.user.email} → {self.project.title}"


class ExpertReviewTask(models.Model):
    """
    Tasks assigned to experts for review.
    Created when consensus shows high disagreement or random sampling.
    """

    STATUS_CHOICES = [
        ("pending", "Pending Review"),
        ("in_review", "In Review"),
        ("approved", "Approved"),
        ("rejected", "Rejected - Needs Rework"),
        ("corrected", "Corrected by Expert"),
        ("escalated", "Escalated to Lead"),
    ]

    REJECTION_REASON_CHOICES = [
        ("low_quality", "Low Quality Annotations"),
        ("disagreement", "High Annotator Disagreement"),
        ("incorrect_labels", "Incorrect Labels"),
        ("incomplete", "Incomplete Annotation"),
        ("ambiguous", "Ambiguous Data - Skip"),
        ("other", "Other"),
    ]

    # Core relationships
    expert = models.ForeignKey(
        ExpertProfile, on_delete=models.CASCADE, related_name="review_tasks"
    )
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, related_name="expert_reviews"
    )
    task_consensus = models.ForeignKey(
        "TaskConsensus", on_delete=models.CASCADE, related_name="expert_reviews"
    )
    project_assignment = models.ForeignKey(
        ExpertProjectAssignment,
        on_delete=models.CASCADE,
        related_name="review_tasks",
        null=True,
        blank=True,
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    # Assignment context
    assignment_reason = models.CharField(
        max_length=50,
        default="disagreement",
        help_text="Why this task was assigned (disagreement, random_sample, manual)",
    )
    disagreement_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Disagreement score that triggered review",
    )

    # Review details
    review_notes = models.TextField(blank=True)
    rejection_reason = models.CharField(
        max_length=50, choices=REJECTION_REASON_CHOICES, blank=True
    )

    # Expert's corrected result (if they made corrections)
    corrected_result = models.JSONField(
        null=True, blank=True, help_text="Expert's corrected annotation result"
    )
    correction_summary = models.TextField(
        blank=True, help_text="Summary of what was corrected"
    )

    # Time tracking
    assigned_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    review_time_seconds = models.IntegerField(default=0)

    # Payment
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    payment_released = models.BooleanField(default=False)

    class Meta:
        db_table = "expert_review_task"
        verbose_name = "Expert Review Task"
        verbose_name_plural = "Expert Review Tasks"
        unique_together = ("expert", "task")
        ordering = ["-assigned_at"]
        indexes = [
            models.Index(fields=["expert", "status"]),
            models.Index(fields=["task", "status"]),
            models.Index(fields=["status", "assigned_at"]),
        ]

    def __str__(self):
        return (
            f"Review: Task {self.task_id} by {self.expert.user.email} ({self.status})"
        )

    @property
    def is_overdue(self):
        """Check if review is overdue (more than 24 hours)"""
        if self.status not in ["pending", "in_review"]:
            return False
        from datetime import timedelta

        return timezone.now() > self.assigned_at + timedelta(hours=24)


class ExpertEarningsTransaction(models.Model):
    """Transaction history for expert earnings"""

    TRANSACTION_TYPE_CHOICES = [
        ("review_payment", "Review Payment"),
        ("correction_bonus", "Correction Bonus"),
        ("quality_bonus", "Quality Bonus"),
        ("withdrawal", "Withdrawal"),
        ("adjustment", "Adjustment"),
    ]

    expert = models.ForeignKey(
        ExpertProfile, on_delete=models.CASCADE, related_name="earnings_transactions"
    )

    transaction_type = models.CharField(max_length=30, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    balance_after = models.DecimalField(max_digits=10, decimal_places=2)

    # Related objects
    review_task = models.ForeignKey(
        ExpertReviewTask,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )

    description = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "expert_earnings_transaction"
        verbose_name = "Expert Earnings Transaction"
        verbose_name_plural = "Expert Earnings Transactions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["expert", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.expert.user.email} - {self.transaction_type}: ₹{self.amount}"


class ExpertPayoutRequest(models.Model):
    """Payout requests from experts"""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    ]

    expert = models.ForeignKey(
        ExpertProfile, on_delete=models.CASCADE, related_name="payout_requests"
    )

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    payout_method = models.CharField(max_length=20, default="bank_transfer")
    bank_details = models.JSONField(default=dict, help_text="Snapshot of bank details")

    transaction_id = models.CharField(max_length=100, blank=True)
    failure_reason = models.TextField(blank=True)

    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="processed_expert_payouts",
    )

    class Meta:
        db_table = "expert_payout_request"
        verbose_name = "Expert Payout Request"
        verbose_name_plural = "Expert Payout Requests"
        ordering = ["-requested_at"]

    def __str__(self):
        return f"{self.expert.user.email} - ₹{self.amount} ({self.status})"


class AnnotatorPerformanceHistory(models.Model):
    """
    Track historical changes to annotator performance metrics.
    Useful for monitoring trends and identifying issues.
    """

    METRIC_TYPE_CHOICES = [
        ("ground_truth_accuracy", "Ground Truth Accuracy"),
        ("honeypot_accuracy", "Honeypot Accuracy"),
        ("peer_agreement", "Peer Agreement"),
        ("level_change", "Trust Level Change"),
        ("fraud_flag", "Fraud Flag"),
    ]

    annotator = models.ForeignKey(
        AnnotatorProfile, on_delete=models.CASCADE, related_name="performance_history"
    )
    task = models.ForeignKey(
        Task, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )

    metric_type = models.CharField(max_length=30, choices=METRIC_TYPE_CHOICES)
    old_value = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    new_value = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    change_reason = models.TextField(blank=True)
    details = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "annotator_performance_history"
        verbose_name = "Annotator Performance History"
        verbose_name_plural = "Annotator Performance Histories"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["annotator", "-created_at"]),
            models.Index(fields=["metric_type", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.annotator.user.email} - {self.metric_type}: {self.old_value} → {self.new_value}"


class AnnotatorNotification(models.Model):
    """
    Notifications for annotators (review feedback, announcements, etc.)
    """

    NOTIFICATION_TYPE_CHOICES = [
        ("review_accepted", "Review Accepted"),
        ("review_rejected_reannotate", "Review Rejected - Re-annotation Required"),
        ("review_feedback", "Review Feedback"),
        ("payment_released", "Payment Released"),
        ("task_assigned", "Task Assigned"),
        ("achievement_unlocked", "Achievement Unlocked"),
        ("system_announcement", "System Announcement"),
        ("other", "Other"),
    ]

    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("urgent", "Urgent"),
    ]

    annotator = models.ForeignKey(
        AnnotatorProfile, on_delete=models.CASCADE, related_name="notifications"
    )

    notification_type = models.CharField(
        max_length=50, choices=NOTIFICATION_TYPE_CHOICES, default="other"
    )
    priority = models.CharField(
        max_length=20, choices=PRIORITY_CHOICES, default="medium"
    )

    title = models.CharField(max_length=255)
    message = models.TextField()

    # Related objects
    task = models.ForeignKey(
        Task,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="annotator_notifications",
    )
    project = models.ForeignKey(
        "projects.Project",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="annotator_notifications",
    )

    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    # Metadata
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "annotator_notification"
        verbose_name = "Annotator Notification"
        verbose_name_plural = "Annotator Notifications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["annotator", "-created_at"]),
            models.Index(fields=["annotator", "is_read"]),
            models.Index(fields=["notification_type"]),
        ]

    def __str__(self):
        return f"{self.annotator.user.email} - {self.title} ({'read' if self.is_read else 'unread'})"

    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=["is_read", "read_at"])


# =============================================================================
# HONEYPOT SYSTEM v2 MODELS
# =============================================================================


class GoldenStandardTask(models.Model):
    """
    Pre-annotated tasks with verified ground truth for quality control.
    
    These are tasks with known correct answers used to evaluate annotator accuracy.
    Annotators don't know which tasks are golden standards.
    """
    
    SOURCE_CHOICES = [
        ('expert', 'Expert Annotated'),
        ('client', 'Client Provided'),
        ('admin', 'Admin Curated'),
    ]
    
    # Link to original task
    task = models.OneToOneField(
        Task,
        on_delete=models.CASCADE,
        related_name='golden_standard'
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='golden_standards'
    )
    
    # The verified correct annotation (what we compare against)
    ground_truth = models.JSONField(
        help_text="Verified correct annotation result"
    )
    
    # Source tracking
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    source_annotation = models.ForeignKey(
        Annotation,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="Original annotation this was created from"
    )
    
    # Tolerance for matching (0.0 = exact match, 1.0 = any answer passes)
    # Default 0.85 = 85% match required to pass
    tolerance = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.85
    )
    
    # Usage statistics
    times_shown = models.IntegerField(default=0)
    times_passed = models.IntegerField(default=0)
    times_failed = models.IntegerField(default=0)
    average_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_golden_standards'
    )
    
    # Retirement (stop showing after too many uses to prevent memorization)
    max_uses = models.IntegerField(default=100)
    is_retired = models.BooleanField(default=False)
    retired_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'golden_standard_task'
        verbose_name = 'Golden Standard Task'
        verbose_name_plural = 'Golden Standard Tasks'
        indexes = [
            models.Index(fields=['project', 'is_active']),
            models.Index(fields=['is_retired']),
        ]
    
    def __str__(self):
        return f"Golden Standard for Task {self.task.id} ({self.source})"
    
    def retire_if_needed(self):
        """Retire golden standard if used too many times"""
        if self.times_shown >= self.max_uses and not self.is_retired:
            self.is_retired = True
            self.retired_at = timezone.now()
            self.is_active = False
            self.save(update_fields=['is_retired', 'retired_at', 'is_active'])
            return True
        return False
    
    def update_statistics(self, passed, score):
        """Update statistics after evaluation"""
        self.times_shown += 1
        if passed:
            self.times_passed += 1
        else:
            self.times_failed += 1
        
        # Update running average
        if self.times_shown == 1:
            self.average_score = Decimal(str(score))
        else:
            # Incremental average calculation
            old_avg = float(self.average_score)
            new_avg = old_avg + (score - old_avg) / self.times_shown
            self.average_score = Decimal(str(round(new_avg, 2)))
        
        self.save(update_fields=[
            'times_shown', 'times_passed', 'times_failed', 'average_score'
        ])
        
        # Check for retirement
        self.retire_if_needed()


class HoneypotAssignment(models.Model):
    """
    Tracks honeypot task assignments to annotators.
    
    THIS TABLE IS INTERNAL ONLY - Never exposed to annotator APIs.
    Annotators cannot query this table or know which tasks are honeypots.
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),         # Assigned, not yet submitted
        ('submitted', 'Submitted'),     # Submitted, awaiting evaluation
        ('evaluated', 'Evaluated'),     # Evaluation complete
        ('skipped', 'Skipped'),         # Annotator skipped or timed out
    ]
    
    annotator = models.ForeignKey(
        AnnotatorProfile,
        on_delete=models.CASCADE,
        related_name='honeypot_assignments'
    )
    golden_standard = models.ForeignKey(
        GoldenStandardTask,
        on_delete=models.CASCADE,
        related_name='assignments'
    )
    task_assignment = models.OneToOneField(
        'TaskAssignment',
        on_delete=models.CASCADE,
        related_name='honeypot_info'
    )
    
    # Position in the assignment queue (for analysis)
    position_in_queue = models.IntegerField(default=0)
    
    # Timing
    assigned_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    
    # Evaluation results (filled after submission)
    annotator_result = models.JSONField(null=True, blank=True)
    accuracy_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    passed = models.BooleanField(null=True)
    evaluation_details = models.JSONField(
        null=True,
        blank=True,
        help_text="Detailed comparison breakdown"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    class Meta:
        db_table = 'honeypot_assignment'
        verbose_name = 'Honeypot Assignment'
        verbose_name_plural = 'Honeypot Assignments'
        indexes = [
            models.Index(fields=['annotator', 'status']),
            models.Index(fields=['golden_standard', 'status']),
            models.Index(fields=['status', 'assigned_at']),
        ]
    
    def __str__(self):
        status = f"passed" if self.passed else ("failed" if self.passed is False else "pending")
        return f"Honeypot for {self.annotator.user.email} - {status}"


class AccuracyHistory(models.Model):
    """
    Daily accuracy snapshots for trend analysis.
    
    Stores both lifetime and rolling metrics for comparison.
    """
    
    annotator = models.ForeignKey(
        AnnotatorProfile,
        on_delete=models.CASCADE,
        related_name='honeypot_accuracy_history'
    )
    date = models.DateField()
    
    # Daily metrics
    honeypots_evaluated = models.IntegerField(default=0)
    honeypots_passed = models.IntegerField(default=0)
    daily_average_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Cumulative metrics (at end of day)
    total_honeypots_lifetime = models.IntegerField(default=0)
    lifetime_accuracy = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="All-time accuracy at end of this day"
    )
    rolling_accuracy = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Rolling window accuracy at end of this day"
    )
    
    class Meta:
        db_table = 'accuracy_history'
        verbose_name = 'Accuracy History'
        verbose_name_plural = 'Accuracy Histories'
        unique_together = ['annotator', 'date']
        indexes = [
            models.Index(fields=['annotator', 'date']),
            models.Index(fields=['date']),
        ]
    
    def __str__(self):
        return f"{self.annotator.user.email} - {self.date} - {self.lifetime_accuracy}%"
    
    @classmethod
    def record_daily_snapshot(cls, annotator):
        """Record end-of-day accuracy snapshot."""
        today = timezone.now().date()
        
        # Get today's honeypots
        todays_honeypots = HoneypotAssignment.objects.filter(
            annotator=annotator,
            status='evaluated',
            submitted_at__date=today
        )
        
        if not todays_honeypots.exists():
            return None
        
        daily_scores = [
            float(h.accuracy_score) 
            for h in todays_honeypots 
            if h.accuracy_score is not None
        ]
        
        # Get rolling accuracy from TrustLevel
        try:
            rolling_acc = float(annotator.trust_level.rolling_accuracy)
        except (TrustLevel.DoesNotExist, AttributeError):
            rolling_acc = 0
        
        snapshot, created = cls.objects.update_or_create(
            annotator=annotator,
            date=today,
            defaults={
                'honeypots_evaluated': todays_honeypots.count(),
                'honeypots_passed': todays_honeypots.filter(passed=True).count(),
                'daily_average_score': Decimal(str(
                    sum(daily_scores) / len(daily_scores)
                )) if daily_scores else None,
                'total_honeypots_lifetime': annotator.total_honeypots_evaluated or 0,
                'lifetime_accuracy': annotator.accuracy_score or Decimal('0'),
                'rolling_accuracy': Decimal(str(rolling_acc)),
            }
        )
        return snapshot


class AnnotatorWarning(models.Model):
    """
    Track warnings issued to annotators based on honeypot performance.
    """
    
    WARNING_TYPES = [
        ('soft_warning', 'Soft Warning'),
        ('formal_warning', 'Formal Warning'),
        ('final_warning', 'Final Warning'),
        ('suspension', 'Suspension'),
        ('recovery', 'Recovery'),
    ]
    
    annotator = models.ForeignKey(
        AnnotatorProfile,
        on_delete=models.CASCADE,
        related_name='honeypot_warnings'
    )
    warning_type = models.CharField(max_length=20, choices=WARNING_TYPES)
    accuracy_at_warning = models.DecimalField(max_digits=5, decimal_places=2)
    message = models.TextField()
    
    # Email tracking
    email_sent = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    
    # Acknowledgment (optional - for compliance tracking)
    acknowledged = models.BooleanField(default=False)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'annotator_warning'
        verbose_name = 'Annotator Warning'
        verbose_name_plural = 'Annotator Warnings'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['annotator', 'warning_type']),
            models.Index(fields=['warning_type', 'created_at']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.warning_type} for {self.annotator.user.email} at {self.accuracy_at_warning}%"
    
    def mark_email_sent(self):
        """Mark that warning email was sent"""
        self.email_sent = True
        self.email_sent_at = timezone.now()
        self.save(update_fields=['email_sent', 'email_sent_at'])
    
    def acknowledge(self):
        """Mark warning as acknowledged by annotator"""
        self.acknowledged = True
        self.acknowledged_at = timezone.now()
        self.save(update_fields=['acknowledged', 'acknowledged_at'])


# ============================================================================
# EXPERTISE SYSTEM MODELS
# ============================================================================


class ExpertiseCategory(models.Model):
    """
    Main annotation categories (e.g., Computer Vision, NLP, Audio/Speech).
    Maps to top-level annotation_templates folders.
    """
    
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(
        max_length=50, 
        blank=True, 
        help_text="Icon name or class (e.g., 'image', 'mic', 'text')"
    )
    
    # Template folder mapping
    template_folder = models.CharField(
        max_length=100,
        blank=True,
        help_text="Folder name in annotation_templates (e.g., 'computer-vision')"
    )
    
    # Ordering
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'expertise_category'
        verbose_name = 'Expertise Category'
        verbose_name_plural = 'Expertise Categories'
        ordering = ['display_order', 'name']
    
    def __str__(self):
        return self.name


class ExpertiseSpecialization(models.Model):
    """
    Sub-expertise within a category (e.g., X-Ray, MRI under Medical Imaging).
    These are more specific skills an annotator can claim.
    """
    
    category = models.ForeignKey(
        ExpertiseCategory,
        on_delete=models.CASCADE,
        related_name='specializations'
    )
    
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    
    # Template mapping (subfolder within category)
    template_folder = models.CharField(
        max_length=100,
        blank=True,
        help_text="Subfolder name (e.g., 'object-detection-with-bounding-boxes')"
    )
    
    # Requirements
    requires_certification = models.BooleanField(
        default=False,
        help_text="Whether this specialization requires external certification proof"
    )
    certification_instructions = models.TextField(
        blank=True,
        help_text="Instructions for certification upload/verification"
    )
    
    # Test configuration
    min_test_questions = models.IntegerField(
        default=10,
        help_text="Minimum questions for qualification test"
    )
    passing_score = models.IntegerField(
        default=70,
        help_text="Minimum score (%) to pass qualification"
    )
    
    # Ordering and status
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'expertise_specialization'
        verbose_name = 'Expertise Specialization'
        verbose_name_plural = 'Expertise Specializations'
        ordering = ['category', 'display_order', 'name']
        unique_together = [('category', 'slug')]
    
    def __str__(self):
        return f"{self.category.name} → {self.name}"


class AnnotatorExpertise(models.Model):
    """
    Tracks which expertise/specializations an annotator has claimed and verified.
    Many-to-many relationship with additional metadata.
    """
    
    STATUS_CHOICES = [
        ('claimed', 'Claimed'),           # Annotator said they have this skill
        ('testing', 'Taking Test'),       # Currently taking qualification test
        ('verified', 'Verified'),         # Passed test, can receive tasks
        ('failed', 'Failed Test'),        # Failed qualification, can retry
        ('expired', 'Expired'),           # Needs re-certification
        ('revoked', 'Revoked'),           # Admin revoked (fraud/quality)
    ]
    
    annotator = models.ForeignKey(
        AnnotatorProfile,
        on_delete=models.CASCADE,
        related_name='expertise_profiles'
    )
    category = models.ForeignKey(
        ExpertiseCategory,
        on_delete=models.CASCADE,
        related_name='annotator_expertise'
    )
    specialization = models.ForeignKey(
        ExpertiseSpecialization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='annotator_expertise',
        help_text="Optional: specific sub-expertise"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='claimed'
    )
    
    # Qualification test tracking
    test_attempts = models.IntegerField(default=0)
    last_test_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    last_test_at = models.DateTimeField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When certification expires (if applicable)"
    )
    
    # Certification documents (for specializations requiring proof)
    certification_url = models.URLField(
        blank=True,
        help_text="Link to uploaded certification document"
    )
    certification_verified = models.BooleanField(default=False)
    certification_verified_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='verified_certifications'
    )
    
    # Performance within this expertise
    tasks_completed = models.IntegerField(default=0)
    accuracy_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.0
    )
    average_time_per_task = models.IntegerField(
        default=0,
        help_text="Seconds"
    )
    
    # Additional metadata
    self_rating = models.IntegerField(
        default=5,
        help_text="Self-rated expertise (1-10)"
    )
    years_experience = models.IntegerField(
        default=0,
        help_text="Years of experience in this area"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional info from annotator"
    )
    
    # Badge display (shown when verified)
    badge_earned = models.BooleanField(
        default=False,
        help_text="Whether the badge has been earned for this expertise"
    )
    badge_earned_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the badge was earned"
    )
    
    # Test invitation token (for email-based test links)
    test_token = models.UUIDField(
        null=True,
        blank=True,
        unique=True,
        help_text="Token for accessing the expertise test via email link"
    )
    test_token_created_at = models.DateTimeField(
        null=True,
        blank=True
    )
    test_email_sent = models.BooleanField(
        default=False,
        help_text="Whether test invitation email has been sent"
    )
    test_email_sent_at = models.DateTimeField(
        null=True,
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'annotator_expertise'
        verbose_name = 'Annotator Expertise'
        verbose_name_plural = 'Annotator Expertise'
        # Prevent duplicate entries
        unique_together = [('annotator', 'category', 'specialization')]
        indexes = [
            models.Index(fields=['annotator', 'status']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['specialization', 'status']),
            models.Index(fields=['status', 'verified_at']),
        ]
    
    def __str__(self):
        spec = f" ({self.specialization.name})" if self.specialization else ""
        return f"{self.annotator.user.email}: {self.category.name}{spec} - {self.status}"
    
    @property
    def is_verified(self):
        """Check if expertise is currently valid"""
        if self.status != 'verified':
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        return True
    
    def record_test_attempt(self, score, passed):
        """Record a test attempt for this expertise"""
        self.test_attempts += 1
        self.last_test_score = score
        self.last_test_at = timezone.now()
        
        if passed:
            self.status = 'verified'
            self.verified_at = timezone.now()
            # Award badge
            self.badge_earned = True
            self.badge_earned_at = timezone.now()
        else:
            self.status = 'failed'
        
        self.save()
    
    def generate_test_token(self):
        """Generate a new test token for email-based access"""
        import uuid
        self.test_token = uuid.uuid4()
        self.test_token_created_at = timezone.now()
        self.save(update_fields=['test_token', 'test_token_created_at'])
        return self.test_token
    
    def is_test_token_valid(self, hours=72):
        """Check if test token is still valid (default 72 hours)"""
        if not self.test_token or not self.test_token_created_at:
            return False
        expiry = self.test_token_created_at + timezone.timedelta(hours=hours)
        return timezone.now() < expiry
    
    def mark_email_sent(self):
        """Mark that test invitation email was sent"""
        self.test_email_sent = True
        self.test_email_sent_at = timezone.now()
        self.save(update_fields=['test_email_sent', 'test_email_sent_at'])
    
    @property
    def badge_info(self):
        """Get badge display information"""
        if not self.badge_earned:
            return None
        
        return {
            'name': self.specialization.name if self.specialization else self.category.name,
            'category': self.category.name,
            'icon': self.specialization.icon if self.specialization else self.category.icon,
            'earned_at': self.badge_earned_at,
            'score': float(self.last_test_score) if self.last_test_score else None,
        }
    
    def can_retry_test(self, cooldown_days=7):
        """Check if annotator can retry the qualification test"""
        if self.status == 'verified':
            return False
        if not self.last_test_at:
            return True
        # Check cooldown period
        cooldown = timezone.timedelta(days=cooldown_days)
        return timezone.now() > self.last_test_at + cooldown


class ExpertiseTestQuestion(models.Model):
    """
    Test questions for expertise qualification.
    Questions are linked to categories and/or specializations.
    """
    
    QUESTION_TYPES = [
        ('mcq', 'Multiple Choice'),
        ('multi_select', 'Multiple Select'),
        ('true_false', 'True/False'),
        ('image_label', 'Image Labeling'),
        ('text_annotation', 'Text Annotation'),
    ]
    
    DIFFICULTY_LEVELS = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    
    category = models.ForeignKey(
        ExpertiseCategory,
        on_delete=models.CASCADE,
        related_name='test_questions'
    )
    specialization = models.ForeignKey(
        ExpertiseSpecialization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='test_questions',
        help_text="If set, question only applies to this specialization"
    )
    
    question_type = models.CharField(
        max_length=20,
        choices=QUESTION_TYPES,
        default='mcq'
    )
    difficulty = models.CharField(
        max_length=10,
        choices=DIFFICULTY_LEVELS,
        default='medium'
    )
    
    # Question content
    question_text = models.TextField()
    question_image_url = models.URLField(
        blank=True,
        help_text="URL to image for image-based questions"
    )
    question_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional question data (e.g., annotation config)"
    )
    
    # Answer options (for MCQ/multi-select)
    options = models.JSONField(
        default=list,
        help_text="List of answer options"
    )
    correct_answer = models.JSONField(
        help_text="Correct answer(s) - index for MCQ, list for multi-select, ground truth for annotations"
    )
    
    # Scoring
    points = models.IntegerField(default=1)
    partial_credit = models.BooleanField(
        default=False,
        help_text="Allow partial credit for partially correct answers"
    )
    
    # Explanation shown after test
    explanation = models.TextField(
        blank=True,
        help_text="Explanation shown after test submission"
    )
    
    # Metadata
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='created_test_questions'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'expertise_test_question'
        verbose_name = 'Expertise Test Question'
        verbose_name_plural = 'Expertise Test Questions'
        ordering = ['category', 'specialization', 'difficulty', 'id']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['specialization', 'is_active']),
            models.Index(fields=['question_type', 'difficulty']),
        ]
    
    def __str__(self):
        spec = f"/{self.specialization.name}" if self.specialization else ""
        return f"[{self.category.name}{spec}] {self.question_text[:50]}..."


class ExpertiseTest(models.Model):
    """
    Record of an expertise qualification test attempt.
    Links to AnnotationTest for unified test tracking.
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('submitted', 'Submitted'),
        ('passed', 'Passed'),
        ('failed', 'Failed'),
    ]
    
    annotator = models.ForeignKey(
        AnnotatorProfile,
        on_delete=models.CASCADE,
        related_name='expertise_tests'
    )
    expertise = models.ForeignKey(
        AnnotatorExpertise,
        on_delete=models.CASCADE,
        related_name='tests'
    )
    
    # Questions selected for this test
    questions = models.ManyToManyField(
        ExpertiseTestQuestion,
        related_name='test_instances'
    )
    
    # Answers submitted
    answers = models.JSONField(
        default=dict,
        help_text="Map of question_id to answer"
    )
    
    # Results
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    max_score = models.IntegerField(default=0)
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    passed = models.BooleanField(default=False)
    
    # Detailed results
    results_breakdown = models.JSONField(
        default=dict,
        help_text="Per-question results"
    )
    
    # Timing
    started_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    time_limit_minutes = models.IntegerField(
        default=30,
        help_text="Time limit for the test"
    )
    
    # Feedback
    feedback = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'expertise_test'
        verbose_name = 'Expertise Test'
        verbose_name_plural = 'Expertise Tests'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['annotator', 'status']),
            models.Index(fields=['expertise', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"Test for {self.annotator.user.email}: {self.expertise} - {self.status}"
    
    def start(self):
        """Start the test"""
        self.status = 'in_progress'
        self.started_at = timezone.now()
        self.save()
    
    def submit(self, answers):
        """Submit and grade the test"""
        self.answers = answers
        self.submitted_at = timezone.now()
        self.grade_test()
    
    def grade_test(self):
        """Grade the test and update results"""
        from decimal import Decimal
        
        total_points = 0
        earned_points = 0
        breakdown = {}
        
        for question in self.questions.all():
            total_points += question.points
            answer = self.answers.get(str(question.id))
            
            # Grade based on question type
            is_correct = False
            if question.question_type == 'mcq':
                is_correct = answer == question.correct_answer
            elif question.question_type == 'multi_select':
                # For multi-select, check if all correct answers are selected
                correct = set(question.correct_answer) if isinstance(question.correct_answer, list) else {question.correct_answer}
                submitted = set(answer) if isinstance(answer, list) else {answer}
                is_correct = correct == submitted
            elif question.question_type == 'true_false':
                is_correct = answer == question.correct_answer
            # For annotation questions, we'd need more complex grading
            
            if is_correct:
                earned_points += question.points
            
            breakdown[str(question.id)] = {
                'points': question.points,
                'earned': question.points if is_correct else 0,
                'correct': is_correct,
                'answer': answer,
                'correct_answer': question.correct_answer,
            }
        
        self.score = Decimal(str(earned_points))
        self.max_score = total_points
        self.percentage = Decimal(str((earned_points / total_points * 100) if total_points > 0 else 0))
        self.results_breakdown = breakdown
        
        # Check if passed
        passing_score = self.expertise.specialization.passing_score if self.expertise.specialization else 70
        self.passed = float(self.percentage) >= passing_score
        self.status = 'passed' if self.passed else 'failed'
        
        # Update the expertise record
        self.expertise.record_test_attempt(self.percentage, self.passed)
        
        self.save()


# ============================================================================
# EXPERT EXPERTISE MODEL
# ============================================================================


class ExpertExpertise(models.Model):
    """
    Tracks which expertise/specializations an expert has been assigned.
    Unlike AnnotatorExpertise, experts don't need to take tests - they are
    directly assigned by admins.
    """
    
    STATUS_CHOICES = [
        ('assigned', 'Assigned'),         # Admin assigned this expertise
        ('active', 'Active'),             # Currently active
        ('revoked', 'Revoked'),           # Admin revoked
    ]
    
    expert = models.ForeignKey(
        ExpertProfile,
        on_delete=models.CASCADE,
        related_name='expertise_profiles'
    )
    category = models.ForeignKey(
        ExpertiseCategory,
        on_delete=models.CASCADE,
        related_name='expert_expertise'
    )
    specialization = models.ForeignKey(
        ExpertiseSpecialization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='expert_expertise',
        help_text="Optional: specific sub-expertise"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='assigned'
    )
    
    # When was this expertise assigned
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='assigned_expert_expertise'
    )
    
    # Performance within this expertise
    tasks_reviewed = models.IntegerField(default=0)
    approvals_count = models.IntegerField(default=0)
    rejections_count = models.IntegerField(default=0)
    corrections_count = models.IntegerField(default=0)
    
    # Average review time in seconds
    average_review_time = models.IntegerField(default=0)
    
    # Quality metrics
    accuracy_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.0
    )
    
    # Additional notes from admin
    notes = models.TextField(
        blank=True,
        help_text="Notes from admin about this assignment"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Expert Expertise"
        verbose_name_plural = "Expert Expertise"
        unique_together = ['expert', 'category', 'specialization']
        ordering = ['-assigned_at']
    
    def __str__(self):
        spec = f" ({self.specialization.name})" if self.specialization else ""
        return f"{self.expert.user.email} - {self.category.name}{spec}"
    
    @property
    def badge_info(self):
        """Get badge display info for this expertise."""
        return {
            'name': self.specialization.name if self.specialization else self.category.name,
            'icon': self.specialization.icon if self.specialization else self.category.icon,
            'category': self.category.name,
            'status': self.status,
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
            'tasks_reviewed': self.tasks_reviewed,
        }
    
    def activate(self):
        """Activate this expertise."""
        self.status = 'active'
        self.save()
    
    def revoke(self):
        """Revoke this expertise."""
        self.status = 'revoked'
        self.save()
