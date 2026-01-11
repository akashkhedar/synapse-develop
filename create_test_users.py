"""
Create test users with different roles for Synapse
Run: python manage.py shell < create_test_users.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.label_studio')
django.setup()

from django.utils import timezone
from users.models import User

# Password for all users
PASSWORD = "itsAKASH@26"

# User configurations
users_config = [
    {
        "email": "client@gmail.com",
        "username": "Client User",
        "is_client": True,
        "is_annotator": False,
        "is_expert": False,
    },
    {
        "email": "annotator1@gmail.com",
        "username": "Annotator One",
        "is_client": False,
        "is_annotator": True,
        "is_expert": False,
    },
    {
        "email": "annotator2@gmail.com",
        "username": "Annotator Two",
        "is_client": False,
        "is_annotator": True,
        "is_expert": False,
    },
    {
        "email": "expert@gmail.com",
        "username": "Expert User",
        "is_client": False,
        "is_annotator": False,
        "is_expert": True,
    },
]

print("Creating test users...")
print("=" * 60)

for config in users_config:
    email = config["email"]
    
    # Check if user already exists
    if User.objects.filter(email=email).exists():
        user = User.objects.get(email=email)
        print(f"✓ User {email} already exists, updating...")
    else:
        # Create new user
        user = User.objects.create_user(
            email=email,
            password=PASSWORD,
            username=config["username"],
        )
        print(f"✓ Created user: {email}")
    
    # Set roles
    user.is_client = config["is_client"]
    user.is_annotator = config["is_annotator"]
    user.is_expert = config["is_expert"]
    
    # Verify email and activate
    user.email_verified = True
    user.email_verified_at = timezone.now()
    user.is_active = True
    
    # Set annotator status to approved if annotator or expert
    if config["is_annotator"] or config["is_expert"]:
        user.annotator_status = "approved"
    
    user.save()
    
    print(f"  - Role: {'Client' if config['is_client'] else 'Annotator' if config['is_annotator'] else 'Expert'}")
    print(f"  - Email Verified: ✓")
    print(f"  - Status: Active")
    if config["is_annotator"] or config["is_expert"]:
        print(f"  - Annotator Status: Approved")
    print()

print("=" * 60)
print("All users created successfully!")
print(f"Password for all users: {PASSWORD}")
print("\nYou can now login with:")
for config in users_config:
    role = "Client" if config["is_client"] else "Annotator" if config["is_annotator"] else "Expert"
    print(f"  - {config['email']} ({role})")
