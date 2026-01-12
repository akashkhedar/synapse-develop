"""
Management command to create an ExpertProfile for a user.

Usage:
    python manage.py create_expert_profile <email>
    python manage.py create_expert_profile <email> --level senior_expert
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from annotators.models import ExpertProfile

User = get_user_model()


class Command(BaseCommand):
    help = "Create an ExpertProfile for a user to access expert features"

    def add_arguments(self, parser):
        parser.add_argument(
            "email",
            type=str,
            help="Email of the user to create expert profile for",
        )
        parser.add_argument(
            "--level",
            type=str,
            default="junior_expert",
            choices=["junior_expert", "senior_expert", "lead_expert"],
            help="Expertise level (default: junior_expert)",
        )
        parser.add_argument(
            "--areas",
            type=str,
            nargs="+",
            default=["classification", "bounding_box", "ner"],
            help="Expertise areas (default: classification bounding_box ner)",
        )

    def handle(self, *args, **options):
        email = options["email"]
        level = options["level"]
        areas = options["areas"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise CommandError(f"User with email '{email}' not found")

        # Check if expert profile already exists
        if hasattr(user, "expert_profile"):
            self.stdout.write(
                self.style.WARNING(
                    f"User {email} already has an ExpertProfile (ID: {user.expert_profile.id})"
                )
            )
            return

        # Create expert profile
        expert_profile = ExpertProfile.objects.create(
            user=user,
            status="active",
            expertise_level=level,
            expertise_areas=areas,
        )

        # Also set is_expert on user if not already set
        if not user.is_expert:
            user.is_expert = True
            user.save(update_fields=["is_expert"])
            self.stdout.write(f"  ✓ Set is_expert=True on user")

        self.stdout.write(
            self.style.SUCCESS(
                f"✓ Created ExpertProfile for {email}\n"
                f"  - Profile ID: {expert_profile.id}\n"
                f"  - Level: {level}\n"
                f"  - Areas: {areas}"
            )
        )
