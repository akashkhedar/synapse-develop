
from users.models import User
from annotators.models import AnnotatorProfile
from django.utils import timezone

email = "born200three@gmail.com"
print(f"Processing user: {email}")

try:
    user = User.objects.get(email=email)
    
    profile, created = AnnotatorProfile.objects.get_or_create(user=user)
    
    if created:
        print("Created new AnnotatorProfile.")
    else:
        print("Found existing AnnotatorProfile.")
        
    # Approve
    profile.status = "approved"
    if not profile.approved_at:
        profile.approved_at = timezone.now()
    profile.email_verified = True # Ensure email is verified too
    profile.save()
    
    print(f"Successfully approved annotator: {email}")
    print(f"Status: {profile.status}")
    print(f"Approved At: {profile.approved_at}")

except User.DoesNotExist:
    print(f"User {email} not found!")
except Exception as e:
    print(f"Error: {e}")
