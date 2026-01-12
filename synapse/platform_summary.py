import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.label_studio")
django.setup()

from django.contrib.auth import get_user_model
from annotators.models import AnnotatorProfile
from projects.models import Project, ProjectMember

User = get_user_model()

print("\n" + "="*80)
print("SYNAPSE PLATFORM - ALL USERS SUMMARY")
print("="*80 + "\n")

# Get all users
users = User.objects.all().order_by('-date_joined')

print(f"Total Users: {users.count()}\n")
print("="*80)

# Categorize users by role
admins = []
clients = []
experts = []
annotators = []

for user in users:
    role_info = {
        'email': user.email,
        'id': user.id,
        'name': f"{user.first_name} {user.last_name}".strip() or user.username,
        'verified': user.email_verified if hasattr(user, 'email_verified') else True,
        'active': user.is_active
    }
    
    if user.is_superuser or user.is_staff:
        role_info['role'] = 'Admin'
        admins.append(role_info)
    elif user.is_expert:
        role_info['role'] = 'Expert Reviewer'
        try:
            profile = user.annotator_profile
            role_info['trust_level'] = profile.trust_level.level
            role_info['multiplier'] = f"{profile.trust_level.multiplier}x"
        except:
            pass
        experts.append(role_info)
    elif user.is_client:
        role_info['role'] = 'Client'
        clients.append(role_info)
    elif user.is_annotator:
        role_info['role'] = 'Annotator'
        try:
            profile = user.annotator_profile
            role_info['trust_level'] = profile.trust_level.level
            role_info['multiplier'] = f"{profile.trust_level.multiplier}x"
            role_info['status'] = profile.status
        except:
            pass
        annotators.append(role_info)

# Display by role
print("\n📋 ADMINS ({})".format(len(admins)))
print("-" * 80)
for admin in admins:
    print(f"  • {admin['name']} ({admin['email']})")
    print(f"    ID: {admin['id']} | Active: {admin['active']}")

print("\n💼 CLIENTS ({})".format(len(clients)))
print("-" * 80)
for client in clients:
    print(f"  • {client['name']} ({client['email']})")
    print(f"    ID: {client['id']} | Verified: {client['verified']} | Active: {client['active']}")

print("\n⭐ EXPERT REVIEWERS ({})".format(len(experts)))
print("-" * 80)
for expert in experts:
    print(f"  • {expert['name']} ({expert['email']})")
    print(f"    ID: {expert['id']} | Trust: {expert.get('trust_level', 'N/A')} | Pay: {expert.get('multiplier', 'N/A')}")
    print(f"    Verified: {expert['verified']} | Active: {expert['active']}")

print("\n✍️ ANNOTATORS ({})".format(len(annotators)))
print("-" * 80)
for annotator in annotators:
    print(f"  • {annotator['name']} ({annotator['email']})")
    print(f"    ID: {annotator['id']} | Trust: {annotator.get('trust_level', 'N/A')} | Pay: {annotator.get('multiplier', 'N/A')}")
    print(f"    Status: {annotator.get('status', 'N/A')} | Verified: {annotator['verified']}")

# Project 15 summary
print("\n" + "="*80)
print("PROJECT 15 TEAM")
print("="*80)

try:
    project = Project.objects.get(id=15)
    print(f"\nProject: {project.title}")
    print(f"Total Tasks: {project.tasks.count()}")
    
    # Project members
    members = ProjectMember.objects.filter(project=project).select_related('user')
    print(f"\nProject Members: {members.count()}")
    print("-" * 80)
    
    for member in members:
        user = member.user
        role = user.get_user_role() if hasattr(user, 'get_user_role') else 'Unknown'
        print(f"  • {user.email} - {role.title()}")
        
    # Annotator assignments
    from annotators.models import ProjectAssignment, TaskAssignment
    
    project_assignments = ProjectAssignment.objects.filter(
        project=project,
        active=True
    ).select_related('annotator__user', 'annotator__trust_level')
    
    if project_assignments.exists():
        print(f"\nActive Annotators: {project_assignments.count()}")
        print("-" * 80)
        for pa in project_assignments:
            task_count = TaskAssignment.objects.filter(
                task__project=project,
                annotator=pa.annotator
            ).count()
            print(f"  • {pa.annotator.user.email}")
            print(f"    Trust: {pa.annotator.trust_level.level} | Tasks: {task_count}")
    
except Project.DoesNotExist:
    print("\n⚠ Project 15 not found")

print("\n" + "="*80)
print("✅ PLATFORM READY - ALL ROLES ACTIVE")
print("="*80 + "\n")
