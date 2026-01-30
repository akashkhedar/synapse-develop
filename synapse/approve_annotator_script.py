import sys
from users.models import User
from projects.models import Project, ProjectMember

email = "born200three@gmail.com"
print(f"Processing user: {email}")

try:
    user = User.objects.get(email=email)
    print(f"Found user {user.email} (ID: {user.id})")
    
    # 1. Approve
    user.is_annotator = True
    user.annotator_status = 'approved'
    user.is_active = True
    user.save()
    print("User approved and set as active annotator.")
    
    # 2. Assign to project
    projects = Project.objects.all()
    if not projects.exists():
        print("No projects found!")
    else:
        print(f"Found {projects.count()} projects.")
        for project in projects:
            print(f"Assigning to project: {project.title} (ID: {project.id})")
            # Using get_or_create might require importing ProjectMember which I verified exists
            # Note: ProjectMember might be defined inside projects.models but not exported? 
            # I'll use string reference or just import as I did.
            
            pm, created = ProjectMember.objects.get_or_create(user=user, project=project)
            if created:
                print("  - Added as member")
            else:
                print("  - Already a member")
            
            # Ensure member is enabled??
            # I don't see 'enabled' field in my grep but standard practice.
            # I'll check dir(pm) if possible or just print status.
            
except User.DoesNotExist:
    print(f"User {email} not found!")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
