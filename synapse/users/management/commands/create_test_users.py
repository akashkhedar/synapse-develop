"""
Django management command to create test users
Usage: python manage.py create_test_users
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from users.models import User
from organizations.models import Organization, OrganizationMember


class Command(BaseCommand):
    help = 'Create test users with different roles and verify their emails'

    def handle(self, *args, **options):
        PASSWORD = "itsAKASH@26"

        # User configurations
        users_config = [
            {
                "email": "client@gmail.com",
                "username": "Client User",
                "is_client": True,
                "is_annotator": False,
                "is_expert": False,
            },
            {
                "email": "annotator1@gmail.com",
                "username": "Annotator One",
                "is_client": False,
                "is_annotator": True,
                "is_expert": False,
            },
            {
                "email": "annotator2@gmail.com",
                "username": "Annotator Two",
                "is_client": False,
                "is_annotator": True,
                "is_expert": False,
            },
            {
                "email": "expert@gmail.com",
                "username": "Expert User",
                "is_client": False,
                "is_annotator": False,
                "is_expert": True,
            },
        ]

        self.stdout.write("Creating test users...")
        self.stdout.write("=" * 60)

        for config in users_config:
            email = config["email"]
            
            # Check if user already exists
            if User.objects.filter(email=email).exists():
                user = User.objects.get(email=email)
                self.stdout.write(
                    self.style.WARNING(f"✓ User {email} already exists, updating...")
                )
            else:
                # Create new user
                user = User.objects.create_user(
                    email=email,
                    password=PASSWORD,
                    username=config["username"],
                )
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Created user: {email}")
                )
            
            # Set roles
            user.is_client = config["is_client"]
            user.is_annotator = config["is_annotator"]
            user.is_expert = config["is_expert"]
            
            # Verify email and activate
            user.email_verified = True
            user.email_verified_at = timezone.now()
            user.is_active = True
            
            # Set annotator status to approved if annotator or expert
            if config["is_annotator"] or config["is_expert"]:
                user.annotator_status = "approved"
            
            user.save()
            
            role = "Client" if config["is_client"] else "Annotator" if config["is_annotator"] else "Expert"
            self.stdout.write(f"  - Role: {role}")
            self.stdout.write(f"  - Email Verified: ✓")
            self.stdout.write(f"  - Status: Active")
            if config["is_annotator"] or config["is_expert"]:
                self.stdout.write(f"  - Annotator Status: Approved")
            self.stdout.write("")

        self.stdout.write("=" * 60)
        
        # Create organization for client
        self.stdout.write("\nCreating organization for client...")
        client_user = User.objects.get(email="client@gmail.com")
        
        # Check if organization already exists
        try:
            org = Organization.find_by_user(client_user)
            self.stdout.write(
                self.style.WARNING(f"✓ Organization already exists: {org.title}")
            )
        except ValueError:
            # Create new organization
            org = Organization.create_organization(
                created_by=client_user,
                title="Client Test Organization"
            )
            # Add client as owner
            OrganizationMember.objects.create(
                user=client_user,
                organization=org,
                role=OrganizationMember.ROLE_OWNER
            )
            # Set as active organization
            client_user.active_organization = org
            client_user.save(update_fields=['active_organization'])
            self.stdout.write(
                self.style.SUCCESS(f"✓ Created organization: {org.title}")
            )
        
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("All users created successfully!"))
        self.stdout.write(f"Password for all users: {PASSWORD}")
        self.stdout.write("\nYou can now login with:")
        for config in users_config:
            role = "Client" if config["is_client"] else "Annotator" if config["is_annotator"] else "Expert"
            self.stdout.write(f"  - {config['email']} ({role})")
