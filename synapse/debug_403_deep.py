
import sys
import os
import django
from django.conf import settings

# Setup Django if run directly (though we will use manage.py shell)
if __name__ == "__main__":
    pass

from users.models import User
from projects.models import Project, ProjectMember
from annotators.models import TaskAssignment

email = "born200three@gmail.com"
project_id = 549

print(f"\n=== DEEP DEBUG 403 Project {project_id} | User {email} ===\n")

try:
    user = User.objects.get(email=email)
    project = Project.objects.get(id=project_id)
    
    print(f"[User] ID: {user.id} | active: {user.is_active} | annotator: {user.is_annotator}")
    print(f"[User] Active Org: {user.active_organization}")
    
    print(f"[Project] ID: {project.id} | Org: {project.organization}")
    
    # 1. Check ProjectMember
    print("\n[Check 1: ProjectMember]")
    members = ProjectMember.objects.filter(user=user, project=project)
    if members.exists():
        pm = members.first()
        print(f"  ProjectMember FOUND. ID: {pm.id}")
        # Check for 'enabled' field if it exists
        if hasattr(pm, 'enabled'):
            print(f"  Field 'enabled': {pm.enabled}")
        else:
            print("  Field 'enabled': <Not Present on Model>")
            
        # Check other fields
        print(f"  Field dump: {pm.__dict__}")
    else:
        print("  ProjectMember NOT FOUND!")

    # 2. Check QuerySet Logic (Annotator path)
    print("\n[Check 2: API QuerySet Logic]")
    print("  Replicating: Project.objects.filter(members__user=user, members__enabled=True)")
    
    try:
        # Try exact filter from API
        qs = Project.objects.filter(members__user=user, members__enabled=True)
        found = qs.filter(id=project_id).exists()
        print(f"  QuerySet Match (members__enabled=True): {found}")
        
        if not found:
            # Try without enabled
            qs2 = Project.objects.filter(members__user=user)
            found2 = qs2.filter(id=project_id).exists()
            print(f"  QuerySet Match (members only): {found2}")
            
    except Exception as e:
        print(f"  QuerySet Filter Error: {e}")

    # 3. Check Permissions
    print("\n[Check 3: User Permissions]")
    # requires 'projects.view'
    perm = 'projects.view'
    has_perm = user.has_perm(perm)
    print(f"  user.has_perm('{perm}'): {has_perm}")
    
    # Check permissions backend/rules if possible
    # (Checking if user is authenticated is usually enough for 'rules' default shown earlier)
    
    # 4. Check active_organization mismatch logic
    print("\n[Check 4: Organization Context]")
    if user.active_organization != project.organization:
        print(f"  MISMATCH: User Org ({user.active_organization}) != Project Org ({project.organization})")
        print("  (Note: Annotator API path shouldn't care, but good to know)")
    else:
        print("  Organization Match: OK")

except Exception as e:
    print(f"\nCRITICAL ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n=== DEBUG END ===")
