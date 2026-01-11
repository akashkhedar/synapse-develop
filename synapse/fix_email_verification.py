# Check and fix email verification
from users.models import User

email = 'azgmxrk@kemail.uk'
print(f"\nChecking email verification for: {email}\n")

user = User.objects.get(email=email)

# Check all verification-related fields
print(f"User fields:")
print(f"  email: {user.email}")
print(f"  is_active: {user.is_active}")

# Check if there's an email_verified field on User
if hasattr(user, 'email_verified'):
    print(f"  email_verified: {user.email_verified}")
    if not user.email_verified:
        user.email_verified = True
        user.save()
        print(f"  → Set email_verified = True")

# Check for EmailVerificationToken
try:
    from users.models import EmailVerificationToken
    tokens = EmailVerificationToken.objects.filter(user=user)
    print(f"\nEmailVerificationToken:")
    if tokens.exists():
        for token in tokens:
            print(f"  Token: {token.token[:20]}...")
            print(f"  Is verified: {token.is_verified}")
            if not token.is_verified:
                token.is_verified = True
                token.save()
                print(f"  → Set is_verified = True")
    else:
        print(f"  No tokens found")
except ImportError:
    print(f"\nNo EmailVerificationToken model")

# Check annotator profile
from annotators.models import AnnotatorProfile
profile = AnnotatorProfile.objects.get(user=user)
print(f"\nAnnotatorProfile:")
print(f"  email_verified: {profile.email_verified}")
print(f"  status: {profile.status}")

if not profile.email_verified:
    profile.email_verified = True
    profile.save()
    print(f"  → Set email_verified = True")

print(f"\n✓ Email verification status updated\n")
