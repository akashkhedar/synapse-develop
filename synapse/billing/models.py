from django.db import models
from django.contrib.auth import get_user_model
from organizations.models import Organization
from django.utils import timezone
from decimal import Decimal

User = get_user_model()


class SubscriptionPlan(models.Model):
    """Subscription plans available for purchase"""

    PLAN_TYPE_CHOICES = [
        ("payg", "Pay As You Go"),
        ("starter", "Starter"),
        ("growth", "Growth"),
        ("scale", "Scale"),
        ("enterprise", "Enterprise"),
    ]

    BILLING_CYCLE_CHOICES = [
        ("none", "No Billing Cycle (PAYG)"),
        ("monthly", "Monthly"),
        ("annual", "Annual"),
    ]

    name = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPE_CHOICES)
    billing_cycle = models.CharField(max_length=20, choices=BILLING_CYCLE_CHOICES)
    price_inr = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Price in INR"
    )
    credits_per_month = models.IntegerField(help_text="Credits allocated per month")
    effective_rate = models.DecimalField(
        max_digits=5, decimal_places=2, help_text="Effective rate per credit"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Features
    storage_gb = models.IntegerField(default=5, help_text="Free storage in GB")
    max_users = models.IntegerField(
        null=True, blank=True, help_text="Max users allowed (null = unlimited)"
    )
    priority_support = models.BooleanField(default=False)
    api_access = models.BooleanField(default=True)
    credit_rollover = models.BooleanField(
        default=True, help_text="Allow unused credits to rollover"
    )
    max_rollover_months = models.IntegerField(
        default=1, help_text="Max months to rollover credits"
    )
    
    # Project limits
    max_projects = models.IntegerField(
        default=3,
        help_text="Maximum number of active projects allowed (0 = unlimited)"
    )
    
    # Storage pricing
    extra_storage_rate_per_gb = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=15.00,
        help_text="Rate per GB per month for storage beyond free limit (in INR)"
    )
    storage_discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Discount percentage on extra storage charges"
    )
    
    # Subscription discounts
    annotation_discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Discount percentage on annotation costs"
    )
    renewal_discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Discount for existing subscribers renewing"
    )
    
    # Annual plan bonus
    annual_bonus_months = models.IntegerField(
        default=0,
        help_text="Number of free months for annual plan (e.g., 2 = pay for 10, get 12)"
    )
    annual_bonus_credits = models.IntegerField(
        default=0,
        help_text="Bonus credits for annual subscription"
    )
    
    # Description for display
    description = models.TextField(
        blank=True,
        help_text="Plan description for display to users"
    )
    features_json = models.JSONField(
        default=list,
        help_text="List of features for display"
    )

    class Meta:
        db_table = "billing_subscription_plan"
        ordering = ["price_inr"]

    def __str__(self):
        return f"{self.name} - {self.billing_cycle} (₹{self.price_inr})"


class CreditPackage(models.Model):
    """Pay-as-you-go credit packages"""

    name = models.CharField(max_length=100)
    credits = models.IntegerField()
    price_inr = models.DecimalField(max_digits=10, decimal_places=2)
    rate_per_credit = models.DecimalField(
        max_digits=5, decimal_places=2, help_text="Price per credit in INR"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "billing_credit_package"
        ordering = ["credits"]

    def __str__(self):
        return f"{self.credits} credits - ₹{self.price_inr}"


class OrganizationBilling(models.Model):
    """Billing information for organizations"""

    BILLING_TYPE_CHOICES = [
        ("payg", "Pay As You Go"),
        ("subscription", "Subscription"),
    ]

    organization = models.OneToOneField(
        Organization, on_delete=models.CASCADE, related_name="billing"
    )
    billing_type = models.CharField(
        max_length=20, choices=BILLING_TYPE_CHOICES, default="payg"
    )

    # Credit balance
    available_credits = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    rollover_credits = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Credits rolled over from previous month",
    )

    # Subscription details
    active_subscription = models.ForeignKey(
        "Subscription",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="billing_orgs",
    )

    # Storage tracking
    storage_used_gb = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    last_storage_check = models.DateTimeField(null=True, blank=True)

    # Razorpay details
    razorpay_customer_id = models.CharField(max_length=100, blank=True)

    # Billing address
    billing_email = models.EmailField(blank=True)
    billing_address = models.TextField(blank=True)
    gstin = models.CharField(
        max_length=15, blank=True, help_text="GST Identification Number"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "billing_organization_billing"

    def __str__(self):
        return f"{self.organization.title} - {self.billing_type} ({self.available_credits} credits)"

    def has_sufficient_credits(self, required_credits):
        """Check if organization has enough credits"""
        return self.available_credits >= Decimal(str(required_credits))

    def deduct_credits(self, amount, description=""):
        """Deduct credits from organization balance"""
        if not self.has_sufficient_credits(amount):
            raise ValueError("Insufficient credits")

        self.available_credits -= Decimal(str(amount))
        self.save()

        # Create transaction record
        CreditTransaction.objects.create(
            organization=self.organization,
            transaction_type="debit",
            amount=amount,
            balance_after=self.available_credits,
            description=description,
        )

    def add_credits(self, amount, description=""):
        """Add credits to organization balance"""
        self.available_credits += Decimal(str(amount))
        self.save()

        # Create transaction record
        CreditTransaction.objects.create(
            organization=self.organization,
            transaction_type="credit",
            amount=amount,
            balance_after=self.available_credits,
            description=description,
        )


class Subscription(models.Model):
    """Active subscriptions for organizations"""

    STATUS_CHOICES = [
        ("active", "Active"),
        ("cancelled", "Cancelled"),
        ("expired", "Expired"),
        ("paused", "Paused"),
    ]

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="subscriptions"
    )
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")

    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    next_billing_date = models.DateTimeField()

    # Razorpay subscription ID
    razorpay_subscription_id = models.CharField(max_length=100, blank=True)

    auto_renew = models.BooleanField(default=True)
    credits_allocated_this_month = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "billing_subscription"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.organization.title} - {self.plan.name} ({self.status})"

    def is_active(self):
        """Check if subscription is currently active"""
        return (
            self.status == "active"
            and self.start_date <= timezone.now() <= self.end_date
        )

    def allocate_monthly_credits(self):
        """Allocate credits for the current billing cycle"""
        if self.credits_allocated_this_month:
            return False

        billing = self.organization.billing

        # Handle credit rollover if enabled
        if self.plan.credit_rollover and billing.available_credits > 0:
            billing.rollover_credits = billing.available_credits
            billing.save()

        # Add new credits
        billing.add_credits(
            self.plan.credits_per_month, f"Monthly credit allocation - {self.plan.name}"
        )

        self.credits_allocated_this_month = True
        self.save()
        return True


class CreditTransaction(models.Model):
    """Transaction history for credits"""

    TRANSACTION_TYPE_CHOICES = [
        ("credit", "Credit"),
        ("debit", "Debit"),
    ]

    CATEGORY_CHOICES = [
        ("purchase", "Credit Purchase"),
        ("subscription", "Subscription Allocation"),
        ("annotation", "Annotation Cost"),
        ("storage", "Storage Cost"),
        ("refund", "Refund"),
        ("rollover", "Credit Rollover"),
        ("bonus", "Bonus Credits"),
    ]

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="credit_transactions"
    )
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES)
    category = models.CharField(
        max_length=20, choices=CATEGORY_CHOICES, default="annotation"
    )

    amount = models.DecimalField(max_digits=15, decimal_places=2)
    balance_after = models.DecimalField(max_digits=15, decimal_places=2)

    description = models.TextField()
    metadata = models.JSONField(
        default=dict, blank=True, help_text="Additional transaction details"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        db_table = "billing_credit_transaction"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organization", "-created_at"]),
            models.Index(fields=["transaction_type", "category"]),
        ]

    def __str__(self):
        return (
            f"{self.organization.title} - {self.transaction_type} {self.amount} credits"
        )


class Payment(models.Model):
    """Payment records from Razorpay"""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("authorized", "Authorized"),
        ("captured", "Captured"),
        ("refunded", "Refunded"),
        ("failed", "Failed"),
    ]

    PAYMENT_FOR_CHOICES = [
        ("credits", "Credit Package"),
        ("subscription", "Subscription"),
    ]

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="payments"
    )

    payment_for = models.CharField(max_length=20, choices=PAYMENT_FOR_CHOICES)
    credit_package = models.ForeignKey(
        CreditPackage, on_delete=models.SET_NULL, null=True, blank=True
    )
    subscription = models.ForeignKey(
        Subscription, on_delete=models.SET_NULL, null=True, blank=True
    )

    amount_inr = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    # Razorpay details
    razorpay_order_id = models.CharField(max_length=100, unique=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True)
    razorpay_signature = models.CharField(max_length=255, blank=True)

    payment_method = models.CharField(max_length=50, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        db_table = "billing_payment"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.organization.title} - ₹{self.amount_inr} ({self.status})"


class AnnotationPricing(models.Model):
    """Pricing rules for different annotation types based on the master pricing table"""

    DATA_TYPE_CHOICES = [
        ("2d_image", "2D Image"),
        ("3d_volume", "3D Volume"),
        ("time_series", "Time Series"),
        ("video", "Video"),
        ("3d_annotation", "3D Annotation"),
        ("signal_data", "Signal Data"),
        ("document", "Document"),
    ]

    data_type = models.CharField(max_length=20, choices=DATA_TYPE_CHOICES)
    modality = models.CharField(
        max_length=100, help_text="e.g., X-ray (Chest), CT Scan, ECG"
    )

    # Base credit per unit
    base_credit = models.DecimalField(max_digits=10, decimal_places=2)
    unit_description = models.CharField(
        max_length=100, help_text="e.g., per image, per slice, per minute"
    )

    # Annotation type costs
    classification_credit = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    bounding_box_credit = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    segmentation_credit = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    keypoint_credit = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    polygon_credit = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    time_sequence_credit = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "billing_annotation_pricing"
        unique_together = ["data_type", "modality"]

    def __str__(self):
        return f"{self.get_data_type_display()} - {self.modality}"

    def calculate_credit(self, annotation_type, volume=1):
        """Calculate credits based on annotation type and volume"""
        type_credits = {
            "classification": self.classification_credit,
            "bounding_box": self.bounding_box_credit,
            "segmentation": self.segmentation_credit,
            "keypoint": self.keypoint_credit,
            "polygon": self.polygon_credit,
            "time_sequence": self.time_sequence_credit,
        }

        annotation_credit = type_credits.get(annotation_type, 0) or 0
        total_credit = (float(self.base_credit) + float(annotation_credit)) * volume

        return Decimal(str(total_credit))


class AnnotatorEarnings(models.Model):
    """Track earnings for annotators (revenue share)"""

    annotator = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="earnings"
    )
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="annotator_earnings"
    )

    # Credits earned (40-50% of task credits)
    credits_earned = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    inr_equivalent = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Revenue share percentage for this annotator
    revenue_share_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=45.00,
        help_text="Percentage of credits annotator receives",
    )

    total_annotations = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "billing_annotator_earnings"
        unique_together = ["annotator", "organization"]

    def __str__(self):
        return f"{self.annotator.email} - {self.organization.title} (₹{self.inr_equivalent})"


class StorageBilling(models.Model):
    """Track storage usage and billing for organizations"""

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="storage_billing"
    )

    billing_month = models.DateField(help_text="First day of billing month")

    storage_used_gb = models.DecimalField(max_digits=10, decimal_places=2)
    free_storage_gb = models.DecimalField(max_digits=10, decimal_places=2, default=5)
    billable_storage_gb = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    
    # Rate and discount tracking
    rate_per_gb = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=15.00,
        help_text="Rate per GB per month applied"
    )
    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Discount percentage applied from subscription"
    )
    gross_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Amount before discount"
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Discount amount"
    )
    net_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Final amount after discount"
    )

    credits_charged = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Credits deducted from balance",
    )

    is_charged = models.BooleanField(default=False)
    charged_at = models.DateTimeField(null=True, blank=True)
    
    # Subscription info at time of billing
    subscription_plan_name = models.CharField(max_length=100, blank=True)
    billing_type = models.CharField(max_length=20, default="payg")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "billing_storage_billing"
        unique_together = ["organization", "billing_month"]
        ordering = ["-billing_month"]

    def __str__(self):
        return f"{self.organization.title} - {self.billing_month} ({self.storage_used_gb} GB)"

    def calculate_charges(self, subscription_plan=None):
        """
        Calculate storage charges with subscription discounts
        
        Args:
            subscription_plan: Optional SubscriptionPlan for discount calculation
        """
        self.billable_storage_gb = max(Decimal("0"), self.storage_used_gb - self.free_storage_gb)
        
        # Get rate and discount from subscription or use defaults
        if subscription_plan:
            self.rate_per_gb = subscription_plan.extra_storage_rate_per_gb
            self.discount_percent = subscription_plan.storage_discount_percent
            self.subscription_plan_name = subscription_plan.name
            self.billing_type = "subscription"
        else:
            # PAYG defaults
            self.rate_per_gb = Decimal("20.00")  # Higher rate for PAYG
            self.discount_percent = Decimal("0.00")
            self.subscription_plan_name = ""
            self.billing_type = "payg"
        
        # Calculate amounts
        self.gross_amount = self.billable_storage_gb * self.rate_per_gb
        self.discount_amount = self.gross_amount * (self.discount_percent / Decimal("100"))
        self.net_amount = self.gross_amount - self.discount_amount
        self.credits_charged = self.net_amount  # 1 INR = 1 credit
        
        self.save()
        return self.credits_charged


class ProjectBilling(models.Model):
    """
    Billing and lifecycle management for individual projects.
    Tracks security deposits, storage usage, and project states.
    """

    # Project Lifecycle States
    class ProjectState(models.TextChoices):
        ACTIVE = "active", "Active"
        DORMANT = "dormant", "Dormant (No activity 30 days)"
        WARNING = "warning", "Warning (Low credits)"
        GRACE = "grace", "Grace Period (Credits exhausted)"
        DELETED = "deleted", "Deleted"
        COMPLETED = "completed", "Completed"

    project = models.OneToOneField(
        "projects.Project", on_delete=models.CASCADE, related_name="billing"
    )

    # Security Deposit
    security_deposit_required = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Security deposit required for this project",
    )
    security_deposit_paid = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Security deposit actually paid",
    )
    security_deposit_refunded = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Security deposit refunded",
    )
    deposit_paid_at = models.DateTimeField(null=True, blank=True)
    deposit_refunded_at = models.DateTimeField(null=True, blank=True)

    # Storage Tracking
    storage_used_bytes = models.BigIntegerField(default=0)
    storage_used_gb = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    last_storage_calculated = models.DateTimeField(null=True, blank=True)

    # Annotation Cost Tracking
    estimated_annotation_cost = models.DecimalField(
        max_digits=15, decimal_places=2, default=0
    )
    actual_annotation_cost = models.DecimalField(
        max_digits=15, decimal_places=2, default=0
    )
    credits_consumed = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Project Lifecycle State
    state = models.CharField(
        max_length=20, choices=ProjectState.choices, default=ProjectState.ACTIVE
    )
    state_changed_at = models.DateTimeField(auto_now_add=True)

    # Activity Tracking
    last_activity_at = models.DateTimeField(auto_now_add=True)
    last_export_at = models.DateTimeField(null=True, blank=True)
    export_count = models.IntegerField(default=0)

    # Deletion Policy
    dormant_since = models.DateTimeField(null=True, blank=True)
    warning_sent_at = models.DateTimeField(null=True, blank=True)
    grace_period_start = models.DateTimeField(null=True, blank=True)
    scheduled_deletion_at = models.DateTimeField(null=True, blank=True)

    # Flags
    is_deposit_held = models.BooleanField(default=False)
    is_exportable = models.BooleanField(default=True)
    export_blocked_reason = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "billing_project_billing"

    def __str__(self):
        return f"{self.project.title} - {self.state} (Deposit: ₹{self.security_deposit_paid})"

    @property
    def storage_used_gb_display(self):
        """Human-readable storage display"""
        return round(float(self.storage_used_gb), 2)

    @property
    def is_deposit_sufficient(self):
        """Check if security deposit covers requirements"""
        return self.security_deposit_paid >= self.security_deposit_required

    @property
    def deposit_shortfall(self):
        """Amount needed to meet deposit requirement"""
        return max(
            Decimal("0"), self.security_deposit_required - self.security_deposit_paid
        )

    @property
    def refundable_deposit(self):
        """Calculate refundable deposit amount"""
        # Refund = Paid - Consumed - Already Refunded
        consumed = self.credits_consumed + self.actual_annotation_cost
        refundable = (
            self.security_deposit_paid - consumed - self.security_deposit_refunded
        )
        return max(Decimal("0"), refundable)

    def update_storage(self, bytes_used):
        """Update storage tracking"""
        self.storage_used_bytes = bytes_used
        self.storage_used_gb = Decimal(str(bytes_used / (1024**3)))
        self.last_storage_calculated = timezone.now()
        self.save(
            update_fields=[
                "storage_used_bytes",
                "storage_used_gb",
                "last_storage_calculated",
            ]
        )

    def record_activity(self):
        """Record project activity to prevent dormant state"""
        self.last_activity_at = timezone.now()
        if self.state == self.ProjectState.DORMANT:
            self.state = self.ProjectState.ACTIVE
            self.dormant_since = None
            self.state_changed_at = timezone.now()
        self.save(
            update_fields=[
                "last_activity_at",
                "state",
                "dormant_since",
                "state_changed_at",
            ]
        )

    def transition_to_state(self, new_state, reason=""):
        """Transition project to a new state"""
        old_state = self.state
        self.state = new_state
        self.state_changed_at = timezone.now()

        if new_state == self.ProjectState.DORMANT:
            self.dormant_since = timezone.now()
        elif new_state == self.ProjectState.WARNING:
            self.warning_sent_at = timezone.now()
        elif new_state == self.ProjectState.GRACE:
            self.grace_period_start = timezone.now()
            from datetime import timedelta

            self.scheduled_deletion_at = timezone.now() + timedelta(days=30)
        elif new_state == self.ProjectState.DELETED:
            self.is_exportable = False
            self.export_blocked_reason = "Project deleted due to credit exhaustion"

        self.save()

        # Create state change log
        ProjectBillingStateLog.objects.create(
            project_billing=self,
            from_state=old_state,
            to_state=new_state,
            reason=reason,
        )


class ProjectBillingStateLog(models.Model):
    """Log of project billing state changes"""

    project_billing = models.ForeignKey(
        ProjectBilling, on_delete=models.CASCADE, related_name="state_logs"
    )
    from_state = models.CharField(max_length=20)
    to_state = models.CharField(max_length=20)
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "billing_project_state_log"
        ordering = ["-created_at"]


class SecurityDeposit(models.Model):
    """
    Track security deposits for projects.
    Separate from ProjectBilling for detailed transaction history.
    """

    class DepositStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        HELD = "held", "Held"
        PARTIALLY_USED = "partially_used", "Partially Used"
        REFUNDED = "refunded", "Refunded"
        FORFEITED = "forfeited", "Forfeited"

    project = models.ForeignKey(
        "projects.Project", on_delete=models.CASCADE, related_name="security_deposits"
    )
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="security_deposits"
    )

    # Deposit calculation breakdown
    base_fee = models.DecimalField(max_digits=10, decimal_places=2, default=500)
    storage_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    annotation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_deposit = models.DecimalField(max_digits=15, decimal_places=2)

    # Status tracking
    status = models.CharField(
        max_length=20, choices=DepositStatus.choices, default=DepositStatus.PENDING
    )

    amount_used = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    amount_refunded = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    amount_forfeited = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)
    forfeited_at = models.DateTimeField(null=True, blank=True)

    # Linked transaction
    payment_transaction = models.ForeignKey(
        CreditTransaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="security_deposits",
    )
    refund_transaction = models.ForeignKey(
        CreditTransaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deposit_refunds",
    )

    class Meta:
        db_table = "billing_security_deposit"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.project.title} - ₹{self.total_deposit} ({self.status})"


class APIUsageTracking(models.Model):
    """Track API usage for rate limiting and billing"""

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="api_usage"
    )

    date = models.DateField()

    # Endpoint categories
    read_requests = models.IntegerField(
        default=0, help_text="GET requests (list, retrieve)"
    )
    write_requests = models.IntegerField(
        default=0, help_text="POST, PUT, PATCH requests"
    )
    export_requests = models.IntegerField(
        default=0, help_text="Export/download requests"
    )

    # Free tier limits
    free_read_limit = models.IntegerField(default=10000)
    free_write_limit = models.IntegerField(default=1000)
    free_export_limit = models.IntegerField(default=100)

    # Overage tracking
    read_overage = models.IntegerField(default=0)
    write_overage = models.IntegerField(default=0)
    export_overage = models.IntegerField(default=0)

    # Credits charged for overage
    credits_charged = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    charged_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "billing_api_usage"
        unique_together = ["organization", "date"]
        ordering = ["-date"]

    def __str__(self):
        return f"{self.organization.title} - {self.date} (R:{self.read_requests}/W:{self.write_requests}/E:{self.export_requests})"

    def increment_read(self, count=1):
        """Increment read request count"""
        self.read_requests += count
        if self.read_requests > self.free_read_limit:
            self.read_overage = self.read_requests - self.free_read_limit
        self.save(update_fields=["read_requests", "read_overage", "updated_at"])

    def increment_write(self, count=1):
        """Increment write request count"""
        self.write_requests += count
        if self.write_requests > self.free_write_limit:
            self.write_overage = self.write_requests - self.free_write_limit
        self.save(update_fields=["write_requests", "write_overage", "updated_at"])

    def increment_export(self, count=1):
        """Increment export request count"""
        self.export_requests += count
        if self.export_requests > self.free_export_limit:
            self.export_overage = self.export_requests - self.free_export_limit
        self.save(update_fields=["export_requests", "export_overage", "updated_at"])

    def calculate_overage_credits(self):
        """
        Calculate credits to charge for API overage.
        Rates:
        - Read: 1 credit per 1000 requests over limit
        - Write: 5 credits per 1000 requests over limit
        - Export: 10 credits per export over limit
        """
        read_credits = Decimal(str(self.read_overage / 1000))
        write_credits = Decimal(str(self.write_overage / 1000 * 5))
        export_credits = Decimal(str(self.export_overage * 10))

        total = read_credits + write_credits + export_credits
        return total.quantize(Decimal("0.01"))


class ExportRecord(models.Model):
    """Track exports for billing and throttling"""

    project = models.ForeignKey(
        "projects.Project", on_delete=models.CASCADE, related_name="export_records"
    )
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="export_records"
    )
    exported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    # Export details
    export_format = models.CharField(max_length=50)
    tasks_exported = models.IntegerField(default=0)
    annotations_exported = models.IntegerField(default=0)
    file_size_bytes = models.BigIntegerField(default=0)

    # Billing
    credits_charged = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_free_export = models.BooleanField(
        default=False, help_text="First export is free"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "billing_export_record"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["project", "-created_at"]),
            models.Index(fields=["organization", "-created_at"]),
        ]

    def __str__(self):
        return (
            f"{self.project.title} - {self.export_format} ({self.tasks_exported} tasks)"
        )


class CreditExpiry(models.Model):
    """Track credit expiry for bonus/promotional credits"""

    class CreditType(models.TextChoices):
        PURCHASED = "purchased", "Purchased (Never expires)"
        BONUS = "bonus", "Bonus (90 days)"
        ROLLOVER = "rollover", "Rollover (30 days)"
        PROMOTIONAL = "promotional", "Promotional (Custom)"

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="credit_expiries"
    )

    credit_type = models.CharField(max_length=20, choices=CreditType.choices)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    remaining = models.DecimalField(max_digits=15, decimal_places=2)

    expires_at = models.DateTimeField(
        null=True, blank=True, help_text="Null for never-expiring credits"
    )
    is_expired = models.BooleanField(default=False)
    expired_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "billing_credit_expiry"
        ordering = ["expires_at"]  # FIFO - oldest first

    def __str__(self):
        expiry = self.expires_at.strftime("%Y-%m-%d") if self.expires_at else "Never"
        return f"{self.organization.title} - {self.remaining}/{self.amount} credits (Expires: {expiry})"





