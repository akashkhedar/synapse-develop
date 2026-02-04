import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.synapse')
django.setup()

from billing.models import SubscriptionPlan, CreditPackage

# Deactivate old monthly plans (without "Monthly" in the name)
old_monthly_plans = SubscriptionPlan.objects.filter(
    plan_type__in=['starter', 'growth', 'scale'],
    billing_cycle='monthly',
    is_active=True
).exclude(name__icontains='Monthly')

print("Deactivating old monthly plans:")
for plan in old_monthly_plans:
    print(f"  - {plan.name}: ₹{plan.price_inr} ({plan.credits_per_month} credits)")
    plan.is_active = False
    plan.save()

print(f"\n✅ Deactivated {old_monthly_plans.count()} old monthly plans")

# Deactivate old PAYG packages
old_payg_names = ['Starter Pack', 'Basic Pack', 'Pro Pack', 'Enterprise Pack']
old_payg = CreditPackage.objects.filter(name__in=old_payg_names, is_active=True)

print("\nDeactivating old PAYG packages:")
for pkg in old_payg:
    print(f"  - {pkg.name}: ₹{pkg.price_inr} ({pkg.credits} credits)")
    pkg.is_active = False
    pkg.save()

print(f"\n✅ Deactivated {old_payg.count()} old PAYG packages")

# Show currently active plans
print("\n" + "="*60)
print("CURRENTLY ACTIVE SUBSCRIPTION PLANS:")
print("="*60)
active_plans = SubscriptionPlan.objects.filter(is_active=True).order_by('billing_cycle', 'price_inr')
for plan in active_plans:
    print(f"{plan.name}: ₹{plan.price_inr:,.0f} - {plan.credits_per_month:,} credits/month")

print("\n" + "="*60)
print("CURRENTLY ACTIVE PAYG PACKAGES:")
print("="*60)
active_packages = CreditPackage.objects.filter(is_active=True).order_by('credits')
for pkg in active_packages:
    print(f"{pkg.name}: ₹{pkg.price_inr:,.0f} - {pkg.credits:,} credits")

print("\n✅ All done! Old plans deactivated, new plans active.")
