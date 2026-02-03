import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.synapse')
django.setup()

from billing.models import SubscriptionPlan, CreditPackage
from decimal import Decimal

def update_billing_plans():
    # ------------------------------------------------------------------
    # 1. Update/Create Subscription Plans
    # ------------------------------------------------------------------
    
    # Define plans data
    plans_data = [
        # MONTHLY PLANS
        {
            "name": "Starter Monthly",
            "plan_type": "starter",
            "billing_cycle": "monthly",
            "price_inr": Decimal("19999.00"),
            "credits_per_month": 16000,
            "effective_rate": Decimal("1.25"),
            "storage_gb": 10,
            "extra_storage_rate_per_gb": Decimal("25.00"),
            "max_projects": 10,
            "max_users": None,
            "priority_support": True,
            "api_access": True,
            "credit_rollover": True,
            "max_rollover_months": 12
        },
        {
            "name": "Growth Monthly",
            "plan_type": "growth",
            "billing_cycle": "monthly",
            "price_inr": Decimal("49999.00"),
            "credits_per_month": 43000,
            "effective_rate": Decimal("1.16"),
            "storage_gb": 25,
            "extra_storage_rate_per_gb": Decimal("18.00"),
            "max_projects": 20,
            "max_users": None,
            "priority_support": True,
            "api_access": True,
            "credit_rollover": True,
            "max_rollover_months": 12
        },
        {
            "name": "Scale Monthly",
            "plan_type": "scale",
            "billing_cycle": "monthly",
            "price_inr": Decimal("79999.00"),
            "credits_per_month": 79999,
            "effective_rate": Decimal("1.00"),
            "storage_gb": 50,
            "extra_storage_rate_per_gb": Decimal("13.00"),
            "max_projects": 30,
            "max_users": None,
            "priority_support": True,
            "api_access": True,
            "credit_rollover": True,
            "max_rollover_months": 12
        },
        # ANNUAL PLANS
        {
            "name": "Starter Annual",
            "plan_type": "starter",
            "billing_cycle": "annual",
            "price_inr": Decimal("199990.00"),
            "credits_per_month": 18000,
            "effective_rate": Decimal("0.93"),
            "storage_gb": 10,
            "extra_storage_rate_per_gb": Decimal("25.00"),
            "max_projects": 10,
            "max_users": None,
            "priority_support": True,
            "api_access": True,
            "credit_rollover": True,
            "max_rollover_months": 12
        },
        {
            "name": "Growth Annual",
            "plan_type": "growth",
            "billing_cycle": "annual",
            "price_inr": Decimal("499990.00"),
            "credits_per_month": 45000,
            "effective_rate": Decimal("0.93"),
            "storage_gb": 25,
            "extra_storage_rate_per_gb": Decimal("18.00"),
            "max_projects": 20,
            "max_users": None,
            "priority_support": True,
            "api_access": True,
            "credit_rollover": True,
            "max_rollover_months": 12
        },
        {
            "name": "Scale Annual",
            "plan_type": "scale",
            "billing_cycle": "annual",
            "price_inr": Decimal("799990.00"),
            "credits_per_month": 81000,
            "effective_rate": Decimal("0.82"),
            "storage_gb": 50,
            "extra_storage_rate_per_gb": Decimal("13.00"),
            "max_projects": 30,
            "max_users": None,
            "priority_support": True,
            "api_access": True,
            "credit_rollover": True,
            "max_rollover_months": 12
        },
        # ENTERPRISE
        {
            "name": "Enterprise",
            "plan_type": "enterprise",
            "billing_cycle": "annual",
            "price_inr": Decimal("0.00"),
            "credits_per_month": 0,
            "effective_rate": Decimal("0.00"),
            "storage_gb": 100,
            "extra_storage_rate_per_gb": Decimal("10.00"),
            "max_projects": 0,
            "max_users": None,
            "priority_support": True,
            "api_access": True,
            "credit_rollover": True,
            "max_rollover_months": 12
        },
    ]

    print("\nUpdating Subscription Plans...")
    for p_data in plans_data:
        plan, created = SubscriptionPlan.objects.update_or_create(
            name=p_data["name"],
            billing_cycle=p_data["billing_cycle"],
            defaults=p_data
        )
        action = "Created" if created else "Updated"
        print(f"✅ {action}: {plan.name} (₹{plan.price_inr})")


    # ------------------------------------------------------------------
    # 2. Update/Create Credit Packages
    # ------------------------------------------------------------------
    
    credit_packages = [
        # (Credits, Price, Rate/Credit, Name)
        (5000, "8750.00", "1.75", "Explorer Package"),
        (25000, "37500.00", "1.50", "Professional Package"),
        (100000, "135000.00", "1.35", "Team Package"),
        (500000, "650000.00", "1.30", "Enterprise PAYG"),
    ]

    print("\nUpdating Credit Packages...")
    for credits, price, rate, name in credit_packages:
        pkg, created = CreditPackage.objects.update_or_create(
            credits=credits,
            defaults={
                "name": name,
                "price_inr": Decimal(price),
                "rate_per_credit": Decimal(rate),
                "is_active": True
            }
        )
        action = "Created" if created else "Updated"
        print(f"✅ {action}: {pkg.name} (₹{pkg.price_inr})")

if __name__ == "__main__":
    update_billing_plans()
