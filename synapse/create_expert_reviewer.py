import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.label_studio")
django.setup()

from django.contrib.auth import get_user_model
from annotators.models import AnnotatorProfile, TrustLevel
from projects.models import Project, ProjectMember
from django.utils import timezone

User = get_user_model()

print("\n" + "="*70)
print("CREATING EXPERT REVIEWER")
print("="*70 + "\n")

# Generate unique email
email = f"expert.reviewer{timezone.now().strftime('%Y%m%d%H%M%S')}@synapse.com"
username = email.split('@')[0]

# Create Expert User
print(f"Creating expert user: {email}")
user = User.objects.create_user(
    username=username,
    email=email,
    password='expert123',
    first_name='Expert',
    last_name='Reviewer',
    is_expert=True,  # Expert role for quality review
    is_annotator=False,  # Not an annotator
    is_client=False,  # Not a client
    email_verified=True
)
print(f"✓ Expert user created (ID: {user.id})")

# Create AnnotatorProfile for the expert (experts can have profiles too for reviewing)
print("\nCreating expert profile...")
expert_profile = AnnotatorProfile.objects.create(
    user=user,
    status='approved',
    email_verified=True,
    skills=['quality_assurance', 'consensus_review', 'task_validation'],
    bio='Expert reviewer for quality assurance and consensus tasks',
    experience_level='expert',
    approved_at=timezone.now()
)
print(f"✓ Expert profile created (ID: {expert_profile.id})")

# Create TrustLevel (expert level for high-quality reviews)
print("\nCreating expert trust level...")
trust_level = TrustLevel.objects.create(
    annotator=expert_profile,
    level='expert',
    multiplier=2.0,  # Expert reviewers get 2.0x payment
    tasks_completed=1000,  # Simulated extensive experience
    accuracy_score=99.00
)
print(f"✓ TrustLevel created (Level: {trust_level.level}, Multiplier: {trust_level.multiplier}x)")

# Add expert as reviewer to project 15
try:
    project = Project.objects.get(id=15)
    print(f"\nAdding expert as reviewer to project: {project.title}")
    
    # Check if ProjectMember already exists
    project_member, created = ProjectMember.objects.get_or_create(
        user=user,
        project=project,
        defaults={'enabled': True}
    )
    
    if created:
        print(f"✓ Expert added to project as member (ID: {project_member.id})")
    else:
        print(f"✓ Expert already member of project")
        
except Project.DoesNotExist:
    print("\n⚠ Project 15 not found - skipping project assignment")

print("\n" + "="*70)
print("✅ EXPERT REVIEWER CREATED SUCCESSFULLY")
print("="*70)
print(f"\nLogin credentials:")
print(f"  Email: {email}")
print(f"  Password: expert123")
print(f"\nExpert details:")
print(f"  User ID: {user.id}")
print(f"  Role: Expert Reviewer (is_expert=True)")
print(f"  Profile ID: {expert_profile.id}")
print(f"  Trust Level: {trust_level.level}")
print(f"  Payment Multiplier: {trust_level.multiplier}x")
print(f"  Can review consolidated tasks: Yes")
print(f"  Email Verified: Yes")
print("="*70 + "\n")
