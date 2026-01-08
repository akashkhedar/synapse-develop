# Generated migration for adding role field to OrganizationMember
from django.db import migrations, models


def set_owner_roles(apps, schema_editor):
    """Set role='owner' for organization creators"""
    OrganizationMember = apps.get_model('organizations', 'OrganizationMember')
    Organization = apps.get_model('organizations', 'Organization')
    
    for org in Organization.objects.all():
        if org.created_by:
            # Set the creator as owner
            OrganizationMember.objects.filter(
                organization=org,
                user=org.created_by,
                deleted_at__isnull=True
            ).update(role='owner')
    
    # All other existing members remain as 'member' (default)


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0007_change_created_by_to_foreignkey'),
    ]

    operations = [
        migrations.AddField(
            model_name='organizationmember',
            name='role',
            field=models.CharField(
                choices=[('owner', 'Owner'), ('admin', 'Admin'), ('member', 'Member')],
                db_index=True,
                default='member',
                help_text='Role of the member in the organization. Owner is the creator, Admin can manage members, Member is regular user.',
                max_length=10,
                verbose_name='role',
            ),
        ),
        migrations.RunPython(set_owner_roles, reverse_code=migrations.RunPython.noop),
    ]





