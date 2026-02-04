import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.synapse')
django.setup()

from billing.models import SubscriptionPlan, CreditPackage

print("="*70)
print("ALL SUBSCRIPTION PLANS (ACTIVE AND INACTIVE):")
print("="*70)
all_plans = SubscriptionPlan.objects.all().order_by('billing_cycle', 'price_inr')
for plan in all_plans:
    status = "✓ ACTIVE" if plan.is_active else "✗ INACTIVE"
    print(f"{status:12} | {plan.name:30} | ₹{plan.price_inr:>10,.0f} | {plan.credits_per_month:>8,} credits")

print("\n" + "="*70)
print("ALL PAYG PACKAGES (ACTIVE AND INACTIVE):")
print("="*70)
all_packages = CreditPackage.objects.all().order_by('credits')
for pkg in all_packages:
    status = "✓ ACTIVE" if pkg.is_active else "✗ INACTIVE"
    print(f"{status:12} | {pkg.name:30} | ₹{pkg.price_inr:>10,.0f} | {pkg.credits:>8,} credits")

# Now deactivate the specific old plans
print("\n" + "="*70)
print("DEACTIVATING OLD PLANS...")
print("="*70)

# Target the old plans by exact price
old_starter = SubscriptionPlan.objects.filter(price_inr=2499, billing_cycle='monthly', is_active=True)
old_growth = SubscriptionPlan.objects.filter(price_inr=9999, billing_cycle='monthly', is_active=True)
old_scale = SubscriptionPlan.objects.filter(price_inr=24999, billing_cycle='monthly', is_active=True)

for plan in old_starter:
    print(f"Deactivating: {plan.name}")
    plan.is_active = False
    plan.save()

for plan in old_growth:
    print(f"Deactivating: {plan.name}")
    plan.is_active = False
    plan.save()

for plan in old_scale:
    print(f"Deactivating: {plan.name}")
    plan.is_active = False
    plan.save()

# Deactivate old PAYG by price
old_payg_prices = [599, 2499, 6749, 52500]
for price in old_payg_prices:
    old_pkg = CreditPackage.objects.filter(price_inr=price, is_active=True)
    for pkg in old_pkg:
        print(f"Deactivating: {pkg.name}")
        pkg.is_active = False
        pkg.save()

print("\n✅ Done!")
