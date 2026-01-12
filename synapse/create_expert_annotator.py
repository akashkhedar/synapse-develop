import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.label_studio")
django.setup()

from django.contrib.auth import get_user_model
from annotators.models import AnnotatorProfile, AnnotationTest, TrustLevel, ProjectAssignment
from projects.models import Project
from django.utils import timezone

User = get_user_model()

print("\n" + "="*60)
print("Creating Expert Annotator")
print("="*60 + "\n")

# Generate unique email
email = f"expert{timezone.now().strftime('%Y%m%d%H%M%S')}@example.com"
username = email.split('@')[0]

# Create User
print(f"Creating user: {email}")
user = User.objects.create_user(
    username=username,
    email=email,
    password='expert123',  # Default password
    first_name='Expert',
    last_name='Annotator',
    is_annotator=True,
    annotator_status='approved',
    email_verified=True
)
print(f"✓ User created (ID: {user.id})")

# Create AnnotatorProfile
print("\nCreating AnnotatorProfile...")
annotator = AnnotatorProfile.objects.create(
    user=user,
    status='approved',
    email_verified=True,
    skills=['text_classification', 'named_entity_recognition', 'sentiment_analysis'],
    bio='Expert annotator with extensive experience',
    experience_level='expert',
    approved_at=timezone.now()
)
print(f"✓ AnnotatorProfile created (ID: {annotator.id})")

# Create AnnotationTest (passed)
print("\nCreating AnnotationTest...")
test = AnnotationTest.objects.create(
    annotator=annotator,
    status='passed',
    accuracy=98.50,
    submitted_at=timezone.now(),
    evaluated_at=timezone.now(),
    evaluated_by=user
)
print(f"✓ AnnotationTest created (ID: {test.id}, Accuracy: {test.accuracy}%)")

# Create TrustLevel (expert)
print("\nCreating TrustLevel...")
trust_level = TrustLevel.objects.create(
    annotator=annotator,
    level='expert',
    multiplier=1.5,  # Expert gets 1.5x payment
    tasks_completed=500,  # Simulate experience
    accuracy_score=98.50
)
print(f"✓ TrustLevel created (Level: {trust_level.level}, Multiplier: {trust_level.multiplier}x)")

# Assign to project 15 if it exists
try:
    project = Project.objects.get(id=15)
    print(f"\nAssigning to project: {project.title}")
    project_assignment = ProjectAssignment.objects.create(
        project=project,
        annotator=annotator,
        role='annotator',
        active=True,
        assigned_by='system'
    )
    print(f"✓ ProjectAssignment created (ID: {project_assignment.id})")
except Project.DoesNotExist:
    print("\n⚠ Project 15 not found - skipping project assignment")

print("\n" + "="*60)
print("✅ EXPERT ANNOTATOR CREATED SUCCESSFULLY")
print("="*60)
print(f"\nLogin credentials:")
print(f"  Email: {email}")
print(f"  Password: expert123")
print(f"\nAnnotator details:")
print(f"  User ID: {user.id}")
print(f"  Profile ID: {annotator.id}")
print(f"  Trust Level: {trust_level.level}")
print(f"  Payment Multiplier: {trust_level.multiplier}x")
print(f"  Status: {annotator.status}")
print("="*60 + "\n")
