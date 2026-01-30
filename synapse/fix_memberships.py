
import os
import django
from django.utils import timezone

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.synapse')
django.setup()

from users.models import User
from organizations.models import Organization, OrganizationMember

print("Fixing Organization Memberships...")
print("=" * 60)

# Get or create the main organization
org, created = Organization.objects.get_or_create(
    title="Synapse Demo Org"
)
if created:
    print(f"Created new organization: {org.title}")
else:
    print(f"Using existing organization: {org.title}")

# Target users
target_emails = [
    "client@gmail.com",
    "annotator1@gmail.com",
    "annotator2@gmail.com",
    "expert@gmail.com"
]

for email in target_emails:
    try:
        user = User.objects.get(email=email)
        
        # Check membership
        if not OrganizationMember.objects.filter(user=user, organization=org).exists():
            # Determine role
            if user.is_client:
                role = OrganizationMember.ROLE_OWNER
            elif user.is_expert:
                role = OrganizationMember.ROLE_ADMIN
            else:
                role = OrganizationMember.ROLE_MEMBER
                
            OrganizationMember.objects.create(
                user=user,
                organization=org,
                role=role
            )
            print(f"  - Added {email} to organization as {role}")
        else:
            print(f"  - {email} is already a member")
            
        # Ensure active_organization is set
        if hasattr(user, 'active_organization') and not user.active_organization:
            user.active_organization = org
            user.save()
            print(f"  - Set active_organization for {email}")

    except User.DoesNotExist:
        print(f"  ! User {email} not found (skipped)")

print("=" * 60)
print("Fix Complete.")
