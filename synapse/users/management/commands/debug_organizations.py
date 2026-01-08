"""
Django management command to debug organization issues
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from organizations.models import Organization, OrganizationMember

User = get_user_model()


class Command(BaseCommand):
    help = "Debug organization memberships for users"

    def handle(self, *args, **options):
        users = User.objects.all()

        self.stdout.write(
            self.style.SUCCESS(f"\n📊 Found {users.count()} total users:\n")
        )

        for user in users:
            self.stdout.write(f"\n👤 User: {user.email} (ID: {user.id})")
            self.stdout.write(
                f"   Staff: {user.is_staff}, Superuser: {user.is_superuser}"
            )
            self.stdout.write(f"   Active: {user.is_active}")
            self.stdout.write(f"   Active Organization: {user.active_organization}")

            # Check memberships
            memberships = OrganizationMember.objects.filter(user=user)
            self.stdout.write(f"   Memberships: {memberships.count()}")

            for membership in memberships:
                self.stdout.write(
                    f"      - Organization: {membership.organization.title} (ID: {membership.organization.id})"
                )
                self.stdout.write(
                    f"        Deleted: {membership.deleted_at is not None}"
                )

        # List all organizations
        orgs = Organization.objects.all()
        self.stdout.write(
            self.style.SUCCESS(f"\n\n🏢 Found {orgs.count()} total organizations:\n")
        )

        for org in orgs:
            members = OrganizationMember.objects.filter(organization=org)
            self.stdout.write(f"\n   Organization: {org.title} (ID: {org.id})")
            self.stdout.write(f"   Created by: {org.created_by}")
            self.stdout.write(f"   Token: {org.token}")
            self.stdout.write(f"   Members: {members.count()}")





