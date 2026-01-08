"""
Django management command to create organizations for users without memberships
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from organizations.models import Organization, OrganizationMember

User = get_user_model()


class Command(BaseCommand):
    help = "Create organizations for users without memberships"

    def handle(self, *args, **options):
        users_without_org = []

        # Find all users without organization membership
        for user in User.objects.all():
            memberships = OrganizationMember.objects.filter(user=user)
            if not memberships.exists():
                users_without_org.append(user)
                self.stdout.write(
                    self.style.WARNING(f"Found user without organization: {user.email}")
                )

        if not users_without_org:
            self.stdout.write(self.style.SUCCESS("✅ All users have organizations!"))
            return

        self.stdout.write(
            f"\n📝 Creating organizations for {len(users_without_org)} users...\n"
        )

        for user in users_without_org:
            # Create organization for this user
            org = Organization.create_organization(
                created_by=user, title=f"{user.email.split('@')[0]}'s Organization"
            )

            # Create membership with owner role
            OrganizationMember.objects.create(user=user, organization=org)

            # Set as active organization
            user.active_organization = org
            user.save(update_fields=["active_organization"])

            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Created organization '{org.title}' for {user.email}"
                )
            )
            self.stdout.write(f"   Organization ID: {org.id}")
            self.stdout.write(f"   Token: {org.token}\n")

        self.stdout.write(
            self.style.SUCCESS(f"\n🎉 Fixed {len(users_without_org)} users!")
        )
        self.stdout.write(self.style.SUCCESS("You can now log in successfully.\n"))





