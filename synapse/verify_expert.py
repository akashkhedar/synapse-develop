import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.label_studio")
django.setup()

from projects.models import Project
from annotators.models import AnnotatorProfile, TaskAssignment, TrustLevel
from annotators.assignment_engine import AssignmentEngine
from django.contrib.auth import get_user_model

User = get_user_model()

# Get the expert annotator (most recently created)
expert_user = User.objects.filter(email__startswith='expert').order_by('-id').first()
expert = AnnotatorProfile.objects.get(user=expert_user)

print("\n" + "="*60)
print("EXPERT ANNOTATOR STATUS")
print("="*60)
print(f"\nUser: {expert_user.email}")
print(f"  - ID: {expert_user.id}")
print(f"  - is_annotator: {expert_user.is_annotator}")
print(f"  - annotator_status: {expert_user.annotator_status}")
print(f"  - email_verified: {expert_user.email_verified}")

print(f"\nAnnotatorProfile: {expert.id}")
print(f"  - Status: {expert.status}")
print(f"  - Experience level: {expert.experience_level}")
print(f"  - Skills: {expert.skills}")
print(f"  - Email verified: {expert.email_verified}")

print(f"\nTrustLevel:")
print(f"  - Level: {expert.trust_level.level}")
print(f"  - Multiplier: {expert.trust_level.multiplier}x")
print(f"  - Tasks completed: {expert.trust_level.tasks_completed}")
print(f"  - Accuracy: {expert.trust_level.accuracy_score}%")

print(f"\nAnnotationTest:")
test = expert.tests.first()
if test:
    print(f"  - Status: {test.status}")
    print(f"  - Accuracy: {test.accuracy}%")
else:
    print("  - No test found")

# Check project assignment
project = Project.objects.get(id=15)
print(f"\nProject: {project.title} (ID: {project.id})")

# Check current task assignments
current_assignments = TaskAssignment.objects.filter(
    task__project=project,
    annotator=expert
).count()
print(f"  - Current task assignments: {current_assignments}")

if current_assignments == 0:
    print("\n📋 Distributing tasks to expert...")
    from annotators.models import ProjectAssignment
    annotators = [
        pa.annotator 
        for pa in ProjectAssignment.objects.filter(project=project, active=True)
        .select_related('annotator__user', 'annotator__trust_level')
    ]
    
    result = AssignmentEngine.distribute_tasks_intelligently(
        project=project,
        annotators=annotators,
        required_overlap=3
    )
    
    new_count = TaskAssignment.objects.filter(
        task__project=project,
        annotator=expert
    ).count()
    
    print(f"✓ Tasks distributed! Expert now has {new_count} task assignments")

print("\n" + "="*60)
print("✅ EXPERT ANNOTATOR READY")
print("="*60 + "\n")
