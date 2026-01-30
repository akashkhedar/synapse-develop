
import sys
from users.models import User
from projects.models import Project
from tasks.models import Task
from annotators.models import TaskAssignment, ProjectAssignment

email = "born200three@gmail.com"
project_id = 549

print(f"Inspecting Project {project_id} for user {email}")

try:
    user = User.objects.get(email=email)
    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        print(f"Project {project_id} DOES NOT EXIST")
        sys.exit()

    print(f"Project: {project.title}")
    
    # Check Project Assignment
    has_proj_assignment = ProjectAssignment.objects.filter(project=project, annotator__user=user).exists()
    print(f"Has ProjectAssignment: {has_proj_assignment}")
    
    # Check Task Assignments
    task_assignments = TaskAssignment.objects.filter(task__project=project, annotator__user=user)
    count = task_assignments.count()
    print(f"Task Assignments count: {count}")
    
    if count == 0:
        tasks_count = Task.objects.filter(project=project).count()
        print(f"Total tasks in project: {tasks_count}")
        if tasks_count > 0:
            print("Action Needed: Assign tasks to user.")
        else:
            print("Action Needed: Project has no tasks to assign!")

except User.DoesNotExist:
    print(f"User {email} not found!")

except Exception as e:
    print(f"Error: {e}")
