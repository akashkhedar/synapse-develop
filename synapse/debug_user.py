
from users.models import User
from annotators.models import AnnotatorProfile

email = "born200three@gmail.com"
print(f"Checking for user: {email}")

try:
    user = User.objects.get(email=email)
    print(f"User found: ID={user.pk} - Email={user.email}")
    try:
        profile = user.annotator_profile
        print(f"Profile found: Status={profile.status}")
    except AnnotatorProfile.DoesNotExist:
        print("No AnnotatorProfile found for this user.")
except User.DoesNotExist:
    print("User does not exist.")
    print("\nRecent users:")
    for u in User.objects.order_by('-date_joined')[:10]:
        print(f"- {u.email} (ID: {u.pk}, Joined: {u.date_joined})")
