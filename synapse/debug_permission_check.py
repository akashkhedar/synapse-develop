
import sys
from users.models import User
from projects.models import Project
from annotators.models import TaskAssignment

email = "born200three@gmail.com"
project_id = 549

print(f"Debug: Permission Check for {email} on P{project_id}")

try:
    user = User.objects.get(email=email)
    project = Project.objects.get(id=project_id)
    
    print(f"User ID: {user.id}")
    print(f"Is Authenticated: {user.is_authenticated}")
    print(f"Is Annotator: {user.is_annotator}")
    print(f"Is Superuser: {user.is_superuser}")
    
    # Simulate has_permission logic
    print("\n--- Simulating has_permission ---")
    
    if user.is_superuser:
        print("Result: True (Superuser)")
    
    elif hasattr(user, "is_expert") and user.is_expert:
        print("Checking Expert...")
        # (Expert check logic omitted for brevity as user is annotator)
    
    elif hasattr(user, "is_annotator") and user.is_annotator:
        print("Checking Annotator...")
        try:
             # Check if user has any active task assignments in this project
            has_tasks = TaskAssignment.objects.filter(
                annotator__user=user,
                task__project=project,
                status__in=["assigned", "in_progress"]
            ).exists()
            print(f"Has Tasks: {has_tasks}")
            if has_tasks:
                print("Result: True (Annotator with tasks)")
            else:
                print("Result: False (Annotator without tasks)")
        except Exception as e:
            print(f"Exception in Annotator check: {e}")
            
    else:
        print("Checking Organization...")
        if hasattr(project, "organization") and project.organization:
             has_org = project.organization.has_user(user)
             print(f"Has Org User: {has_org}")
        else:
             print("Result: True (No Org)")

    # Actual Method Call
    print("\n--- Actual Method Call ---")
    try:
        permission = project.has_permission(user)
        print(f"project.has_permission(user) returned: {permission}")
    except Exception as e:
        print(f"project.has_permission(user) RAISED: {e}")
        import traceback
        traceback.print_exc()

except Exception as e:
    print(f"Setup Error: {e}")
