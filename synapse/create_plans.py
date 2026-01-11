#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.synapse')
django.setup()

from billing.models import SubscriptionPlan

plans = [
    {'name': 'Starter Monthly', 'plan_type': 'starter', 'billing_cycle': 'monthly', 'price_inr': 499, 'credits_per_month': 100, 'effective_rate': 4.99, 'storage_gb': 5, 'max_users': 1, 'priority_support': False},
    {'name': 'Starter Annual', 'plan_type': 'starter', 'billing_cycle': 'annual', 'price_inr': 4990, 'credits_per_month': 100, 'effective_rate': 4.16, 'storage_gb': 5, 'max_users': 1, 'priority_support': False},
    {'name': 'Growth Monthly', 'plan_type': 'growth', 'billing_cycle': 'monthly', 'price_inr': 1999, 'credits_per_month': 500, 'effective_rate': 4.00, 'storage_gb': 25, 'max_users': 5, 'priority_support': False},
    {'name': 'Growth Annual', 'plan_type': 'growth', 'billing_cycle': 'annual', 'price_inr': 19990, 'credits_per_month': 500, 'effective_rate': 3.33, 'storage_gb': 25, 'max_users': 5, 'priority_support': False},
    {'name': 'Scale Monthly', 'plan_type': 'scale', 'billing_cycle': 'monthly', 'price_inr': 4999, 'credits_per_month': 1500, 'effective_rate': 3.33, 'storage_gb': 100, 'max_users': 15, 'priority_support': True},
    {'name': 'Scale Annual', 'plan_type': 'scale', 'billing_cycle': 'annual', 'price_inr': 49990, 'credits_per_month': 1500, 'effective_rate': 2.78, 'storage_gb': 100, 'max_users': 15, 'priority_support': True},
    {'name': 'Enterprise Monthly', 'plan_type': 'enterprise', 'billing_cycle': 'monthly', 'price_inr': 14999, 'credits_per_month': 5000, 'effective_rate': 3.00, 'storage_gb': 500, 'max_users': None, 'priority_support': True},
    {'name': 'Enterprise Annual', 'plan_type': 'enterprise', 'billing_cycle': 'annual', 'price_inr': 149990, 'credits_per_month': 5000, 'effective_rate': 2.50, 'storage_gb': 500, 'max_users': None, 'priority_support': True},
]

for p in plans:
    obj, created = SubscriptionPlan.objects.get_or_create(
        plan_type=p['plan_type'],
        billing_cycle=p['billing_cycle'],
        defaults=p
    )
    status = 'Created' if created else 'Exists'
    print(f"{status}: {obj.name}")

print('Done!')
