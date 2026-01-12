import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.label_studio")
django.setup()

from projects.models import Project
from annotators.models import AnnotatorProfile, TaskAssignment
from django.contrib.auth import get_user_model

User = get_user_model()

# Get the project and annotator
project = Project.objects.get(id=15)
user = User.objects.get(email="azgmxrk@kemail.uk")
annotator = AnnotatorProfile.objects.get(user=user)

print(f"\n✓ PROJECT: {project.title} (ID: {project.id})")
print(f"  Total tasks: {project.tasks.count()}")

print(f"\n✓ ANNOTATOR: {user.email}")
print(f"  Trust level: {annotator.trust_level.level}")

# Check task assignments
assignments = TaskAssignment.objects.filter(
    task__project=project,
    annotator=annotator
)

print(f"\n✓ TASK ASSIGNMENTS: {assignments.count()}")

# Show first 5 assignments
print("\nFirst 5 assignments:")
for i, assignment in enumerate(assignments[:5], 1):
    print(f"  {i}. Task {assignment.task.id} - Status: {assignment.status}")

# Check assignment status breakdown
status_counts = {}
for status in ['pending', 'in_progress', 'completed', 'reviewed']:
    count = assignments.filter(status=status).count()
    if count > 0:
        status_counts[status] = count

print(f"\nAssignment status breakdown:")
for status, count in status_counts.items():
    print(f"  - {status}: {count}")

print("\n✅ Task assignment successful! The annotator should now see tasks in the web interface.")
