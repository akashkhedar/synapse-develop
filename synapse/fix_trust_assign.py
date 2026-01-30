
import os
import django
from django.utils import timezone

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.synapse')
django.setup()

from users.models import User
from annotators.models import AnnotatorProfile, TrustLevel
from projects.models import Project, ProjectMember

PROJECT_ID = 552

print("=" * 60)
print("Fixing Trust Levels and Assigning Project")
print("=" * 60)

# Step 1: Create TrustLevel for all AnnotatorProfiles that don't have one
profiles_without_trust = AnnotatorProfile.objects.filter(trust_level__isnull=True)
print(f"\nFound {profiles_without_trust.count()} profiles without TrustLevel")

for profile in profiles_without_trust:
    trust_level = TrustLevel.objects.create(annotator=profile)
    print(f"  Created TrustLevel for: {profile.user.email}")

print(f"\nAll profiles now have TrustLevel records.")

# Step 2: Assign project 552 to annotator1 and annotator2
try:
    project = Project.objects.get(id=PROJECT_ID)
    print(f"\nProject: {project.title} (ID: {project.id})")
except Project.DoesNotExist:
    print(f"ERROR: Project {PROJECT_ID} not found!")
    exit(1)

annotators_to_assign = ["annotator1@gmail.com", "annotator2@gmail.com"]

for email in annotators_to_assign:
    try:
        user = User.objects.get(email=email)
        
        # Create ProjectMember if not exists
        member, created = ProjectMember.objects.get_or_create(
            project=project,
            user=user,
            defaults={'enabled': True}
        )
        
        if created:
            print(f"  Added {email} to project {PROJECT_ID}")
        else:
            # Make sure they're enabled
            if not member.enabled:
                member.enabled = True
                member.save()
                print(f"  Re-enabled {email} on project {PROJECT_ID}")
            else:
                print(f"  {email} already assigned to project {PROJECT_ID}")
                
    except User.DoesNotExist:
        print(f"  ERROR: User {email} not found!")

print("\n" + "=" * 60)
print("Done!")
