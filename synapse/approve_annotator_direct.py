"""Direct script to approve an annotator"""
import os
import sys
import pathlib

# Setup Django environment
SYNAPSE_PATH = str(pathlib.Path(__file__).parent.absolute())
sys.path.insert(0, SYNAPSE_PATH)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "synapse.core.settings.synapse")

# Load environment variables
try:
    from dotenv import load_dotenv
    env_path = pathlib.Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path, override=True)
except ImportError:
    pass

# Initialize Django
import django
django.setup()

from django.utils import timezone
from annotators.models import AnnotatorProfile, AnnotationTest


def list_pending_annotators():
    """List all pending annotators"""
    print("\n" + "="*80)
    print("PENDING ANNOTATORS AWAITING APPROVAL")
    print("="*80 + "\n")

    pending = AnnotatorProfile.objects.filter(
        status__in=['pending_verification', 'pending_test', 'test_submitted', 'under_review']
    ).select_related('user').order_by('status', '-applied_at')

    if not pending.exists():
        print("✨ No pending annotators found\n")
        return []

    annotators = []
    for profile in pending:
        test = AnnotationTest.objects.filter(annotator=profile).order_by('-created_at').first()
        
        print(f"\n📧 Email: {profile.user.email}")
        print(f"   Name: {profile.user.get_full_name() or 'Not provided'}")
        print(f"   Status: {profile.status}")
        print(f"   Email Verified: {'✅ Yes' if profile.email_verified else '❌ No'}")
        print(f"   Applied: {profile.applied_at.strftime('%Y-%m-%d %H:%M')}")
        
        if test:
            print(f"   Test Status: {test.status}")
            if test.submitted_at:
                print(f"   Test Submitted: {test.submitted_at.strftime('%Y-%m-%d %H:%M')}")
            if test.accuracy:
                print(f"   Test Accuracy: {test.accuracy}%")
        
        print("-" * 80)
        annotators.append(profile)

    print(f"\n📊 Total pending: {len(annotators)}\n")
    return annotators


def approve_annotator(email):
    """Approve an annotator by email"""
    try:
        profile = AnnotatorProfile.objects.select_related('user').get(user__email=email)
        
        print(f"\n📋 Found annotator: {profile.user.get_full_name() or profile.user.email}")
        print(f"Current status: {profile.status}")
        
        # Get their test if they have one
        test = AnnotationTest.objects.filter(annotator=profile).order_by('-created_at').first()
        
        if test:
            print(f"Test status: {test.status}")
            
            # Approve the test
            if test.status in ['submitted', 'pending', 'in_progress']:
                test.status = 'passed'
                test.accuracy = 100.00
                test.evaluated_at = timezone.now()
                test.feedback = "Test approved by admin"
                test.save(update_fields=['status', 'accuracy', 'evaluated_at', 'feedback'])
                print("✅ Test marked as passed")
        
        # Approve the annotator
        if profile.status != 'approved':
            profile.status = 'approved'
            profile.approved_at = timezone.now()
            profile.user.is_active = True
            profile.user.save(update_fields=['is_active'])
            profile.save(update_fields=['status', 'approved_at'])
            
            print(f"\n✅ Annotator approved successfully!")
            print(f"Email: {profile.user.email}")
            print(f"Status: {profile.status}")
            print(f"Approved at: {profile.approved_at}")
        else:
            print(f"\n⚠️  Annotator already approved")
            
        return True
        
    except AnnotatorProfile.DoesNotExist:
        print(f"\n❌ No annotator found with email: {email}")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Approve specific annotator
        email = sys.argv[1]
        approve_annotator(email)
    else:
        # List all pending
        annotators = list_pending_annotators()
        
        if annotators:
            print("\n💡 To approve an annotator, run:")
            print(f"   python approve_annotator_direct.py EMAIL")
