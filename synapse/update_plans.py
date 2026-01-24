
from billing.models import SubscriptionPlan, CreditPackage
from decimal import Decimal

def update_billing_plans():
    # ------------------------------------------------------------------
    # 1. Update/Create Subscription Plans
    # ------------------------------------------------------------------
    
    # Define plans data
    plans_data = [
        # TEST PLAN (Temporary)
        {
            "name": "Test Subscription",
            "plan_type": "starter", # Using starter type for features
            "billing_cycle": "monthly",
            "price_inr": Decimal("1.00"),
            "credits_per_month": 10000,
            "effective_rate": Decimal("0.00"),
            "storage_gb": 10,
            "max_users": 1,
            "priority_support": True,
            "api_access": True,
            "credit_rollover": True,
            "max_rollover_months": 1
        },
        # MONTHLY PLANS
        {
            "name": "Starter Monthly",
            "plan_type": "starter",
            "billing_cycle": "monthly",
            "price_inr": Decimal("2499.00"),
            "credits_per_month": 500,
            "effective_rate": Decimal("4.99"),
            "storage_gb": 5,
            "max_users": 3,
            "priority_support": False,
            "api_access": True,
            "credit_rollover": True,
            "max_rollover_months": 1
        },
        {
            "name": "Growth Monthly",
            "plan_type": "growth",
            "billing_cycle": "monthly",
            "price_inr": Decimal("9999.00"),
            "credits_per_month": 2500,
            "effective_rate": Decimal("4.00"),
            "storage_gb": 25,
            "max_users": 10,
            "priority_support": True,
            "api_access": True,
            "credit_rollover": True,
            "max_rollover_months": 2
        },
        {
            "name": "Scale Monthly",
            "plan_type": "scale",
            "billing_cycle": "monthly",
            "price_inr": Decimal("24999.00"),
            "credits_per_month": 7500,
            "effective_rate": Decimal("3.33"),
            "storage_gb": 100,
            "max_users": None, # Unlimited
            "priority_support": True,
            "api_access": True,
            "credit_rollover": True,
            "max_rollover_months": 3
        },
        # ANNUAL PLANS
        {
            "name": "Starter Annual",
            "plan_type": "starter",
            "billing_cycle": "annual",
            "price_inr": Decimal("24990.00"),
            "credits_per_month": 500, 
            "effective_rate": Decimal("4.16"), 
            "storage_gb": 5,
            "max_users": 3,
            "priority_support": False,
            "api_access": True,
            "credit_rollover": True,
            "max_rollover_months": 2
        },
        {
            "name": "Growth Annual",
            "plan_type": "growth",
            "billing_cycle": "annual",
            "price_inr": Decimal("99990.00"),
            "credits_per_month": 2500,
            "effective_rate": Decimal("3.33"),
            "storage_gb": 25,
            "max_users": 10,
            "priority_support": True,
            "api_access": True,
            "credit_rollover": True,
            "max_rollover_months": 3
        },
        {
            "name": "Scale Annual",
            "plan_type": "scale",
            "billing_cycle": "annual",
            "price_inr": Decimal("249990.00"),
            "credits_per_month": 7500,
            "effective_rate": Decimal("2.78"),
            "storage_gb": 100,
            "max_users": None, # Unlimited
            "priority_support": True,
            "api_access": True,
            "credit_rollover": True,
            "max_rollover_months": 6
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
        (100, "599.00", "5.99", "100 Credits"),
        (500, "2499.00", "4.99", "500 Credits"),
        (1500, "6749.00", "4.50", "1,500 Credits"),
        (5000, "19995.00", "4.00", "5,000 Credits"),
        (15000, "52500.00", "3.50", "15,000 Credits"),
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
