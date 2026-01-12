import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.label_studio")
django.setup()

from projects.models import Project
from annotators.models import AnnotatorProfile, ProjectAssignment
from django.contrib.auth import get_user_model

User = get_user_model()

print("\n" + "="*70)
print("CLEANING UP INCOMPLETE ANNOTATORS")
print("="*70 + "\n")

# Find annotators without trust levels
incomplete = []
for profile in AnnotatorProfile.objects.select_related('user'):
    try:
        _ = profile.trust_level
    except:
        incomplete.append(profile)
        print(f"Found incomplete: {profile.user.email} (Profile ID: {profile.id})")

if incomplete:
    print(f"\nRemoving {len(incomplete)} incomplete annotator(s)...")
    for profile in incomplete:
        email = profile.user.email
        user_id = profile.user.id
        # Remove project assignments first
        ProjectAssignment.objects.filter(annotator=profile).delete()
        # Delete user (will cascade to profile)
        profile.user.delete()
        print(f"  ✓ Removed {email} (User ID: {user_id})")
else:
    print("No incomplete annotators found")

print("\n" + "="*70)
print("FINAL PROJECT STATUS")
print("="*70)

project = Project.objects.get(id=15)
print(f"\nProject: {project.title}")
print(f"Total tasks: {project.tasks.count()}")

assignments = ProjectAssignment.objects.filter(
    project=project, 
    active=True
).select_related('annotator__user', 'annotator__trust_level')

print(f"\nActive annotators: {assignments.count()}")
print("-" * 70)

from annotators.models import TaskAssignment

for pa in assignments:
    annotator = pa.annotator
    task_count = TaskAssignment.objects.filter(
        task__project=project,
        annotator=annotator
    ).count()
    
    print(f"\n✓ {annotator.user.email}")
    print(f"  • Trust Level: {annotator.trust_level.level} ({annotator.trust_level.multiplier}x)")
    print(f"  • Experience: {annotator.experience_level}")
    print(f"  • Tasks Assigned: {task_count}")
    print(f"  • Status: {annotator.status}")
    print(f"  • Can Login: {'Yes' if annotator.user.email_verified and annotator.user.is_annotator else 'No'}")

print("\n" + "="*70)
print("✅ SETUP COMPLETE")
print("="*70 + "\n")
