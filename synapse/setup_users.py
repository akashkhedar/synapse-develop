
import os
import django
from django.utils import timezone

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.synapse')
django.setup()

from users.models import User
from annotators.models import AnnotatorProfile

# Password for all users
PASSWORD = "synapse123"

print("Cleaning up existing users...")
# Delete all users to simulate flush (since flush might have issues or fixtures)
# We exclude superusers if we want to keep admin, but prompt said "flush all"
# So we delete everything.
count = User.objects.all().count()
User.objects.all().delete()
print(f"Deleted {count} users.")

# User configurations
users_config = [
    {
        "email": "client@gmail.com",
        "username": "Client User",
        "is_client": True,
        "is_annotator": False,
        "is_expert": False,
        "role_name": "Client"
    },
    {
        "email": "annotator1@gmail.com",
        "username": "Annotator One",
        "is_client": False,
        "is_annotator": True,
        "is_expert": False,
        "experience": "intermediate",
        "role_name": "Annotator"
    },
    {
        "email": "annotator2@gmail.com",
        "username": "Annotator Two",
        "is_client": False,
        "is_annotator": True,
        "is_expert": False,
        "experience": "intermediate",
        "role_name": "Annotator"
    },
    {
        "email": "expert@gmail.com",
        "username": "Expert User",
        "is_client": False,
        "is_annotator": False,  # Experts might also be annotators
        "is_expert": True,
        "experience": "expert",
        "role_name": "Expert"
    },
]

print("Setting up users...")
print("=" * 60)

for config in users_config:
    email = config["email"]
    
    # Create user (we know they don't exist now)
    user = User.objects.create_user(
        email=email,
        password=PASSWORD,
        username=config["username"],
    )
    print(f"Created user: {email}")
    
    # Set User flags
    user.is_client = config["is_client"]
    user.is_annotator = config["is_annotator"]
    user.is_expert = config["is_expert"]
    user.email_verified = True
    user.email_verified_at = timezone.now()
    user.is_active = True
    
    # Compatibility with User model's annotator_status if it exists
    if hasattr(user, 'annotator_status') and (config["is_annotator"] or config["is_expert"]):
        user.annotator_status = "approved"
        
    user.save()

    # Create/Approve AnnotatorProfile for Annotators and Experts
    if config["is_annotator"] or config["is_expert"]:
        profile, created = AnnotatorProfile.objects.get_or_create(user=user)
        
        profile.status = "approved"
        profile.email_verified = True
        if not profile.approved_at:
            profile.approved_at = timezone.now()
        
        if "experience" in config:
            profile.experience_level = config["experience"]
            
        profile.save()
        print(f"  - Profile Approved: YES ({profile.experience_level})")

    print(f"  - Role: {config['role_name']}")
    print(f"  - Verified: YES")
    print()

print("=" * 60)
print("Setup Complete.")
