"""Management command to list pending annotators"""

from django.core.management.base import BaseCommand
from annotators.models import AnnotatorProfile, AnnotationTest


class Command(BaseCommand):
    help = 'List all pending annotators awaiting approval'

    def handle(self, *args, **options):
        self.stdout.write("\n" + "="*80)
        self.stdout.write("PENDING ANNOTATORS AWAITING APPROVAL")
        self.stdout.write("="*80 + "\n")

        # Get all non-approved annotators
        pending = AnnotatorProfile.objects.filter(
            status__in=['pending_verification', 'pending_test', 'test_submitted', 'under_review']
        ).select_related('user').order_by('status', '-applied_at')

        if not pending.exists():
            self.stdout.write(self.style.WARNING("✨ No pending annotators found\n"))
            return

        for profile in pending:
            # Get test info
            test = AnnotationTest.objects.filter(annotator=profile).order_by('-created_at').first()
            
            self.stdout.write(f"\n📧 Email: {profile.user.email}")
            self.stdout.write(f"   Name: {profile.user.get_full_name() or 'Not provided'}")
            self.stdout.write(f"   Status: {self.get_status_display(profile.status)}")
            self.stdout.write(f"   Email Verified: {'✅ Yes' if profile.email_verified else '❌ No'}")
            self.stdout.write(f"   Applied: {profile.applied_at.strftime('%Y-%m-%d %H:%M')}")
            
            if test:
                self.stdout.write(f"   Test Status: {test.status}")
                if test.submitted_at:
                    self.stdout.write(f"   Test Submitted: {test.submitted_at.strftime('%Y-%m-%d %H:%M')}")
                if test.accuracy:
                    self.stdout.write(f"   Test Accuracy: {test.accuracy}%")
            
            self.stdout.write(f"   👉 Approve: python manage.py approve_annotator {profile.user.email}")
            self.stdout.write("-" * 80)

        self.stdout.write(f"\n📊 Total pending: {pending.count()}")
        self.stdout.write("")

    def get_status_display(self, status):
        """Add color to status"""
        status_colors = {
            'pending_verification': '🔴 Pending Email Verification',
            'pending_test': '🟡 Pending Test',
            'test_submitted': '🟢 Test Submitted - Ready for Approval',
            'under_review': '🟠 Under Review',
        }
        return status_colors.get(status, status)
