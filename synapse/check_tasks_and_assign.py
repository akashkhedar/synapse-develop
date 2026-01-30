
import sys
import random
from users.models import User
from projects.models import Project
from tasks.models import Task
from annotators.models import AnnotatorProfile, TaskAssignment, ProjectAssignment

email = "born200three@gmail.com"
target_project_id = 549
print(f"Processing user: {email} for Project {target_project_id}")

try:
    user = User.objects.get(email=email)
    print(f"Found user {user.email}")

    # Ensure AnnotatorProfile exists
    profile, created = AnnotatorProfile.objects.get_or_create(user=user)
    if created:
        print("Created AnnotatorProfile")
        profile.status = 'approved'
        profile.save()
    else:
        if profile.status != 'approved':
             profile.status = 'approved'
             profile.save()
             print("Updated profile status to approved")

    # Target specific project
    try:
        project = Project.objects.get(id=target_project_id)
        print(f"\nChecking Project: {project.title} (ID: {project.id})")
        
        tasks = Task.objects.filter(project=project)
        count = tasks.count()
        print(f"  Total Tasks: {count}")
        
        if count > 0:
            # Check existing assignments
            existing_assignments = TaskAssignment.objects.filter(annotator=profile, task__project=project)
            print(f"  Existing Assignments: {existing_assignments.count()}")
            
            if existing_assignments.count() == 0:
                # Assign 5 random tasks
                tasks_to_assign = tasks.order_by('?')[:5]
                print(f"  Assigning {len(tasks_to_assign)} tasks...")
                
                for task in tasks_to_assign:
                    TaskAssignment.objects.create(
                        annotator=profile,
                        task=task,
                        status='assigned'
                    )
                print("  Tasks assigned successfully.")
                
                # Also create ProjectAssignment if missing
                pa, pa_created = ProjectAssignment.objects.get_or_create(
                    project=project,
                    annotator=profile,
                    defaults={'role': 'annotator', 'assigned_by': 'setup_script'}
                )
                if pa_created:
                     print("  Created ProjectAssignment")
                
            else:
                print("  User already has assignments.")
        else:
            print("  No tasks to assign.")
            
    except Project.DoesNotExist:
        print(f"Project {target_project_id} not found")

except User.DoesNotExist:
    print(f"User {email} not found!")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
