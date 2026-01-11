# Create annotator profile and approve
from django.utils import timezone
from users.models import User
from annotators.models import AnnotatorProfile

email = 'azgmxrk@kemail.uk'
print(f"\nCreating and approving annotator: {email}\n")

user = User.objects.get(email=email)

# Create annotator profile
profile, created = AnnotatorProfile.objects.get_or_create(
    user=user,
    defaults={
        'status': 'approved',
        'email_verified': True,
        'approved_at': timezone.now(),
    }
)

if created:
    print(f"✓ Created new AnnotatorProfile")
else:
    print(f"✓ AnnotatorProfile already exists, updating...")
    profile.status = 'approved'
    profile.email_verified = True
    profile.approved_at = timezone.now()
    profile.save()

# Ensure user is active
user.is_active = True
user.save()

print(f"✓ APPROVED: {user.email}")
print(f"  Status: {profile.status}")
print(f"  Email verified: {profile.email_verified}")
print(f"  User is_active: {user.is_active}")
print()
