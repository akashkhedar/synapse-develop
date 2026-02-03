
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.synapse')
django.setup()

from users.models import User

# Users to remove
users_to_remove = [
    "annotator1@gmail.com",
    "annotator2@gmail.com",
    "client@gmail.com"
]

print("Removing users...")
print("=" * 60)

for email in users_to_remove:
    try:
        user = User.objects.get(email=email)
        user.delete()
        print(f"✓ Deleted: {email}")
    except User.DoesNotExist:
        print(f"✗ Not found: {email}")

print("=" * 60)
print("Removal Complete.")
