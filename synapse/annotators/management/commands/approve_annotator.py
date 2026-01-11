"""Management command to approve annotators"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from annotators.models import AnnotatorProfile, AnnotationTest


class Command(BaseCommand):
    help = 'Approve an annotator and their test'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email of the annotator to approve')

    def handle(self, *args, **options):
        email = options['email']

        try:
            # Find the annotator by email
            profile = AnnotatorProfile.objects.select_related('user').get(user__email=email)
            
            self.stdout.write(f"\n📋 Found annotator: {profile.user.get_full_name() or profile.user.email}")
            self.stdout.write(f"Current status: {profile.status}")
            
            # Get their test if they have one
            test = AnnotationTest.objects.filter(annotator=profile).order_by('-created_at').first()
            
            if test:
                self.stdout.write(f"Test status: {test.status}")
                self.stdout.write(f"Test submitted: {test.submitted_at}")
                
                # Approve the test
                if test.status == 'submitted' or test.status == 'pending':
                    test.status = 'passed'
                    test.accuracy = 100.00  # Default perfect score
                    test.evaluated_at = timezone.now()
                    test.feedback = "Test approved by admin"
                    test.save(update_fields=['status', 'accuracy', 'evaluated_at', 'feedback'])
                    self.stdout.write(self.style.SUCCESS(f"✅ Test marked as passed"))
            
            # Approve the annotator
            if profile.status != 'approved':
                profile.status = 'approved'
                profile.approved_at = timezone.now()
                profile.user.is_active = True
                profile.user.save(update_fields=['is_active'])
                profile.save(update_fields=['status', 'approved_at'])
                
                self.stdout.write(self.style.SUCCESS(f"\n✅ Annotator approved successfully!"))
                self.stdout.write(f"Email: {profile.user.email}")
                self.stdout.write(f"Status: {profile.status}")
                self.stdout.write(f"Approved at: {profile.approved_at}")
                self.stdout.write(f"User is_active: {profile.user.is_active}")
            else:
                self.stdout.write(self.style.WARNING(f"\n⚠️  Annotator already approved"))
                
        except AnnotatorProfile.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"\n❌ No annotator found with email: {email}"))
            self.stdout.write("\nList of pending annotators:")
            
            pending = AnnotatorProfile.objects.filter(
                status__in=['pending_verification', 'pending_test', 'test_submitted', 'under_review']
            ).select_related('user')
            
            if pending.exists():
                for p in pending:
                    self.stdout.write(f"  - {p.user.email} ({p.status})")
            else:
                self.stdout.write("  No pending annotators found")
