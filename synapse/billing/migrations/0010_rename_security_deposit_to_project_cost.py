# Generated migration for renaming security deposit to project cost
# and adding variable security fees

from django.db import migrations, models


def migrate_security_deposit_to_project_cost(apps, schema_editor):
    """Copy existing security deposit data to new project cost fields"""
    ProjectBilling = apps.get_model('billing', 'ProjectBilling')
    
    for billing in ProjectBilling.objects.all():
        billing.project_cost_required = billing.security_deposit_required
        billing.project_cost_paid = billing.security_deposit_paid
        billing.project_cost_refunded = billing.security_deposit_refunded
        billing.save(update_fields=[
            'project_cost_required',
            'project_cost_paid', 
            'project_cost_refunded'
        ])


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0003_storage_subscription_fields'),  # Latest migration
    ]

    operations = [
        # Add new project cost fields to ProjectBilling
        migrations.AddField(
            model_name='projectbilling',
            name='project_cost_required',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text='Project cost required (security fees + estimated costs)',
                max_digits=15
            ),
        ),
        migrations.AddField(
            model_name='projectbilling',
            name='project_cost_paid',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text='Project cost actually paid',
                max_digits=15
            ),
        ),
        migrations.AddField(
            model_name='projectbilling',
            name='project_cost_refunded',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text='Project cost refunded',
                max_digits=15
            ),
        ),
        
        # Update help text for old security_deposit fields (mark as deprecated)
        migrations.AlterField(
            model_name='projectbilling',
            name='security_deposit_required',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text='(Deprecated: use project_cost_required)',
                max_digits=15
            ),
        ),
        migrations.AlterField(
            model_name='projectbilling',
            name='security_deposit_paid',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text='(Deprecated: use project_cost_paid)',
                max_digits=15
            ),
        ),
        migrations.AlterField(
            model_name='projectbilling',
            name='security_deposit_refunded',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text='(Deprecated: use project_cost_refunded)',
                max_digits=15
            ),
        ),
        
        # Add security_fee field to SecurityDeposit model
        migrations.AddField(
            model_name='securitydeposit',
            name='security_fee',
            field=models.DecimalField(
                decimal_places=2,
                default=500,
                help_text='Security fee based on project size: 500/700/900/1100/1300/1500',
                max_digits=10
            ),
        ),
        
        # Update help text for base_fee (mark as deprecated)
        migrations.AlterField(
            model_name='securitydeposit',
            name='base_fee',
            field=models.DecimalField(
                decimal_places=2,
                default=500,
                help_text='(Deprecated: use security_fee)',
                max_digits=10
            ),
        ),
        
        # Data migration: Copy existing security_deposit values to project_cost fields
        migrations.RunPython(
            code=migrate_security_deposit_to_project_cost,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
