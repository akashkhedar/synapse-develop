
import sys
from users.models import User
from annotators.models import AnnotatorProfile, TaskAssignment

email = "born200three@gmail.com"
print(f"Verifying user: {email}")

try:
    user = User.objects.get(email=email)
    profile = user.annotator_profile
    print(f"Profile Status: {profile.status}")
    
    cnt = TaskAssignment.objects.filter(annotator=profile).count()
    print(f"Total Task Assignments: {cnt}")
    
    if cnt > 0:
        print("SUCCESS: User has assignments.")
    else:
        print("FAILURE: User has NO assignments.")

except Exception as e:
    print(f"Error: {e}")
