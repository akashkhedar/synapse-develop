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





