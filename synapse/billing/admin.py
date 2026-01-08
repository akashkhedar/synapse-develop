from django.contrib import admin
from .models import (
    SubscriptionPlan, CreditPackage, OrganizationBilling, Subscription,
    CreditTransaction, Payment, AnnotationPricing, AnnotatorEarnings, StorageBilling
)


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'plan_type', 'billing_cycle', 'price_inr', 'credits_per_month', 'effective_rate', 'is_active']
    list_filter = ['plan_type', 'billing_cycle', 'is_active']
    search_fields = ['name']


@admin.register(CreditPackage)
class CreditPackageAdmin(admin.ModelAdmin):
    list_display = ['name', 'credits', 'price_inr', 'rate_per_credit', 'is_active']
    list_filter = ['is_active']


@admin.register(OrganizationBilling)
class OrganizationBillingAdmin(admin.ModelAdmin):
    list_display = ['organization', 'billing_type', 'available_credits', 'rollover_credits', 'storage_used_gb']
    list_filter = ['billing_type']
    search_fields = ['organization__title', 'billing_email']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['organization', 'plan', 'status', 'start_date', 'end_date', 'auto_renew']
    list_filter = ['status', 'auto_renew', 'plan']
    search_fields = ['organization__title']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(CreditTransaction)
class CreditTransactionAdmin(admin.ModelAdmin):
    list_display = ['organization', 'transaction_type', 'category', 'amount', 'balance_after', 'created_at']
    list_filter = ['transaction_type', 'category', 'created_at']
    search_fields = ['organization__title', 'description']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['organization', 'payment_for', 'amount_inr', 'status', 'razorpay_order_id', 'created_at']
    list_filter = ['status', 'payment_for', 'created_at']
    search_fields = ['organization__title', 'razorpay_order_id', 'razorpay_payment_id']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(AnnotationPricing)
class AnnotationPricingAdmin(admin.ModelAdmin):
    list_display = ['data_type', 'modality', 'base_credit', 'unit_description', 'is_active']
    list_filter = ['data_type', 'is_active']
    search_fields = ['modality']


@admin.register(AnnotatorEarnings)
class AnnotatorEarningsAdmin(admin.ModelAdmin):
    list_display = ['annotator', 'organization', 'credits_earned', 'inr_equivalent', 'revenue_share_percentage', 'total_annotations']
    list_filter = ['revenue_share_percentage']
    search_fields = ['annotator__email', 'organization__title']


@admin.register(StorageBilling)
class StorageBillingAdmin(admin.ModelAdmin):
    list_display = ['organization', 'billing_month', 'storage_used_gb', 'billable_storage_gb', 'credits_charged', 'is_charged']
    list_filter = ['is_charged', 'billing_month']
    search_fields = ['organization__title']
    date_hierarchy = 'billing_month'





