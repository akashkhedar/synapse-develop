
import sys
from users.models import User
from projects.models import Project, ProjectMember

email = "born200three@gmail.com"
project_id = 549

print(f"Enabling ProjectMember for {email} in Project {project_id}")

try:
    user = User.objects.get(email=email)
    project = Project.objects.get(id=project_id)
    
    pm = ProjectMember.objects.get(user=user, project=project)
    print(f"Found ProjectMember ID: {pm.id}")
    
    if hasattr(pm, 'enabled'):
        print(f"Current enabled status: {pm.enabled}")
        if not pm.enabled:
            pm.enabled = True
            pm.save()
            print("Set enabled = True")
        else:
            print("Already enabled.")
    else:
        print("Model does not have 'enabled' field via hasattr check, but API uses it?")
        # Force set it if it's dynamic or just print dictionary
        pass

except ProjectMember.DoesNotExist:
    print("ProjectMember DOES NOT EXIST")
except Exception as e:
    print(f"Error: {e}")
