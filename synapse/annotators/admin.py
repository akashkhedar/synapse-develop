"""Admin interface for annotators"""

from django.contrib import admin
from .models import AnnotatorProfile, AnnotationTest
from django.utils import timezone


@admin.register(AnnotatorProfile)
class AnnotatorProfileAdmin(admin.ModelAdmin):
    list_display = [
        "user_email",
        "status",
        "email_verified",
        "experience_level",
        "total_tasks_completed",
        "accuracy_score",
        "applied_at",
    ]

    list_filter = ["status", "email_verified", "experience_level", "applied_at"]
    search_fields = [
        "user__email",
        "user__first_name",
        "user__last_name",
        "phone",
    ]

    readonly_fields = [
        "applied_at",
        "last_active",
        "verification_token",
        "verification_token_created",
        "total_tasks_completed",
        "accuracy_score",
        "rejection_rate",
        "total_earned",
        "available_balance",
        "total_withdrawn",
    ]

    fieldsets = (
        ("User Information", {"fields": ("user", "status", "email_verified")}),
        ("Contact Details", {"fields": ("phone", "alternate_email", "address")}),
        (
            "Skills & Experience",
            {"fields": ("skills", "languages", "experience_level", "bio")},
        ),
        (
            "Performance Metrics",
            {
                "fields": (
                    "total_tasks_completed",
                    "accuracy_score",
                    "average_time_per_task",
                    "rejection_rate",
                )
            },
        ),
        (
            "Earnings",
            {
                "fields": (
                    "total_earned",
                    "pending_approval",
                    "available_balance",
                    "total_withdrawn",
                )
            },
        ),
        (
            "Bank Details",
            {
                "fields": (
                    "bank_name",
                    "account_number",
                    "ifsc_code",
                    "account_holder_name",
                    "upi_id",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "applied_at",
                    "approved_at",
                    "rejected_at",
                    "last_active",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Verification",
            {
                "fields": (
                    "verification_token",
                    "verification_token_created",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    actions = ["approve_annotators", "reject_annotators"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("user")

    def user_email(self, obj):
        return obj.user.email

    user_email.short_description = "Email"
    user_email.admin_order_field = "user__email"

    def approve_annotators(self, request, queryset):
        for profile in queryset:
            profile.status = "approved"
            profile.approved_at = timezone.now()
            profile.user.is_active = True
            profile.user.save(update_fields=["is_active"])
            profile.save(update_fields=["status", "approved_at"])

        self.message_user(request, f"{queryset.count()} annotators approved")

    approve_annotators.short_description = "Approve selected annotators"

    def reject_annotators(self, request, queryset):
        for profile in queryset:
            profile.status = "rejected"
            profile.rejected_at = timezone.now()
            profile.user.is_active = False
            profile.user.save(update_fields=["is_active"])
            profile.save(update_fields=["status", "rejected_at"])

        self.message_user(request, f"{queryset.count()} annotators rejected")

    reject_annotators.short_description = "Reject selected annotators"


@admin.register(AnnotationTest)
class AnnotationTestAdmin(admin.ModelAdmin):
    list_display = [
        "annotator",
        "test_type",
        "status",
        "accuracy",
        "submitted_at",
        "evaluated_at",
    ]

    list_filter = ["status", "test_type", "submitted_at"]
    search_fields = [
        "annotator__user__email",
        "annotator__user__first_name",
        "annotator__user__last_name",
    ]

    readonly_fields = ["created_at", "updated_at"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("annotator", "annotator__user")


# ============================================================================
# EXPERTISE SYSTEM ADMIN
# ============================================================================

from .models import (
    ExpertiseCategory,
    ExpertiseSpecialization,
    AnnotatorExpertise,
    ExpertiseTestQuestion,
    ExpertiseTest,
)


class ExpertiseSpecializationInline(admin.TabularInline):
    model = ExpertiseSpecialization
    extra = 0
    fields = ['name', 'slug', 'template_folder', 'passing_score', 'requires_certification', 'is_active', 'display_order']


@admin.register(ExpertiseCategory)
class ExpertiseCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'template_folder', 'specialization_count', 'is_active', 'display_order']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ExpertiseSpecializationInline]
    ordering = ['display_order', 'name']
    
    def specialization_count(self, obj):
        return obj.specializations.count()
    specialization_count.short_description = 'Specializations'


@admin.register(ExpertiseSpecialization)
class ExpertiseSpecializationAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'template_folder', 'passing_score', 'requires_certification', 'is_active']
    list_filter = ['category', 'is_active', 'requires_certification']
    search_fields = ['name', 'description', 'category__name']
    prepopulated_fields = {'slug': ('name',)}
    raw_id_fields = ['category']
    ordering = ['category', 'display_order', 'name']


@admin.register(AnnotatorExpertise)
class AnnotatorExpertiseAdmin(admin.ModelAdmin):
    list_display = [
        'annotator_email',
        'category',
        'specialization',
        'status',
        'last_test_score',
        'tasks_completed',
        'verified_at',
    ]
    list_filter = ['status', 'category', 'specialization']
    search_fields = [
        'annotator__user__email',
        'annotator__user__first_name',
        'category__name',
        'specialization__name',
    ]
    raw_id_fields = ['annotator', 'category', 'specialization']
    readonly_fields = [
        'test_attempts', 'last_test_score', 'last_test_at',
        'verified_at', 'tasks_completed', 'accuracy_score',
        'created_at', 'updated_at'
    ]
    
    def annotator_email(self, obj):
        return obj.annotator.user.email
    annotator_email.short_description = 'Annotator'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('annotator__user', 'category', 'specialization')


@admin.register(ExpertiseTestQuestion)
class ExpertiseTestQuestionAdmin(admin.ModelAdmin):
    list_display = [
        'short_question',
        'category',
        'specialization',
        'question_type',
        'difficulty',
        'points',
        'is_active',
    ]
    list_filter = ['category', 'specialization', 'question_type', 'difficulty', 'is_active']
    search_fields = ['question_text', 'category__name', 'specialization__name']
    raw_id_fields = ['category', 'specialization', 'created_by']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Question Info', {
            'fields': ('category', 'specialization', 'question_type', 'difficulty')
        }),
        ('Question Content', {
            'fields': ('question_text', 'question_image_url', 'question_data')
        }),
        ('Answer', {
            'fields': ('options', 'correct_answer', 'points', 'partial_credit')
        }),
        ('Explanation', {
            'fields': ('explanation',)
        }),
        ('Status', {
            'fields': ('is_active', 'created_by', 'created_at', 'updated_at')
        }),
    )
    
    def short_question(self, obj):
        return obj.question_text[:60] + '...' if len(obj.question_text) > 60 else obj.question_text
    short_question.short_description = 'Question'


@admin.register(ExpertiseTest)
class ExpertiseTestAdmin(admin.ModelAdmin):
    list_display = [
        'annotator_email',
        'expertise_display',
        'status',
        'score',
        'percentage',
        'passed',
        'started_at',
        'submitted_at',
    ]
    list_filter = ['status', 'passed', 'expertise__category']
    search_fields = [
        'annotator__user__email',
        'expertise__category__name',
        'expertise__specialization__name',
    ]
    raw_id_fields = ['annotator', 'expertise']
    readonly_fields = [
        'score', 'max_score', 'percentage', 'passed',
        'results_breakdown', 'started_at', 'submitted_at',
        'created_at', 'updated_at'
    ]
    filter_horizontal = ['questions']
    
    def annotator_email(self, obj):
        return obj.annotator.user.email
    annotator_email.short_description = 'Annotator'
    
    def expertise_display(self, obj):
        if obj.expertise.specialization:
            return f"{obj.expertise.category.name} / {obj.expertise.specialization.name}"
        return obj.expertise.category.name
    expertise_display.short_description = 'Expertise'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            'annotator__user',
            'expertise__category',
            'expertise__specialization'
        )





