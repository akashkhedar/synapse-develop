
import os
import django
from django.utils import timezone

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.synapse')
django.setup()

from users.models import User
from annotators.models import AnnotatorProfile, TaskAssignment
from projects.models import Project
from tasks.models import Task

PROJECT_ID = 552

print("=" * 60)
print("Assigning Tasks to Annotators")
print("=" * 60)

# Get project and tasks
try:
    project = Project.objects.get(id=PROJECT_ID)
    print(f"\nProject: {project.title} (ID: {project.id})")
except Project.DoesNotExist:
    print(f"ERROR: Project {PROJECT_ID} not found!")
    exit(1)

tasks = Task.objects.filter(project=project)
task_count = tasks.count()
print(f"Total tasks in project: {task_count}")

if task_count == 0:
    print("ERROR: No tasks found in this project!")
    exit(1)

# Get annotators
annotators_to_assign = ["annotator1@gmail.com", "annotator2@gmail.com"]
annotator_profiles = []

for email in annotators_to_assign:
    try:
        user = User.objects.get(email=email)
        profile = AnnotatorProfile.objects.get(user=user)
        annotator_profiles.append(profile)
        print(f"Found annotator: {email}")
    except User.DoesNotExist:
        print(f"ERROR: User {email} not found!")
    except AnnotatorProfile.DoesNotExist:
        print(f"ERROR: AnnotatorProfile for {email} not found!")

if not annotator_profiles:
    print("ERROR: No valid annotator profiles found!")
    exit(1)

# Assign tasks to annotators
# Strategy: Split tasks evenly between annotators OR assign all tasks to both
# Using: Assign all tasks to both annotators (overlap mode)

print(f"\nAssigning all {task_count} tasks to {len(annotator_profiles)} annotators...")

for profile in annotator_profiles:
    assigned_count = 0
    skipped_count = 0
    
    for task in tasks:
        # Check if already assigned
        existing = TaskAssignment.objects.filter(annotator=profile, task=task).first()
        if existing:
            skipped_count += 1
            continue
            
        # Create assignment
        TaskAssignment.objects.create(
            annotator=profile,
            task=task,
            status="assigned"
        )
        assigned_count += 1
    
    print(f"  {profile.user.email}: {assigned_count} new assignments, {skipped_count} already existed")

print("\n" + "=" * 60)
print("Done! Tasks have been assigned.")
