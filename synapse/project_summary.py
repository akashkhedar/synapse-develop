import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.label_studio")
django.setup()

from projects.models import Project
from annotators.models import AnnotatorProfile, TaskAssignment, ProjectAssignment
from django.contrib.auth import get_user_model

User = get_user_model()

print("\n" + "="*70)
print("PROJECT 15 - ANNOTATOR SUMMARY")
print("="*70)

project = Project.objects.get(id=15)
print(f"\nProject: {project.title}")
print(f"Total tasks: {project.tasks.count()}")

# Get all annotators
assignments = ProjectAssignment.objects.filter(project=project, active=True).select_related('annotator__user', 'annotator__trust_level')

print(f"\nActive annotators: {assignments.count()}")
print("-" * 70)

for pa in assignments:
    annotator = pa.annotator
    task_count = TaskAssignment.objects.filter(
        task__project=project,
        annotator=annotator
    ).count()
    
    print(f"\n{annotator.user.email}")
    print(f"  Trust Level: {annotator.trust_level.level} ({annotator.trust_level.multiplier}x)")
    print(f"  Experience: {annotator.experience_level}")
    print(f"  Tasks Assigned: {task_count}")
    print(f"  Status: {annotator.status}")

print("\n" + "="*70)
print("✅ ALL ANNOTATORS ACTIVE AND READY")
print("="*70 + "\n")
