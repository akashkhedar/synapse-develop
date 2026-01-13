# Synapse Backend Architecture

> Last Updated: January 13, 2026

## Overview

The Synapse backend is built on **Django 5.1.8** with **Django REST Framework 3.15.2**, using **PostgreSQL** as the primary database and **Redis** for caching and task queues. The architecture follows a modular Django app structure with clear separation of concerns.

---

## Table of Contents

1. [Directory Structure](#directory-structure)
2. [Django Applications](#django-applications)
3. [Core Models](#core-models)
4. [API Architecture](#api-architecture)
5. [State Machine (FSM)](#state-machine-fsm)
6. [Task Queue System](#task-queue-system)
7. [Authentication & Authorization](#authentication--authorization)
8. [Database Schema](#database-schema)
9. [Configuration & Settings](#configuration--settings)

---

## Directory Structure

```
synapse/
├── __init__.py
├── manage.py                    # Django management script
├── server.py                    # Server entry point
├── constants.py                 # Global constants
├── pytest.ini                   # Test configuration
│
├── core/                        # Core application
│   ├── settings/                # Django settings (base, dev, prod)
│   ├── middleware.py            # Custom middleware
│   ├── permissions.py           # Permission classes
│   ├── rbac.py                  # Role-based access control
│   ├── redis.py                 # Redis utilities
│   ├── urls.py                  # Root URL configuration
│   ├── views.py                 # Core views
│   ├── models.py                # Core models (AsyncMigrationStatus, etc.)
│   ├── label_config.py          # Label configuration parsing
│   ├── feature_flags/           # Feature flag management
│   ├── utils/                   # Utility functions
│   ├── templates/               # HTML templates
│   └── static/                  # Static files
│
├── organizations/               # Multi-tenancy
│   ├── models.py                # Organization, OrganizationMember
│   ├── api.py                   # Organization APIs
│   ├── permissions.py           # Org-level permissions
│   └── ...
│
├── users/                       # User management
│   ├── models.py                # User model
│   ├── email_verification.py    # Email verification flow
│   ├── api.py                   # User APIs
│   └── ...
│
├── projects/                    # Project management
│   ├── models.py                # Project model (2000+ lines)
│   ├── api.py                   # Project APIs
│   ├── functions/               # Project-related functions
│   └── ...
│
├── tasks/                       # Tasks & Annotations
│   ├── models.py                # Task, Annotation, Prediction models
│   ├── api.py                   # Task APIs
│   ├── choices.py               # Task enums
│   └── ...
│
├── annotators/                  # Annotator workforce
│   ├── models.py                # AnnotatorProfile, TaskAssignment, TrustLevel
│   ├── payment_service.py       # Payment calculations
│   ├── expert_service.py        # Expert review management
│   ├── assignment_engine.py     # Task distribution
│   ├── consensus_service.py     # Consensus calculation
│   ├── accuracy_service.py      # Accuracy tracking
│   └── ...
│
├── billing/                     # Billing & payments
│   ├── models.py                # SubscriptionPlan, CreditPackage, etc.
│   ├── services.py              # CreditService, ProjectBillingService
│   ├── razorpay_utils.py        # Razorpay integration
│   └── ...
│
├── data_import/                 # Data import
│   ├── models.py                # FileUpload, ImportStorage
│   ├── uploader.py              # Upload handling
│   └── ...
│
├── data_export/                 # Data export
│   ├── models.py                # Export models
│   ├── serializers.py           # Export format serializers
│   └── ...
│
├── fsm/                         # Finite State Machine
│   ├── models.py                # BaseState model
│   ├── state_manager.py         # State management
│   ├── transitions.py           # Transition definitions
│   ├── registry.py              # State/transition registry
│   └── ...
│
├── ml/                          # ML Backend integration
│   ├── models.py                # MLBackend model
│   ├── api_connector.py         # ML API integration
│   └── ...
│
├── io_storages/                 # Cloud storage
│   └── models.py                # S3, GCS, Azure storage models
│
├── webhooks/                    # Event notifications
│   ├── models.py                # Webhook model
│   ├── utils.py                 # Webhook dispatching
│   └── ...
│
├── jwt_auth/                    # JWT authentication
│   └── ...
│
├── labels_manager/              # Label management
│   └── models.py                # Label model
│
└── session_policy/              # Session management
    └── ...
```

---

## Django Applications

### 1. Core (`core/`)

The foundational application containing settings, utilities, and shared functionality.

| Component | Description |
|-----------|-------------|
| `settings/` | Django settings for different environments |
| `middleware.py` | Request/response middleware |
| `permissions.py` | DRF permission classes |
| `rbac.py` | Role-based access control |
| `redis.py` | Redis connection utilities |
| `label_config.py` | XML label config parser |
| `feature_flags/` | LaunchDarkly integration |
| `utils/` | Common utility functions |

**Key Models:**

```python
class AsyncMigrationStatus(models.Model):
    """Track async migration progress"""
    name = models.TextField()
    status = models.CharField(choices=['SCHEDULED', 'STARTED', 'IN PROGRESS', 'FINISHED', 'ERROR'])
    project = models.ForeignKey('projects.Project')
    meta = JSONField()

class DeletedRow(models.Model):
    """Soft-delete backup storage"""
    model = models.CharField()       # e.g., 'tasks.task'
    row_id = models.IntegerField()
    data = JSONField()               # Serialized row data
    reason = models.TextField()
```

### 2. Organizations (`organizations/`)

Multi-tenancy support with organization-based data isolation.

**Key Models:**

```python
class Organization(models.Model):
    title = models.CharField(max_length=1000)
    token = models.CharField(unique=True)    # Invite token
    users = models.ManyToManyField(User, through='OrganizationMember')
    created_by = models.ForeignKey(User)

class OrganizationMember(models.Model):
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('member', 'Member'),
    ]
    
    user = models.ForeignKey(User)
    organization = models.ForeignKey(Organization)
    role = models.CharField(choices=ROLE_CHOICES)
    deleted_at = models.DateTimeField(null=True)  # Soft delete
```

**Key Features:**
- Role-based membership (Owner, Admin, Member)
- Soft delete for member removal
- Invite link generation
- Organization-scoped data access

### 3. Users (`users/`)

User authentication and profile management.

**Key Models:**

```python
class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    username = models.CharField()
    first_name = models.CharField()
    last_name = models.CharField()
    
    # Role flags
    is_client = models.BooleanField(default=False)
    is_annotator = models.BooleanField(default=False)
    is_expert = models.BooleanField(default=False)
    
    # Verification
    email_verified = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True)
    annotator_status = models.CharField()  # Workflow status
    
    # Activity tracking
    last_activity = models.DateTimeField()
    activity_at = models.DateTimeField(auto_now=True)
```

**Key Features:**
- Email-based authentication
- Multiple role types (client, annotator, expert)
- Email verification flow
- Activity tracking with Redis caching

### 4. Projects (`projects/`)

Project configuration and management.

**Key Models:**

```python
class Project(FsmHistoryStateModel):
    """Main project model - 2000+ lines"""
    
    # Basic info
    title = models.CharField(max_length=500)
    description = models.TextField()
    organization = models.ForeignKey(Organization)
    
    # Label configuration
    label_config = models.TextField()          # XML config
    parsed_label_config = JSONField()          # Parsed JSON
    expert_instruction = models.TextField()    # Instructions HTML
    
    # Settings
    show_skip_button = models.BooleanField(default=True)
    enable_empty_annotation = models.BooleanField(default=True)
    show_annotation_history = models.BooleanField(default=False)
    show_collab_predictions = models.BooleanField(default=True)
    
    # Skip behavior
    class SkipQueue(models.TextChoices):
        REQUEUE_FOR_ME = "REQUEUE_FOR_ME"
        REQUEUE_FOR_OTHERS = "REQUEUE_FOR_OTHERS"
        IGNORE_SKIPPED = "IGNORE_SKIPPED"
    
    # Statistics (denormalized)
    task_number = models.IntegerField(default=0)
    finished_task_number = models.IntegerField(default=0)
    total_annotations_number = models.IntegerField(default=0)
    
    # Soft delete
    deleted_at = models.DateTimeField(null=True)
```

**Custom Managers:**

```python
class ProjectVisibleManager(ProjectManager):
    """Filters out soft-deleted projects"""
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)

class ProjectManager(models.Manager):
    """Provides counter annotations for statistics"""
    COUNTER_FIELDS = [
        'task_number', 'finished_task_number',
        'total_predictions_number', 'total_annotations_number'
    ]
    
    def with_counts(self, fields=None):
        """Annotate queryset with computed counts"""
        ...
```

### 5. Tasks (`tasks/`)

Task and annotation management - the core of annotation data.

**Key Models:**

```python
class Task(FsmHistoryStateModel):
    """Individual annotation tasks"""
    
    data = JSONField()                    # Task data (image URL, text, etc.)
    meta = JSONField()                    # Metadata
    project = models.ForeignKey(Project)
    
    # Status
    is_labeled = models.BooleanField(default=False)
    overlap = models.IntegerField(default=3)   # Required annotators
    
    # Statistics
    total_annotations = models.IntegerField(default=0)
    cancelled_annotations = models.IntegerField(default=0)
    total_predictions = models.IntegerField(default=0)
    
    # Assignment system
    priority = models.CharField(choices=['critical', 'high', 'normal', 'low'])
    complexity = models.CharField(choices=['beginner', 'intermediate', 'advanced', 'expert'])
    required_trust_level = models.CharField()
    estimated_time = models.IntegerField(default=300)  # seconds

class Annotation(models.Model):
    """Annotation result from annotator"""
    
    task = models.ForeignKey(Task)
    completed_by = models.ForeignKey(User)
    
    result = JSONField()                  # Annotation data
    lead_time = models.FloatField()       # Time spent
    
    # Review workflow
    was_cancelled = models.BooleanField(default=False)
    ground_truth = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Prediction(models.Model):
    """ML model predictions for pre-labeling"""
    
    task = models.ForeignKey(Task)
    result = JSONField()
    model_version = models.CharField()
    score = models.FloatField()           # Confidence score
```

### 6. Annotators (`annotators/`)

Complete workforce management system.

**Key Models:**

```python
class AnnotatorProfile(models.Model):
    """Extended profile for annotators"""
    
    user = models.OneToOneField(User)
    
    # Verification workflow
    STATUS_CHOICES = [
        ('pending_verification', 'Pending Email Verification'),
        ('pending_test', 'Pending Test'),
        ('test_submitted', 'Test Submitted'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    ]
    status = models.CharField(choices=STATUS_CHOICES)
    email_verified = models.BooleanField(default=False)
    
    # Skills
    skills = JSONField(default=list)       # Annotation types
    languages = JSONField(default=list)
    experience_level = models.CharField()  # beginner/intermediate/expert
    
    # Performance metrics
    total_tasks_completed = models.IntegerField(default=0)
    accuracy_score = models.DecimalField(default=0)
    average_time_per_task = models.IntegerField(default=0)
    rejection_rate = models.DecimalField(default=0)
    
    # Earnings
    total_earned = models.DecimalField(default=0)
    pending_approval = models.DecimalField(default=0)
    available_balance = models.DecimalField(default=0)
    total_withdrawn = models.DecimalField(default=0)
    
    # Bank details
    bank_name = models.CharField()
    account_number = models.CharField()
    ifsc_code = models.CharField()
    upi_id = models.CharField()

class TaskAssignment(models.Model):
    """Assignment of task to annotator"""
    
    annotator = models.ForeignKey(AnnotatorProfile)
    task = models.ForeignKey(Task)
    annotation = models.OneToOneField(Annotation, null=True)
    
    STATUS_CHOICES = [
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
        ('skipped', 'Skipped'),
    ]
    status = models.CharField(choices=STATUS_CHOICES)
    
    # Payment (escrow system)
    base_payment = models.DecimalField()
    quality_multiplier = models.DecimalField(default=1.0)
    trust_multiplier = models.DecimalField(default=1.0)
    
    # Escrow stages (40% + 40% + 20%)
    immediate_payment = models.DecimalField()   # On submission
    consensus_payment = models.DecimalField()   # After consensus
    review_payment = models.DecimalField()      # After expert review
    
    immediate_released = models.BooleanField(default=False)
    consensus_released = models.BooleanField(default=False)
    review_released = models.BooleanField(default=False)
    
    # Quality metrics
    quality_score = models.DecimalField()
    consensus_agreement = models.DecimalField()
    time_spent_seconds = models.IntegerField()
    ground_truth_accuracy = models.DecimalField()
    
    # Honeypot
    is_honeypot = models.BooleanField(default=False)
    honeypot_passed = models.BooleanField(null=True)

class TrustLevel(models.Model):
    """Annotator trust level tracking"""
    
    LEVEL_CHOICES = [
        ('new', 'New'),           # 0.8x multiplier
        ('junior', 'Junior'),     # 1.0x
        ('regular', 'Regular'),   # 1.1x
        ('senior', 'Senior'),     # 1.3x
        ('expert', 'Expert'),     # 1.5x
    ]
    
    LEVEL_THRESHOLDS = {
        'new': {'tasks': 0, 'accuracy': 0, 'honeypot_rate': 0},
        'junior': {'tasks': 50, 'accuracy': 70, 'honeypot_rate': 80},
        'regular': {'tasks': 200, 'accuracy': 80, 'honeypot_rate': 90},
        'senior': {'tasks': 500, 'accuracy': 90, 'honeypot_rate': 95},
        'expert': {'tasks': 1000, 'accuracy': 95, 'honeypot_rate': 98},
    }
    
    annotator = models.OneToOneField(AnnotatorProfile)
    level = models.CharField(choices=LEVEL_CHOICES)
    multiplier = models.DecimalField()
    
    tasks_completed = models.IntegerField()
    accuracy_score = models.DecimalField()
    honeypot_pass_rate = models.DecimalField()
    
    fraud_flags = models.IntegerField(default=0)
    is_suspended = models.BooleanField(default=False)
```

**Gamification Models:**

```python
class AnnotatorStreak(models.Model):
    """Daily activity streaks for bonus rewards"""
    annotator = models.OneToOneField(AnnotatorProfile)
    current_streak = models.IntegerField()
    longest_streak = models.IntegerField()
    
    def get_streak_multiplier(self):
        if self.current_streak >= 30: return Decimal('1.25')
        elif self.current_streak >= 14: return Decimal('1.15')
        elif self.current_streak >= 7: return Decimal('1.10')
        elif self.current_streak >= 3: return Decimal('1.05')
        return Decimal('1.0')

class Achievement(models.Model):
    """Predefined achievements"""
    code = models.CharField(unique=True)
    name = models.CharField()
    category = models.CharField()  # volume, quality, streak, speed, special
    tier = models.CharField()      # bronze, silver, gold, platinum, diamond
    bonus_amount = models.DecimalField()
    requirement_type = models.CharField()
    requirement_value = models.DecimalField()

class DailyLeaderboard(models.Model):
    """Daily leaderboard for competitive gamification"""
    date = models.DateField()
    annotator = models.ForeignKey(AnnotatorProfile)
    tasks_completed = models.IntegerField()
    earnings = models.DecimalField()
    rank = models.IntegerField(null=True)
    leaderboard_bonus = models.DecimalField()
```

### 7. Billing (`billing/`)

Complete billing and payment system.

**Key Models:**

```python
class SubscriptionPlan(models.Model):
    """Subscription plans (Starter, Growth, Scale, Enterprise)"""
    
    name = models.CharField()
    plan_type = models.CharField()  # starter, growth, scale, enterprise
    billing_cycle = models.CharField()  # monthly, annual
    price_inr = models.DecimalField()
    credits_per_month = models.IntegerField()
    effective_rate = models.DecimalField()
    
    # Features
    storage_gb = models.IntegerField(default=5)
    max_users = models.IntegerField(null=True)
    priority_support = models.BooleanField()
    api_access = models.BooleanField()
    credit_rollover = models.BooleanField()

class OrganizationBilling(models.Model):
    """Billing for organizations"""
    
    organization = models.OneToOneField(Organization)
    billing_type = models.CharField()  # payg, subscription
    
    available_credits = models.DecimalField()
    rollover_credits = models.DecimalField()
    active_subscription = models.ForeignKey(Subscription, null=True)
    
    storage_used_gb = models.DecimalField()
    razorpay_customer_id = models.CharField()
    gstin = models.CharField()

class AnnotationPricing(models.Model):
    """Pricing rules per annotation type"""
    
    data_type = models.CharField()  # 2d_image, 3d_volume, video, etc.
    modality = models.CharField()   # X-ray, CT Scan, etc.
    base_credit = models.DecimalField()
    
    # Per-type credits
    classification_credit = models.DecimalField()
    bounding_box_credit = models.DecimalField()
    segmentation_credit = models.DecimalField()
    keypoint_credit = models.DecimalField()
    polygon_credit = models.DecimalField()

class ProjectBilling(models.Model):
    """Per-project billing and lifecycle"""
    
    class ProjectState(models.TextChoices):
        ACTIVE = 'active'
        DORMANT = 'dormant'      # No activity 30 days
        WARNING = 'warning'      # Low credits
        GRACE = 'grace'          # Credits exhausted
        DELETED = 'deleted'
        COMPLETED = 'completed'
    
    project = models.OneToOneField(Project)
    
    # Security deposit
    security_deposit_required = models.DecimalField()
    security_deposit_paid = models.DecimalField()
    
    # Usage tracking
    storage_used_bytes = models.BigIntegerField()
    credits_consumed = models.DecimalField()
    
    # Lifecycle
    state = models.CharField(choices=ProjectState.choices)
    last_activity_at = models.DateTimeField()
```

---

## API Architecture

### REST API Structure

```
/api/
├── /organizations/
│   ├── GET      - List user's organizations
│   ├── POST     - Create organization
│   └── /{id}/
│       ├── GET      - Organization details
│       ├── PATCH    - Update organization
│       └── /members/
│           ├── GET      - List members
│           ├── POST     - Add member
│           └── DELETE   - Remove member
│
├── /projects/
│   ├── GET      - List projects
│   ├── POST     - Create project
│   └── /{id}/
│       ├── GET          - Project details
│       ├── PATCH        - Update project
│       ├── DELETE       - Delete project
│       ├── /tasks/      - Task management
│       ├── /export/     - Export annotations
│       └── /import/     - Import data
│
├── /tasks/
│   ├── GET      - List tasks
│   └── /{id}/
│       ├── GET          - Task details
│       ├── PATCH        - Update task
│       └── /annotations/ - Annotation management
│
├── /annotations/
│   ├── GET      - List annotations
│   ├── POST     - Create annotation
│   └── /{id}/
│       ├── GET      - Annotation details
│       ├── PATCH    - Update annotation
│       └── DELETE   - Delete annotation
│
├── /annotators/
│   ├── /signup/         - Annotator registration
│   ├── /verify-email/   - Email verification
│   ├── /dashboard/      - Annotator dashboard
│   ├── /tasks/          - Available tasks
│   ├── /earnings/       - Earnings history
│   └── /payouts/        - Payout requests
│
├── /billing/
│   ├── /credits/        - Credit balance
│   ├── /plans/          - Available plans
│   ├── /subscribe/      - Subscribe to plan
│   ├── /purchase/       - Buy credits
│   └── /transactions/   - Transaction history
│
└── /webhooks/
    ├── GET      - List webhooks
    ├── POST     - Create webhook
    └── /{id}/   - Manage webhook
```

### Authentication Methods

```python
# API Key Authentication
class APIKeyAuthentication(BaseAuthentication):
    def authenticate(self, request):
        api_key = request.headers.get('Authorization')
        # Format: 'Token sk_live_xxxx'
        ...

# JWT Authentication
class JWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        token = request.headers.get('Authorization')
        # Format: 'Bearer eyJ...'
        ...

# Session Authentication (web)
class SessionAuthentication(BaseAuthentication):
    ...
```

### Permission Classes

```python
class IsOrganizationMember(BasePermission):
    """User must be member of the organization"""
    def has_object_permission(self, request, view, obj):
        return obj.organization.has_permission(request.user)

class IsProjectOwner(BasePermission):
    """User must own the project"""
    ...

class IsAnnotator(BasePermission):
    """User must be an approved annotator"""
    def has_permission(self, request, view):
        return request.user.is_annotator and \
               request.user.annotator_profile.status == 'approved'

class IsExpert(BasePermission):
    """User must be an expert reviewer"""
    ...
```

---

## State Machine (FSM)

The FSM framework provides high-performance state tracking with UUID7 optimization.

### Architecture

```
models.py → registry.py → transitions.py → state_manager.py
     ↓           ↓              ↓                ↓
BaseState   State Registry  Transition      State Manager
 Model      & Choices       Definitions     (Main Entry)
```

### Key Components

```python
# 1. Base State Model
class BaseState(models.Model):
    """UUID7-optimized state tracking"""
    id = models.CharField(primary_key=True, max_length=36)  # UUID7
    state = models.CharField(db_index=True)
    previous_state = models.CharField(null=True)
    transition_name = models.CharField()
    transition_data = JSONField()
    user = models.ForeignKey(User, null=True)
    created_at = models.DateTimeField()
    
    class Meta:
        abstract = True

# 2. State Manager
class StateManager:
    """Core state management with caching"""
    
    CACHE_TTL = 300  # 5 minutes
    
    @classmethod
    def get_current_state_value(cls, entity) -> Optional[str]:
        """Get current state with caching"""
        cache_key = cls.get_cache_key(entity)
        cached = cache.get(cache_key)
        if cached:
            return cached
        # Query latest state record
        ...
    
    @classmethod
    def execute_transition(cls, entity, transition_name, **kwargs):
        """Execute state transition with validation"""
        ...
    
    @classmethod
    def get_state_history(cls, entity) -> QuerySet:
        """Get full state history"""
        ...

# 3. Transition Definition
@register_state_transition('project', 'activate')
class ActivateProjectTransition(BaseTransition):
    reason: str = Field(default="")
    
    def get_target_state(self, context) -> str:
        return 'ACTIVE'
    
    def validate_transition(self, context) -> bool:
        return context.current_state in ['DRAFT', 'PAUSED']
    
    def transition(self, context) -> dict:
        return {"activated_by": context.user.id}
```

### Usage

```python
from fsm.state_manager import StateManager

# Execute transition
result = StateManager.execute_transition(
    entity=project,
    transition_name='activate',
    transition_data={'reason': 'Ready for annotations'},
    user=request.user
)

# Query state
current_state = StateManager.get_current_state_value(project)
history = StateManager.get_state_history(project)
```

---

## Task Queue System

Redis Queue (RQ) is used for background task processing.

### Queue Configuration

```python
# settings.py
RQ_QUEUES = {
    'default': {
        'HOST': 'localhost',
        'PORT': 6379,
        'DB': 0,
        'DEFAULT_TIMEOUT': 360,
    },
    'high': {
        'HOST': 'localhost',
        'PORT': 6379,
        'DB': 0,
    },
    'low': {
        'HOST': 'localhost',
        'PORT': 6379,
        'DB': 0,
    },
}
```

### Common Background Tasks

```python
# Export processing
@job('default')
def process_export(project_id, export_format, user_id):
    """Generate export file in background"""
    ...

# Storage sync
@job('low')
def sync_cloud_storage(storage_id):
    """Sync data from cloud storage"""
    ...

# Consensus calculation
@job('high')
def calculate_consensus(task_id):
    """Calculate consensus for task"""
    ...

# Payment processing
@job('default')
def process_payout_batch():
    """Process pending payouts"""
    ...

# Webhooks
@job('high')
def dispatch_webhook(webhook_id, event_type, payload):
    """Send webhook notification"""
    ...
```

---

## Database Schema

### Entity Relationship Diagram (Simplified)

```
┌─────────────────┐       ┌─────────────────┐
│  Organization   │───┐   │      User       │
├─────────────────┤   │   ├─────────────────┤
│ id              │   │   │ id              │
│ title           │   │   │ email           │
│ token           │   │   │ is_client       │
│ created_by ─────┼───┼───│ is_annotator    │
└────────┬────────┘   │   │ is_expert       │
         │            │   └────────┬────────┘
         │            │            │
         │   ┌────────┴────────┐   │
         │   │OrganizationMember   │
         │   ├─────────────────┤   │
         │   │ user ───────────┼───┘
         │   │ organization    │
         │   │ role            │
         │   └─────────────────┘
         │
    ┌────┴────────────┐
    │     Project     │
    ├─────────────────┤
    │ id              │
    │ title           │       ┌─────────────────┐
    │ label_config    │       │AnnotatorProfile │
    │ organization ───┼───┐   ├─────────────────┤
    └────────┬────────┘   │   │ user            │
             │            │   │ status          │
        ┌────┴────────┐   │   │ trust_level     │
        │    Task     │   │   │ total_earned    │
        ├─────────────┤   │   └────────┬────────┘
        │ id          │   │            │
        │ data        │   │   ┌────────┴────────┐
        │ project ────┼───┘   │ TaskAssignment  │
        │ overlap     │       ├─────────────────┤
        └────┬────────┘       │ annotator ──────┤
             │                │ task            │
        ┌────┴────────┐       │ status          │
        │ Annotation  │       │ payment         │
        ├─────────────┤       └─────────────────┘
        │ task ───────┤
        │ result      │
        │ completed_by│
        └─────────────┘
```

### Key Indexes

```sql
-- Task indexes
CREATE INDEX task_project_labeled ON task(project_id, is_labeled);
CREATE INDEX task_project_inner_id ON task(project_id, inner_id);

-- Annotation indexes
CREATE INDEX annotation_task ON annotation(task_id);
CREATE INDEX annotation_user ON annotation(completed_by_id);

-- Assignment indexes
CREATE INDEX assignment_annotator_status ON task_assignment(annotator_id, status);
CREATE INDEX assignment_consensus ON task_assignment(status, consensus_released);

-- Billing indexes
CREATE INDEX credit_tx_org_date ON billing_credit_transaction(organization_id, created_at DESC);
```

---

## Configuration & Settings

### Environment Variables

```bash
# Database
DATABASE_URL=postgres://user:pass@localhost:5432/synapse
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key
DEBUG=false
ALLOWED_HOSTS=synapse.io,app.synapse.io

# Storage
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
AWS_STORAGE_BUCKET_NAME=synapse-data

# Payments
RAZORPAY_KEY_ID=xxx
RAZORPAY_KEY_SECRET=xxx

# Feature Flags
LAUNCHDARKLY_SDK_KEY=xxx

# Monitoring
SENTRY_DSN=xxx
```

### Django Settings Structure

```
synapse/core/settings/
├── __init__.py
├── base.py          # Base settings
├── development.py   # Development overrides
├── production.py    # Production overrides
└── testing.py       # Test settings
```

---

## Key Services

### PaymentService (`annotators/payment_service.py`)

```python
class PaymentService:
    """Handles all annotator payment calculations"""
    
    BASE_RATES = {
        'classification': Decimal('2.0'),
        'bounding_box': Decimal('5.0'),
        'polygon': Decimal('8.0'),
        'segmentation': Decimal('15.0'),
    }
    
    @staticmethod
    def calculate_task_payment(task_assignment, annotation_type):
        """Calculate payment with quality and trust multipliers"""
        ...
    
    @staticmethod
    def calculate_quality_score(task_assignment, annotation_result):
        """Score based on time, completeness, consensus"""
        ...
    
    @staticmethod
    def process_annotation_completion(task_assignment):
        """Release payments based on escrow stages"""
        ...
```

### CreditService (`billing/services.py`)

```python
class CreditService:
    """Manages organization credit operations"""
    
    @staticmethod
    def check_and_deduct_credits(organization, data_type, modality, ...):
        """Deduct credits and record transaction"""
        ...
    
    @staticmethod
    def credit_annotator(annotator, organization, total_credits):
        """Credit annotator with revenue share (40-50%)"""
        ...
```

### ProjectBillingService (`billing/services.py`)

```python
class ProjectBillingService:
    """Manages project-level billing"""
    
    BASE_DEPOSIT_FEE = Decimal('500')
    
    @classmethod
    def calculate_security_deposit(cls, project, estimated_tasks, ...):
        """Calculate required deposit based on complexity"""
        ...
    
    @classmethod
    def create_project_billing(cls, project, deposit_amount):
        """Create billing record and collect deposit"""
        ...
```

---

## Next Steps

- [Business Model →](./BUSINESS_MODEL.md)
- [Frontend Architecture →](./FRONTEND_ARCHITECTURE.md)
- [API Reference →](./api/README.md)
