from users.models import User
from projects.models import Project

email = "born200three@gmail.com"
print(f"Checking user: {email}")

try:
    user = User.objects.get(email=email)
    print(f"User found: {user.email}")
    print(f"  ID: {user.id}")
    print(f"  Is Annotator: {user.is_annotator}")
    print(f"  Annotator Status: {user.annotator_status}")
    print(f"  Active Org: {user.active_organization}")
except User.DoesNotExist:
    print("User NOT found")

print("\nAvailable Projects:")
projects = Project.objects.all()
for p in projects:
    print(f"  [{p.id}] {p.title} (Org: {p.organization_id})")
