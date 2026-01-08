from rest_framework import serializers
from .models import (
    SubscriptionPlan, CreditPackage, OrganizationBilling, Subscription,
    CreditTransaction, Payment, AnnotationPricing, AnnotatorEarnings, StorageBilling
)


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    effective_rate = serializers.FloatField()
    price_inr = serializers.FloatField()
    
    class Meta:
        model = SubscriptionPlan
        fields = [
            'id', 'name', 'plan_type', 'billing_cycle', 'price_inr', 'credits_per_month',
            'effective_rate', 'storage_gb', 'max_users', 'priority_support', 'api_access',
            'credit_rollover', 'max_rollover_months', 'is_active'
        ]


class CreditPackageSerializer(serializers.ModelSerializer):
    price_inr = serializers.FloatField()
    rate_per_credit = serializers.FloatField()
    
    class Meta:
        model = CreditPackage
        fields = ['id', 'name', 'credits', 'price_inr', 'rate_per_credit', 'is_active']


class OrganizationBillingSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.title', read_only=True)
    active_subscription_details = serializers.SerializerMethodField()
    available_credits = serializers.FloatField()
    rollover_credits = serializers.FloatField()
    storage_used_gb = serializers.FloatField()
    
    class Meta:
        model = OrganizationBilling
        fields = [
            'id', 'organization', 'organization_name', 'billing_type', 'available_credits',
            'rollover_credits', 'storage_used_gb', 'active_subscription', 
            'active_subscription_details', 'billing_email', 'gstin', 'created_at'
        ]
        read_only_fields = ['available_credits', 'rollover_credits', 'storage_used_gb']
    
    def get_active_subscription_details(self, obj):
        if obj.active_subscription:
            return SubscriptionSerializer(obj.active_subscription).data
        return None


class SubscriptionSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.title', read_only=True)
    plan_details = SubscriptionPlanSerializer(source='plan', read_only=True)
    
    class Meta:
        model = Subscription
        fields = [
            'id', 'organization', 'organization_name', 'plan', 'plan_details',
            'status', 'start_date', 'end_date', 'next_billing_date',
            'auto_renew', 'created_at'
        ]
        read_only_fields = ['start_date', 'end_date', 'next_billing_date', 'created_at']


class CreditTransactionSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.title', read_only=True)
    created_by_email = serializers.CharField(source='created_by.email', read_only=True)
    amount = serializers.FloatField()
    balance_after = serializers.FloatField()
    
    class Meta:
        model = CreditTransaction
        fields = [
            'id', 'organization', 'organization_name', 'transaction_type', 'category',
            'amount', 'balance_after', 'description', 'metadata', 'created_at',
            'created_by', 'created_by_email'
        ]
        read_only_fields = ['created_at', 'balance_after']


class PaymentSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.title', read_only=True)
    credit_package_details = CreditPackageSerializer(source='credit_package', read_only=True)
    amount_inr = serializers.FloatField()
    
    class Meta:
        model = Payment
        fields = [
            'id', 'organization', 'organization_name', 'payment_for', 
            'credit_package', 'credit_package_details', 'subscription',
            'amount_inr', 'status', 'razorpay_order_id', 'razorpay_payment_id',
            'payment_method', 'created_at', 'paid_at'
        ]
        read_only_fields = ['razorpay_order_id', 'created_at', 'paid_at']


class AnnotationPricingSerializer(serializers.ModelSerializer):
    base_credit = serializers.FloatField()
    classification_credit = serializers.FloatField(allow_null=True)
    bounding_box_credit = serializers.FloatField(allow_null=True)
    segmentation_credit = serializers.FloatField(allow_null=True)
    keypoint_credit = serializers.FloatField(allow_null=True)
    polygon_credit = serializers.FloatField(allow_null=True)
    time_sequence_credit = serializers.FloatField(allow_null=True)
    
    class Meta:
        model = AnnotationPricing
        fields = [
            'id', 'data_type', 'modality', 'base_credit', 'unit_description',
            'classification_credit', 'bounding_box_credit', 'segmentation_credit',
            'keypoint_credit', 'polygon_credit', 'time_sequence_credit', 'is_active'
        ]


class AnnotatorEarningsSerializer(serializers.ModelSerializer):
    annotator_email = serializers.CharField(source='annotator.email', read_only=True)
    organization_name = serializers.CharField(source='organization.title', read_only=True)
    credits_earned = serializers.FloatField()
    inr_equivalent = serializers.FloatField()
    revenue_share_percentage = serializers.FloatField()
    
    class Meta:
        model = AnnotatorEarnings
        fields = [
            'id', 'annotator', 'annotator_email', 'organization', 'organization_name',
            'credits_earned', 'inr_equivalent', 'revenue_share_percentage',
            'total_annotations', 'updated_at'
        ]
        read_only_fields = ['credits_earned', 'inr_equivalent', 'total_annotations']


class StorageBillingSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.title', read_only=True)
    storage_used_gb = serializers.FloatField()
    free_storage_gb = serializers.FloatField()
    billable_storage_gb = serializers.FloatField()
    credits_charged = serializers.FloatField()
    
    class Meta:
        model = StorageBilling
        fields = [
            'id', 'organization', 'organization_name', 'billing_month',
            'storage_used_gb', 'free_storage_gb', 'billable_storage_gb',
            'credits_charged', 'is_charged', 'charged_at', 'created_at'
        ]
        read_only_fields = ['billable_storage_gb', 'credits_charged', 'charged_at']


class CreatePaymentOrderSerializer(serializers.Serializer):
    """Serializer for creating Razorpay payment order"""
    payment_for = serializers.ChoiceField(choices=['credits', 'subscription'])
    credit_package_id = serializers.IntegerField(required=False)
    subscription_plan_id = serializers.IntegerField(required=False)
    
    def validate(self, data):
        if data['payment_for'] == 'credits' and not data.get('credit_package_id'):
            raise serializers.ValidationError("credit_package_id is required for credit purchase")
        if data['payment_for'] == 'subscription' and not data.get('subscription_plan_id'):
            raise serializers.ValidationError("subscription_plan_id is required for subscription")
        return data


class VerifyPaymentSerializer(serializers.Serializer):
    """Serializer for verifying Razorpay payment"""
    razorpay_order_id = serializers.CharField()
    razorpay_payment_id = serializers.CharField()
    razorpay_signature = serializers.CharField()





