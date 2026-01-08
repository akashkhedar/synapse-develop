"""
Management command to initialize default subscription plans and credit packages
"""
from django.core.management.base import BaseCommand
from billing.models import SubscriptionPlan, CreditPackage


class Command(BaseCommand):
    help = 'Initialize default subscription plans and credit packages'
    
    def handle(self, *args, **options):
        self.stdout.write('Creating subscription plans...')
        
        # Monthly plans
        monthly_plans = [
            {
                'name': 'Starter - Monthly',
                'plan_type': 'starter',
                'billing_cycle': 'monthly',
                'price_inr': 5000,
                'credits_per_month': 5000,
                'effective_rate': 1.00,
                'storage_gb': 10,
                'max_users': 5,
                'priority_support': False,
                'credit_rollover': True,
            },
            {
                'name': 'Growth - Monthly',
                'plan_type': 'growth',
                'billing_cycle': 'monthly',
                'price_inr': 20000,
                'credits_per_month': 25000,
                'effective_rate': 0.80,
                'storage_gb': 50,
                'max_users': 20,
                'priority_support': True,
                'credit_rollover': True,
            },
            {
                'name': 'Scale - Monthly',
                'plan_type': 'scale',
                'billing_cycle': 'monthly',
                'price_inr': 50000,
                'credits_per_month': 75000,
                'effective_rate': 0.67,
                'storage_gb': 200,
                'max_users': None,
                'priority_support': True,
                'credit_rollover': True,
            },
        ]
        
        # Annual plans (2-3 months free)
        annual_plans = [
            {
                'name': 'Starter - Annual',
                'plan_type': 'starter',
                'billing_cycle': 'annual',
                'price_inr': 50000,  # 10 months price
                'credits_per_month': 5000,
                'effective_rate': 0.83,
                'storage_gb': 10,
                'max_users': 5,
                'priority_support': False,
                'credit_rollover': True,
            },
            {
                'name': 'Growth - Annual',
                'plan_type': 'growth',
                'billing_cycle': 'annual',
                'price_inr': 200000,  # 10 months price
                'credits_per_month': 25000,
                'effective_rate': 0.67,
                'storage_gb': 50,
                'max_users': 20,
                'priority_support': True,
                'credit_rollover': True,
            },
            {
                'name': 'Scale - Annual',
                'plan_type': 'scale',
                'billing_cycle': 'annual',
                'price_inr': 500000,  # 10 months price (bonus: 3 months free)
                'credits_per_month': 75000,
                'effective_rate': 0.56,
                'storage_gb': 200,
                'max_users': None,
                'priority_support': True,
                'credit_rollover': True,
            },
        ]
        
        all_plans = monthly_plans + annual_plans
        
        for plan_data in all_plans:
            plan, created = SubscriptionPlan.objects.update_or_create(
                name=plan_data['name'],
                defaults=plan_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Created: {plan.name}'))
            else:
                self.stdout.write(f'  Updated: {plan.name}')
        
        self.stdout.write('\nCreating credit packages (PAYG)...')
        
        credit_packages = [
            {
                'name': '1,000 Credits Package',
                'credits': 1000,
                'price_inr': 1500,
                'rate_per_credit': 1.50,
            },
            {
                'name': '5,000 Credits Package',
                'credits': 5000,
                'price_inr': 6750,
                'rate_per_credit': 1.35,
            },
            {
                'name': '10,000 Credits Package',
                'credits': 10000,
                'price_inr': 12000,
                'rate_per_credit': 1.20,
            },
        ]
        
        for package_data in credit_packages:
            package, created = CreditPackage.objects.update_or_create(
                name=package_data['name'],
                defaults=package_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Created: {package.name}'))
            else:
                self.stdout.write(f'  Updated: {package.name}')
        
        self.stdout.write(self.style.SUCCESS('\n✅ Successfully initialized billing plans and packages'))





