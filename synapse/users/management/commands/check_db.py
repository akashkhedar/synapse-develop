"""Check database configuration"""

from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = "Check database configuration"

    def handle(self, *args, **options):
        db = settings.DATABASES["default"]

        self.stdout.write(self.style.SUCCESS("\n📊 Database Configuration:\n"))
        self.stdout.write(f'   Engine: {db["ENGINE"]}')
        self.stdout.write(f'   Name: {db.get("NAME", "N/A")}')
        self.stdout.write(f'   Host: {db.get("HOST", "N/A")}')
        self.stdout.write(f'   Port: {db.get("PORT", "N/A")}')
        self.stdout.write(f'   User: {db.get("USER", "N/A")}')

        # Check if using PostgreSQL or SQLite
        if "sqlite" in db["ENGINE"]:
            self.stdout.write(
                self.style.WARNING(
                    "\n⚠️  Using SQLite - this might have concurrency issues"
                )
            )
        else:
            self.stdout.write(self.style.SUCCESS("\n✅ Using production database"))





