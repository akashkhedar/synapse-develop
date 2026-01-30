
import sys
from users.models import User
from projects.models import Project, ProjectMember

email = "born200three@gmail.com"
project_id = 549

print(f"Checking ProjectMember status for {email} in Project {project_id}")

try:
    user = User.objects.get(email=email)
    project = Project.objects.get(id=project_id)
    
    is_member = ProjectMember.objects.filter(user=user, project=project).exists()
    print(f"Is ProjectMember: {is_member}")
    
    if not is_member:
        print("Creating ProjectMember...")
        ProjectMember.objects.create(user=user, project=project)
        print("ProjectMember created.")
    else:
        print("User is already a ProjectMember.")

except Exception as e:
    print(f"Error: {e}")
