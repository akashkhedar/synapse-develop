import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.synapse')
django.setup()

from billing.models import SubscriptionPlan

# Deactivate the Enterprise plan (it should be Contact Us, not a real plan)
enterprise = SubscriptionPlan.objects.filter(name='Enterprise', is_active=True)
if enterprise.exists():
    enterprise.update(is_active=False)
    print("✅ Deactivated Enterprise plan")

# Verify monthly plans
print("\n" + "="*70)
print("CURRENTLY ACTIVE MONTHLY SUBSCRIPTION PLANS:")
print("="*70)
monthly_plans = SubscriptionPlan.objects.filter(
    is_active=True, 
    billing_cycle='monthly'
).order_by('price_inr')

for plan in monthly_plans:
    print(f"{plan.name:30} | ₹{plan.price_inr:>10,.0f}/month | {plan.credits_per_month:>8,} credits")

print("\n" + "="*70)
print("CURRENTLY ACTIVE ANNUAL SUBSCRIPTION PLANS:")
print("="*70)
annual_plans = SubscriptionPlan.objects.filter(
    is_active=True, 
    billing_cycle='annual'
).order_by('price_inr')

for plan in annual_plans:
    print(f"{plan.name:30} | ₹{plan.price_inr:>10,.0f}/year | {plan.credits_per_month:>8,} credits/month")
