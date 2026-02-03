"""
Script to setup subscription plans with proper tiers and pricing

Run with:
python manage.py shell < setup_subscription_plans.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.synapse')
django.setup()

from billing.models import SubscriptionPlan
from decimal import Decimal

print("Setting up subscription plans...")
print("=" * 70)

# Define all plans
PLANS = [
    # ==================== PAYG (Pay As You Go) ====================
    {
        "name": "Pay As You Go",
        "plan_type": "payg",
        "billing_cycle": "none",
        "price_inr": Decimal("0"),
        "credits_per_month": 0,
        "effective_rate": Decimal("1.00"),
        
        # Storage
        "storage_gb": 1,  # 1 GB free
        "extra_storage_rate_per_gb": Decimal("20.00"),  # Higher rate
        "storage_discount_percent": Decimal("0.00"),
        
        # Projects
        "max_projects": 2,
        
        # Discounts
        "annotation_discount_percent": Decimal("0.00"),
        "renewal_discount_percent": Decimal("0.00"),
        
        # Features
        "max_users": 2,
        "priority_support": False,
        "api_access": True,
        "credit_rollover": False,
        "max_rollover_months": 0,
        
        # Annual bonuses (N/A for PAYG)
        "annual_bonus_months": 0,
        "annual_bonus_credits": 0,
        
        "description": "Perfect for occasional projects. Pay only for what you use.",
        "features_json": [
            "2 Active Projects",
            "1 GB Free Storage",
            "Basic API Access",
            "Email Support",
            "No commitment",
        ],
    },
    
    # ==================== STARTER MONTHLY ====================
    {
        "name": "Starter Monthly",
        "plan_type": "starter",
        "billing_cycle": "monthly",
        "price_inr": Decimal("999"),
        "credits_per_month": 1200,
        "effective_rate": Decimal("0.83"),
        
        # Storage
        "storage_gb": 5,  # 5 GB free
        "extra_storage_rate_per_gb": Decimal("15.00"),
        "storage_discount_percent": Decimal("10.00"),  # 10% off extra storage
        
        # Projects
        "max_projects": 5,
        
        # Discounts
        "annotation_discount_percent": Decimal("5.00"),
        "renewal_discount_percent": Decimal("5.00"),  # 5% off if renewing
        
        # Features
        "max_users": 5,
        "priority_support": False,
        "api_access": True,
        "credit_rollover": True,
        "max_rollover_months": 1,
        
        # Annual bonuses
        "annual_bonus_months": 0,
        "annual_bonus_credits": 0,
        
        "description": "Great for small teams getting started with annotation.",
        "features_json": [
            "1,200 Credits/month",
            "5 Active Projects",
            "5 GB Free Storage",
            "10% Storage Discount",
            "5% Annotation Discount",
            "Credit Rollover (1 month)",
            "API Access",
            "Email Support",
        ],
    },
    
    # ==================== STARTER ANNUAL ====================
    {
        "name": "Starter Annual",
        "plan_type": "starter",
        "billing_cycle": "annual",
        "price_inr": Decimal("9990"),  # ~2 months free
        "credits_per_month": 1200,
        "effective_rate": Decimal("0.69"),
        
        # Storage
        "storage_gb": 10,  # Extra storage for annual
        "extra_storage_rate_per_gb": Decimal("12.00"),
        "storage_discount_percent": Decimal("20.00"),  # 20% off
        
        # Projects
        "max_projects": 7,
        
        # Discounts
        "annotation_discount_percent": Decimal("10.00"),
        "renewal_discount_percent": Decimal("10.00"),
        
        # Features
        "max_users": 5,
        "priority_support": False,
        "api_access": True,
        "credit_rollover": True,
        "max_rollover_months": 2,
        
        # Annual bonuses
        "annual_bonus_months": 2,  # Get 12 months for price of 10
        "annual_bonus_credits": 2000,  # Bonus credits
        
        "description": "Starter plan with annual savings - 2 months free!",
        "features_json": [
            "1,200 Credits/month",
            "2 Months FREE",
            "+2,000 Bonus Credits",
            "7 Active Projects",
            "10 GB Free Storage",
            "20% Storage Discount",
            "10% Annotation Discount",
            "Credit Rollover (2 months)",
            "API Access",
            "Priority Email Support",
        ],
    },
    
    # ==================== GROWTH MONTHLY ====================
    {
        "name": "Growth Monthly",
        "plan_type": "growth",
        "billing_cycle": "monthly",
        "price_inr": Decimal("2999"),
        "credits_per_month": 4000,
        "effective_rate": Decimal("0.75"),
        
        # Storage
        "storage_gb": 20,
        "extra_storage_rate_per_gb": Decimal("12.00"),
        "storage_discount_percent": Decimal("20.00"),
        
        # Projects
        "max_projects": 15,
        
        # Discounts
        "annotation_discount_percent": Decimal("10.00"),
        "renewal_discount_percent": Decimal("8.00"),
        
        # Features
        "max_users": 15,
        "priority_support": True,
        "api_access": True,
        "credit_rollover": True,
        "max_rollover_months": 2,
        
        # Annual bonuses
        "annual_bonus_months": 0,
        "annual_bonus_credits": 0,
        
        "description": "Perfect for growing teams with regular annotation needs.",
        "features_json": [
            "4,000 Credits/month",
            "15 Active Projects",
            "20 GB Free Storage",
            "20% Storage Discount",
            "10% Annotation Discount",
            "Credit Rollover (2 months)",
            "Priority Support",
            "Full API Access",
        ],
    },
    
    # ==================== GROWTH ANNUAL ====================
    {
        "name": "Growth Annual",
        "plan_type": "growth",
        "billing_cycle": "annual",
        "price_inr": Decimal("29990"),  # ~2 months free
        "credits_per_month": 4000,
        "effective_rate": Decimal("0.625"),
        
        # Storage
        "storage_gb": 50,  # Much more storage for annual
        "extra_storage_rate_per_gb": Decimal("10.00"),
        "storage_discount_percent": Decimal("30.00"),
        
        # Projects
        "max_projects": 25,
        
        # Discounts
        "annotation_discount_percent": Decimal("15.00"),
        "renewal_discount_percent": Decimal("12.00"),
        
        # Features
        "max_users": 20,
        "priority_support": True,
        "api_access": True,
        "credit_rollover": True,
        "max_rollover_months": 3,
        
        # Annual bonuses
        "annual_bonus_months": 2,
        "annual_bonus_credits": 8000,
        
        "description": "Growth plan with massive annual savings!",
        "features_json": [
            "4,000 Credits/month",
            "2 Months FREE",
            "+8,000 Bonus Credits",
            "25 Active Projects",
            "50 GB Free Storage",
            "30% Storage Discount",
            "15% Annotation Discount",
            "Credit Rollover (3 months)",
            "Priority Phone Support",
            "Full API Access",
        ],
    },
    
    # ==================== SCALE MONTHLY ====================
    {
        "name": "Scale Monthly",
        "plan_type": "scale",
        "billing_cycle": "monthly",
        "price_inr": Decimal("7999"),
        "credits_per_month": 12000,
        "effective_rate": Decimal("0.67"),
        
        # Storage
        "storage_gb": 100,
        "extra_storage_rate_per_gb": Decimal("8.00"),
        "storage_discount_percent": Decimal("40.00"),
        
        # Projects
        "max_projects": 50,
        
        # Discounts
        "annotation_discount_percent": Decimal("20.00"),
        "renewal_discount_percent": Decimal("10.00"),
        
        # Features
        "max_users": 50,
        "priority_support": True,
        "api_access": True,
        "credit_rollover": True,
        "max_rollover_months": 3,
        
        # Annual bonuses
        "annual_bonus_months": 0,
        "annual_bonus_credits": 0,
        
        "description": "For teams with high-volume annotation requirements.",
        "features_json": [
            "12,000 Credits/month",
            "50 Active Projects",
            "100 GB Free Storage",
            "40% Storage Discount",
            "20% Annotation Discount",
            "Credit Rollover (3 months)",
            "Dedicated Support",
            "Full API Access",
            "SLA Guarantee",
        ],
    },
    
    # ==================== SCALE ANNUAL ====================
    {
        "name": "Scale Annual",
        "plan_type": "scale",
        "billing_cycle": "annual",
        "price_inr": Decimal("79990"),  # ~2 months free
        "credits_per_month": 12000,
        "effective_rate": Decimal("0.56"),
        
        # Storage
        "storage_gb": 250,
        "extra_storage_rate_per_gb": Decimal("5.00"),
        "storage_discount_percent": Decimal("50.00"),
        
        # Projects
        "max_projects": 0,  # Unlimited
        
        # Discounts
        "annotation_discount_percent": Decimal("25.00"),
        "renewal_discount_percent": Decimal("15.00"),
        
        # Features
        "max_users": None,  # Unlimited
        "priority_support": True,
        "api_access": True,
        "credit_rollover": True,
        "max_rollover_months": 6,
        
        # Annual bonuses
        "annual_bonus_months": 2,
        "annual_bonus_credits": 25000,
        
        "description": "Scale plan with maximum savings and unlimited features!",
        "features_json": [
            "12,000 Credits/month",
            "2 Months FREE",
            "+25,000 Bonus Credits",
            "Unlimited Projects",
            "250 GB Free Storage",
            "50% Storage Discount",
            "25% Annotation Discount",
            "Credit Rollover (6 months)",
            "Dedicated Account Manager",
            "Full API Access",
            "99.9% SLA Guarantee",
        ],
    },
    
    # ==================== ENTERPRISE ====================
    {
        "name": "Enterprise",
        "plan_type": "enterprise",
        "billing_cycle": "annual",
        "price_inr": Decimal("0"),  # Custom pricing
        "credits_per_month": 0,  # Custom
        "effective_rate": Decimal("0.50"),
        
        # Storage
        "storage_gb": 1000,  # 1 TB free
        "extra_storage_rate_per_gb": Decimal("3.00"),
        "storage_discount_percent": Decimal("60.00"),
        
        # Projects
        "max_projects": 0,  # Unlimited
        
        # Discounts
        "annotation_discount_percent": Decimal("30.00"),
        "renewal_discount_percent": Decimal("20.00"),
        
        # Features
        "max_users": None,  # Unlimited
        "priority_support": True,
        "api_access": True,
        "credit_rollover": True,
        "max_rollover_months": 12,
        
        # Annual bonuses
        "annual_bonus_months": 0,
        "annual_bonus_credits": 0,
        
        "description": "Custom solutions for large organizations. Contact sales.",
        "features_json": [
            "Custom Credits Package",
            "Unlimited Projects",
            "1 TB Free Storage",
            "60% Storage Discount",
            "30% Annotation Discount",
            "Unlimited Credit Rollover",
            "24/7 Dedicated Support",
            "Custom Integrations",
            "On-premise Option",
            "Custom SLA",
            "Training & Onboarding",
        ],
    },
]


# Create or update plans
for plan_data in PLANS:
    plan, created = SubscriptionPlan.objects.update_or_create(
        name=plan_data["name"],
        defaults=plan_data
    )
    
    status = "Created" if created else "Updated"
    print(f"{status}: {plan.name}")
    print(f"  - Type: {plan.plan_type} | Cycle: {plan.billing_cycle}")
    print(f"  - Price: ₹{plan.price_inr} | Credits: {plan.credits_per_month}/month")
    print(f"  - Storage: {plan.storage_gb} GB free | Extra: ₹{plan.extra_storage_rate_per_gb}/GB")
    print(f"  - Projects: {'Unlimited' if plan.max_projects == 0 else plan.max_projects}")
    print(f"  - Discounts: Annotation {plan.annotation_discount_percent}% | Storage {plan.storage_discount_percent}%")
    if plan.annual_bonus_months > 0:
        print(f"  - Annual Bonus: {plan.annual_bonus_months} free months + {plan.annual_bonus_credits} credits")
    print()

print("=" * 70)
print("Setup Complete!")
print(f"Total plans: {SubscriptionPlan.objects.count()}")

# Print summary table
print("\n" + "=" * 70)
print("PLAN COMPARISON TABLE")
print("=" * 70)
print(f"{'Plan':<25} {'Price':<12} {'Credits':<10} {'Storage':<10} {'Projects':<10}")
print("-" * 70)

for plan in SubscriptionPlan.objects.filter(is_active=True).order_by('price_inr'):
    projects = "∞" if plan.max_projects == 0 else str(plan.max_projects)
    print(f"{plan.name:<25} ₹{plan.price_inr:<10} {plan.credits_per_month:<10} {plan.storage_gb} GB{'':<5} {projects:<10}")

print("=" * 70)
