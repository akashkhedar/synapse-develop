# Generated manually to fix existing member roles

from django.db import migrations


def fix_organization_creator_roles(apps, schema_editor):
    """
    Set the role to 'owner' for organization creators.
    The creator is identified by matching organization.created_by with member.user.
    """
    Organization = apps.get_model('organizations', 'Organization')
    OrganizationMember = apps.get_model('organizations', 'OrganizationMember')
    
    for org in Organization.objects.all():
        if org.created_by_id:
            # Find the membership for the creator and set role to owner
            OrganizationMember.objects.filter(
                organization=org,
                user_id=org.created_by_id,
                deleted_at__isnull=True
            ).update(role='owner')


def reverse_fix(apps, schema_editor):
    """Reverse: set all roles back to member (not recommended)."""
    pass  # No reverse needed


class Migration(migrations.Migration):

    dependencies = [
        ("organizations", "0009_add_api_key_field"),
    ]

    operations = [
        migrations.RunPython(fix_organization_creator_roles, reverse_fix),
    ]
