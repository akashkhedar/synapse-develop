# Fix user annotator fields
from users.models import User

email = 'azgmxrk@kemail.uk'
print(f"\nFixing user fields for: {email}\n")

user = User.objects.get(email=email)

print(f"Current user fields:")
print(f"  is_annotator: {user.is_annotator}")
print(f"  annotator_status: {user.annotator_status}")
print(f"  email_verified: {user.email_verified}")
print(f"  is_active: {user.is_active}")

# Set annotator fields
if not user.is_annotator:
    user.is_annotator = True
    print(f"\n  → Set is_annotator = True")

if user.annotator_status != 'approved':
    user.annotator_status = 'approved'
    print(f"  → Set annotator_status = 'approved'")

user.save()

print(f"\n✓ User fields updated:")
print(f"  is_annotator: {user.is_annotator}")
print(f"  annotator_status: {user.annotator_status}")
print(f"\n✓ User can now login!\n")
