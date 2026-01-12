import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.label_studio")
django.setup()

from projects.models import Project
from annotators.models import AnnotatorProfile, TaskAssignment, ProjectAssignment
from annotators.assignment_engine import AssignmentEngine
from django.contrib.auth import get_user_model

User = get_user_model()

# Get the project and annotator
project = Project.objects.get(id=15)
user = User.objects.get(email="azgmxrk@kemail.uk")
annotator = AnnotatorProfile.objects.get(user=user)

print(f"\nProject: {project.title} (ID: {project.id})")
print(f"Total tasks: {project.tasks.count()}")
print(f"Annotator: {user.email}")
print(f"Trust level: {annotator.trust_level.level}")

# Get active annotators
annotators = [
    pa.annotator 
    for pa in ProjectAssignment.objects.filter(project=project, active=True)
    .select_related('annotator__user', 'annotator__trust_level')
]

print(f"Active annotators: {len(annotators)}")

# Check current assignments
before_count = TaskAssignment.objects.filter(
    task__project=project,
    annotator=annotator
).count()
print(f"Task assignments before: {before_count}")

# Distribute tasks
print("\nCalling distribute_tasks_intelligently...")
result = AssignmentEngine.distribute_tasks_intelligently(
    project=project,
    annotators=annotators,
    required_overlap=3
)

# Check after
after_count = TaskAssignment.objects.filter(
    task__project=project,
    annotator=annotator
).count()

print(f"\n✓ RESULT:")
print(f"  - Return value: {result}")
print(f"  - Task assignments after: {after_count}")
print(f"  - New assignments: {after_count - before_count}")
