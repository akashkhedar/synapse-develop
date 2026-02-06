from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers
from .models import (
    AnnotatorProfile,
    AnnotationTest,
    TrustLevel,
    PayoutRequest,
    EarningsTransaction,
)

User = get_user_model()


class AnnotatorRegistrationSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=150, write_only=True)
    last_name = serializers.CharField(max_length=150, write_only=True)
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True, min_length=8)

    phone = serializers.CharField(max_length=20, write_only=True)
    skills = serializers.ListField(
        child=serializers.CharField(), required=False, default=list, write_only=True
    )
    languages = serializers.ListField(
        child=serializers.CharField(), required=False, default=list, write_only=True
    )
    experience_level = serializers.ChoiceField(
        choices=["beginner", "intermediate", "expert"],
        default="beginner",
        write_only=True,
    )
    bio = serializers.CharField(required=False, allow_blank=True, write_only=True)

    @transaction.atomic
    def create(self, validated_data):
        email = validated_data["email"]

        user = User.objects.create_user(
            username=email,  # acceptable if email == identity
            email=email,
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            password=validated_data["password"],
        )

        profile = AnnotatorProfile.objects.create(
            user=user,
            phone=validated_data["phone"],
            skills=validated_data.get("skills", []),
            languages=validated_data.get("languages", []),
            experience_level=validated_data.get("experience_level", "beginner"),
            bio=validated_data.get("bio", ""),
            status="pending_verification",
        )

        profile.generate_verification_token()
        return profile


class AnnotatorProfileSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = AnnotatorProfile
        fields = [
            "id",
            "user_email",
            "user_name",
            "phone",
            "skills",
            "languages",
            "experience_level",
            "bio",
            "status",
            "email_verified",
            "total_tasks_completed",
            "accuracy_score",
            "rejection_rate",
            "total_earned",
            "available_balance",
            "applied_at",
            "last_active",
        ]
        read_only_fields = [
            "status",
            "email_verified",
            "total_tasks_completed",
            "accuracy_score",
            "rejection_rate",
            "total_earned",
            "available_balance",
            "applied_at",
            "last_active",
        ]

    def get_user_name(self, obj):
        return obj.user.get_full_name() or obj.user.email


class AnnotationTestSerializer(serializers.ModelSerializer):
    annotator_name = serializers.SerializerMethodField()

    class Meta:
        model = AnnotationTest
        fields = [
            "id",
            "annotator",
            "annotator_name",
            "test_type",
            "status",
            "started_at",
            "submitted_at",
            "accuracy",
            "feedback",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields  # tests should never be edited directly

    def get_annotator_name(self, obj):
        return obj.annotator.user.get_full_name() or obj.annotator.user.email


class TrustLevelSerializer(serializers.ModelSerializer):
    """Serializer for annotator trust level information."""

    annotator_name = serializers.SerializerMethodField()
    level_display = serializers.CharField(source="get_level_display", read_only=True)
    next_level = serializers.SerializerMethodField()
    progress_to_next = serializers.SerializerMethodField()

    class Meta:
        model = TrustLevel
        fields = [
            "id",
            "annotator",
            "annotator_name",
            "level",
            "level_display",
            "multiplier",
            "tasks_completed",
            "accuracy_score",
            "honeypot_pass_rate",
            "total_honeypots",
            "passed_honeypots",
            "fraud_flags",
            "is_suspended",
            "level_updated_at",
            "next_level",
            "progress_to_next",
            "created_at",
        ]
        read_only_fields = fields

    def get_annotator_name(self, obj):
        return obj.annotator.user.get_full_name() or obj.annotator.user.email

    def get_next_level(self, obj):
        """Get the next trust level."""
        levels = ["new", "junior", "regular", "senior", "expert"]
        try:
            current_index = levels.index(obj.level)
            if current_index < len(levels) - 1:
                return levels[current_index + 1]
        except ValueError:
            pass
        return None

    def get_progress_to_next(self, obj):
        """Calculate progress towards next level."""
        thresholds = TrustLevel.LEVEL_THRESHOLDS
        next_level = self.get_next_level(obj)

        if not next_level:
            return {"complete": True, "percentage": 100}

        next_thresholds = thresholds.get(next_level, {})

        # Calculate progress for each metric
        tasks_needed = next_thresholds.get("tasks", 0)
        accuracy_needed = next_thresholds.get("accuracy", 0)
        honeypot_needed = next_thresholds.get("honeypot_rate", 0)

        tasks_progress = (
            min(100, (obj.tasks_completed / tasks_needed * 100))
            if tasks_needed > 0
            else 100
        )
        accuracy_progress = (
            min(100, (float(obj.accuracy_score) / accuracy_needed * 100))
            if accuracy_needed > 0
            else 100
        )
        honeypot_progress = (
            min(100, (float(obj.honeypot_pass_rate) / honeypot_needed * 100))
            if honeypot_needed > 0
            else 100
        )

        overall = (tasks_progress + accuracy_progress + honeypot_progress) / 3

        return {
            "complete": False,
            "percentage": round(overall, 1),
            "tasks": {
                "current": obj.tasks_completed,
                "required": tasks_needed,
                "progress": round(tasks_progress, 1),
            },
            "accuracy": {
                "current": float(obj.accuracy_score),
                "required": accuracy_needed,
                "progress": round(accuracy_progress, 1),
            },
            "honeypot": {
                "current": float(obj.honeypot_pass_rate),
                "required": honeypot_needed,
                "progress": round(honeypot_progress, 1),
            },
        }


class PayoutRequestSerializer(serializers.ModelSerializer):
    """Serializer for payout requests."""

    annotator_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = PayoutRequest
        fields = [
            "id",
            "annotator",
            "annotator_name",
            "amount",
            "status",
            "status_display",
            "payout_method",
            "bank_name",
            "account_number_last4",
            "ifsc_code",
            "account_holder_name",
            "upi_id",
            "transaction_id",
            "admin_notes",
            "requested_at",
            "processed_at",
        ]
        read_only_fields = [
            "id",
            "annotator",
            "annotator_name",
            "status",
            "status_display",
            "account_number_last4",
            "transaction_id",
            "admin_notes",
            "requested_at",
            "processed_at",
        ]

    def get_annotator_name(self, obj):
        return obj.annotator.user.get_full_name() or obj.annotator.user.email


class PayoutRequestCreateSerializer(serializers.Serializer):
    """Serializer for creating payout requests."""

    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=100)
    payout_method = serializers.ChoiceField(choices=["bank_transfer", "upi"])
    bank_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    account_number = serializers.CharField(
        max_length=20, required=False, allow_blank=True
    )
    ifsc_code = serializers.CharField(max_length=11, required=False, allow_blank=True)
    account_holder_name = serializers.CharField(
        max_length=200, required=False, allow_blank=True
    )
    upi_id = serializers.CharField(max_length=100, required=False, allow_blank=True)

    def validate(self, data):
        payout_method = data.get("payout_method")

        if payout_method == "bank_transfer":
            if not data.get("bank_name"):
                raise serializers.ValidationError(
                    {"bank_name": "Bank name is required for bank transfer."}
                )
            if not data.get("account_number"):
                raise serializers.ValidationError(
                    {"account_number": "Account number is required for bank transfer."}
                )
            if not data.get("ifsc_code"):
                raise serializers.ValidationError(
                    {"ifsc_code": "IFSC code is required for bank transfer."}
                )
            if not data.get("account_holder_name"):
                raise serializers.ValidationError(
                    {
                        "account_holder_name": "Account holder name is required for bank transfer."
                    }
                )
        elif payout_method == "upi":
            if not data.get("upi_id"):
                raise serializers.ValidationError(
                    {"upi_id": "UPI ID is required for UPI payout."}
                )

        return data


class EarningsTransactionSerializer(serializers.ModelSerializer):
    """Serializer for earnings transactions."""

    annotator_name = serializers.SerializerMethodField()
    transaction_type_display = serializers.CharField(
        source="get_transaction_type_display", read_only=True
    )
    project_name = serializers.SerializerMethodField()
    task_id = serializers.SerializerMethodField()

    class Meta:
        model = EarningsTransaction
        fields = [
            "id",
            "annotator",
            "annotator_name",
            "transaction_type",
            "transaction_type_display",
            "amount",
            "balance_after",
            "description",
            "task_assignment",
            "task_id",
            "project_name",
            "payout_request",
            "created_at",
        ]
        read_only_fields = fields

    def get_annotator_name(self, obj):
        return obj.annotator.user.get_full_name() or obj.annotator.user.email

    def get_project_name(self, obj):
        if (
            obj.task_assignment
            and obj.task_assignment.task
            and obj.task_assignment.task.project
        ):
            return obj.task_assignment.task.project.title
        return None

    def get_task_id(self, obj):
        if obj.task_assignment and obj.task_assignment.task:
            return obj.task_assignment.task.id
        return None


class BankDetailsSerializer(serializers.Serializer):
    """Serializer for storing/updating bank details."""

    payout_method = serializers.ChoiceField(choices=["bank_transfer", "upi"])
    bank_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    account_number = serializers.CharField(
        max_length=20, required=False, allow_blank=True
    )
    ifsc_code = serializers.CharField(max_length=11, required=False, allow_blank=True)
    account_holder_name = serializers.CharField(
        max_length=200, required=False, allow_blank=True
    )
    upi_id = serializers.CharField(max_length=100, required=False, allow_blank=True)

    def validate(self, data):
        payout_method = data.get("payout_method")

        if payout_method == "bank_transfer":
            if not data.get("bank_name"):
                raise serializers.ValidationError(
                    {"bank_name": "Bank name is required for bank transfer."}
                )
            if not data.get("account_number"):
                raise serializers.ValidationError(
                    {"account_number": "Account number is required for bank transfer."}
                )
            if not data.get("ifsc_code"):
                raise serializers.ValidationError(
                    {"ifsc_code": "IFSC code is required for bank transfer."}
                )
            if not data.get("account_holder_name"):
                raise serializers.ValidationError(
                    {
                        "account_holder_name": "Account holder name is required for bank transfer."
                    }
                )
        elif payout_method == "upi":
            if not data.get("upi_id"):
                raise serializers.ValidationError(
                    {"upi_id": "UPI ID is required for UPI payout."}
                )

        return data


class EarningsSummarySerializer(serializers.Serializer):
    """Serializer for earnings summary response."""

    available_balance = serializers.DecimalField(max_digits=10, decimal_places=2)
    pending_earnings = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_earned = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_withdrawn = serializers.DecimalField(max_digits=10, decimal_places=2)
    pending_payout = serializers.DecimalField(max_digits=10, decimal_places=2)
    tasks_completed = serializers.IntegerField()
    trust_level = serializers.CharField()
    payment_multiplier = serializers.DecimalField(max_digits=3, decimal_places=2)
    this_week_earnings = serializers.DecimalField(max_digits=10, decimal_places=2)
    this_month_earnings = serializers.DecimalField(max_digits=10, decimal_places=2)


# ============================================================================
# EXPERTISE SYSTEM SERIALIZERS
# ============================================================================

from .models import (
    ExpertiseCategory,
    ExpertiseSpecialization,
    AnnotatorExpertise,
    ExpertiseTestQuestion,
    ExpertiseTest,
)


class ExpertiseSpecializationSerializer(serializers.ModelSerializer):
    """Serializer for expertise specializations."""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = ExpertiseSpecialization
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'icon',
            'template_folder',
            'requires_certification',
            'certification_instructions',
            'min_test_questions',
            'passing_score',
            'display_order',
            'is_active',
            'category',
            'category_name',
        ]
        read_only_fields = ['id', 'category_name']


class ExpertiseCategorySerializer(serializers.ModelSerializer):
    """Serializer for expertise categories."""
    
    specializations = ExpertiseSpecializationSerializer(many=True, read_only=True)
    specialization_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ExpertiseCategory
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'icon',
            'template_folder',
            'display_order',
            'is_active',
            'specializations',
            'specialization_count',
        ]
        read_only_fields = ['id', 'specializations', 'specialization_count']
    
    def get_specialization_count(self, obj):
        return obj.specializations.filter(is_active=True).count()


class ExpertiseCategoryListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for category listing."""
    
    specialization_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ExpertiseCategory
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'icon',
            'template_folder',
            'display_order',
            'specialization_count',
        ]
    
    def get_specialization_count(self, obj):
        return obj.specializations.filter(is_active=True).count()


class AnnotatorExpertiseSerializer(serializers.ModelSerializer):
    """Serializer for annotator expertise records."""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_slug = serializers.CharField(source='category.slug', read_only=True)
    specialization_name = serializers.CharField(
        source='specialization.name', 
        read_only=True, 
        allow_null=True
    )
    specialization_slug = serializers.CharField(
        source='specialization.slug', 
        read_only=True, 
        allow_null=True
    )
    is_verified = serializers.BooleanField(read_only=True)
    can_retry = serializers.SerializerMethodField()
    
    class Meta:
        model = AnnotatorExpertise
        fields = [
            'id',
            'category',
            'category_name',
            'category_slug',
            'specialization',
            'specialization_name',
            'specialization_slug',
            'status',
            'test_attempts',
            'last_test_score',
            'last_test_at',
            'verified_at',
            'expires_at',
            'is_verified',
            'can_retry',
            'tasks_completed',
            'accuracy_score',
            'self_rating',
            'years_experience',
            'notes',
            'created_at',
        ]
        read_only_fields = [
            'id', 'status', 'test_attempts', 'last_test_score', 
            'last_test_at', 'verified_at', 'is_verified', 'can_retry',
            'tasks_completed', 'accuracy_score', 'created_at',
        ]
    
    def get_can_retry(self, obj):
        return obj.can_retry_test()


class AnnotatorExpertiseCreateSerializer(serializers.Serializer):
    """Serializer for claiming expertise."""
    
    category_id = serializers.IntegerField()
    specialization_id = serializers.IntegerField(required=False, allow_null=True)
    self_rating = serializers.IntegerField(min_value=1, max_value=10, default=5)
    years_experience = serializers.IntegerField(min_value=0, default=0)
    notes = serializers.CharField(required=False, allow_blank=True, default='')
    
    def validate_category_id(self, value):
        try:
            ExpertiseCategory.objects.get(id=value, is_active=True)
        except ExpertiseCategory.DoesNotExist:
            raise serializers.ValidationError("Invalid or inactive category.")
        return value
    
    def validate_specialization_id(self, value):
        if value is None:
            return value
        try:
            ExpertiseSpecialization.objects.get(id=value, is_active=True)
        except ExpertiseSpecialization.DoesNotExist:
            raise serializers.ValidationError("Invalid or inactive specialization.")
        return value
    
    def validate(self, data):
        # Ensure specialization belongs to category if both provided
        if data.get('specialization_id'):
            spec = ExpertiseSpecialization.objects.get(id=data['specialization_id'])
            if spec.category_id != data['category_id']:
                raise serializers.ValidationError({
                    'specialization_id': 'Specialization does not belong to selected category.'
                })
        return data


class ExpertiseTestQuestionSerializer(serializers.ModelSerializer):
    """Serializer for test questions (without answers for test-taking)."""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    specialization_name = serializers.CharField(
        source='specialization.name', 
        read_only=True, 
        allow_null=True
    )
    
    class Meta:
        model = ExpertiseTestQuestion
        fields = [
            'id',
            'question_type',
            'difficulty',
            'question_text',
            'question_image_url',
            'question_data',
            'options',
            'points',
            'partial_credit',
            'category_name',
            'specialization_name',
        ]
        # Note: correct_answer and explanation excluded for test-taking


class ExpertiseTestQuestionAdminSerializer(serializers.ModelSerializer):
    """Full serializer for admins (includes answers)."""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    specialization_name = serializers.CharField(
        source='specialization.name', 
        read_only=True, 
        allow_null=True
    )
    
    class Meta:
        model = ExpertiseTestQuestion
        fields = [
            'id',
            'category',
            'category_name',
            'specialization',
            'specialization_name',
            'question_type',
            'difficulty',
            'question_text',
            'question_image_url',
            'question_data',
            'options',
            'correct_answer',
            'points',
            'partial_credit',
            'explanation',
            'is_active',
            'created_at',
            'updated_at',
        ]


class ExpertiseTestSerializer(serializers.ModelSerializer):
    """Serializer for expertise test attempts."""
    
    expertise_category = serializers.CharField(
        source='expertise.category.name', 
        read_only=True
    )
    expertise_specialization = serializers.CharField(
        source='expertise.specialization.name', 
        read_only=True, 
        allow_null=True
    )
    questions = ExpertiseTestQuestionSerializer(many=True, read_only=True)
    
    class Meta:
        model = ExpertiseTest
        fields = [
            'id',
            'expertise',
            'expertise_category',
            'expertise_specialization',
            'status',
            'score',
            'max_score',
            'percentage',
            'passed',
            'time_limit_minutes',
            'started_at',
            'submitted_at',
            'feedback',
            'questions',
            'created_at',
        ]
        read_only_fields = fields


class ExpertiseTestResultSerializer(serializers.ModelSerializer):
    """Serializer for test results (includes breakdown)."""
    
    expertise_category = serializers.CharField(
        source='expertise.category.name', 
        read_only=True
    )
    expertise_specialization = serializers.CharField(
        source='expertise.specialization.name', 
        read_only=True, 
        allow_null=True
    )
    
    class Meta:
        model = ExpertiseTest
        fields = [
            'id',
            'expertise',
            'expertise_category',
            'expertise_specialization',
            'status',
            'score',
            'max_score',
            'percentage',
            'passed',
            'results_breakdown',
            'feedback',
            'started_at',
            'submitted_at',
        ]


class AnnotatorExpertiseSummarySerializer(serializers.Serializer):
    """Summary serializer for dashboard display."""
    
    verified_expertise = AnnotatorExpertiseSerializer(many=True)
    pending_expertise = AnnotatorExpertiseSerializer(many=True)
    failed_expertise = AnnotatorExpertiseSerializer(many=True)
    total_verified = serializers.IntegerField()
    total_tasks_by_expertise = serializers.DictField()






