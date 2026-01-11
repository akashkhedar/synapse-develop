# Check user and annotator profile
from users.models import User
from annotators.models import AnnotatorProfile

email = 'azgmxrk@kemail.uk'
print(f"\n{'='*60}")
print(f"Checking: {email}")
print('='*60)

# Check if user exists
user = User.objects.filter(email=email).first()
if user:
    print(f"\n✓ User exists:")
    print(f"  ID: {user.id}")
    print(f"  Email: {user.email}")
    print(f"  Username: {user.username}")
    print(f"  Is active: {user.is_active}")
    print(f"  Date joined: {user.date_joined}")
else:
    print(f"\n✗ User does NOT exist")
    print("='*60 + '\n'")
    exit()

# Check if annotator profile exists
profile = AnnotatorProfile.objects.filter(user=user).first()
if profile:
    print(f"\n✓ AnnotatorProfile exists:")
    print(f"  ID: {profile.id}")
    print(f"  Status: {profile.status}")
    print(f"  Email verified: {profile.email_verified}")
    print(f"  Applied at: {profile.applied_at}")
else:
    print(f"\n✗ AnnotatorProfile does NOT exist")
    print(f"  → This is the problem! User exists but no annotator profile.")

print('\n' + '='*60 + '\n')
