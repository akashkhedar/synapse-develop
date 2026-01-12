import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.label_studio")
django.setup()

from projects.models import Project
from annotators.models import AnnotatorProfile, TaskAssignment, ProjectAssignment
from annotators.assignment_engine import AssignmentEngine
from django.contrib.auth import get_user_model

User = get_user_model()

print("\n" + "=" * 60)
print("Distributing tasks for project 15")
print("=" * 60 + "\n")

# Get the project
project = Project.objects.get(id=15)
print(f"Project: {project.title}")
print(f"Total tasks: {project.tasks.count()}")

# Get the annotator
user = User.objects.get(email="azgmxrk@kemail.uk")
annotator = AnnotatorProfile.objects.get(user=user)
print(f"Annotator: {user.email}")
print(f"Trust level: {annotator.trust_level.level} ({annotator.trust_level.multiplier}x)")

# Get all active annotators for the project
project_assignments = ProjectAssignment.objects.filter(
    project=project,
    active=True
).select_related('annotator__user', 'annotator__trust_level')

annotators = [pa.annotator for pa in project_assignments]
print(f"\nAnnotators assigned to project: {len(annotators)}")
for a in annotators:
    print(f"  - {a.user.email} (trust level: {a.trust_level.level})")

# Check current task assignments
current_assignments = TaskAssignment.objects.filter(
    task__project=project,
    annotator=annotator
).count()
print(f"\nCurrent task assignments for {user.email}: {current_assignments}")

# Distribute tasks
print("\nDistributing tasks...")
try:
    result = AssignmentEngine.distribute_tasks_intelligently(
        project=project,
        annotators=annotators,
        required_overlap=3
    )
    print(f"\n✓ Distribution complete!")
    print(f"  - Assigned tasks: {result.get('assigned_tasks', 0)}")
    print(f"  - Annotators used: {result.get('annotators_used', 0)}")
    
    # Check assignments after distribution
    new_assignments = TaskAssignment.objects.filter(
        task__project=project,
        annotator=annotator
    ).count()
    print(f"\nTask assignments after distribution: {new_assignments}")
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
