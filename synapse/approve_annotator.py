# Approve annotator: azgmxrk@kemail.uk
from django.utils import timezone
from annotators.models import AnnotatorProfile, AnnotationTest

EMAIL = "azgmxrk@kemail.uk"
print(f"\nApproving annotator: {EMAIL}\n")

try:
    profile = AnnotatorProfile.objects.select_related('user').get(user__email=EMAIL)
    print(f"Found: {profile.user.email} (Status: {profile.status})")
    
    # Approve test
    test = profile.tests.order_by('-created_at').first()
    if test and test.status in ['submitted', 'pending', 'in_progress']:
        test.status = 'passed'
        test.accuracy = 100.00
        test.evaluated_at = timezone.now()
        test.feedback = "Approved by admin"
        test.save()
        print("✓ Test approved")
    
    # Approve annotator
    if profile.status != 'approved':
        profile.status = 'approved'
        profile.approved_at = timezone.now()
        profile.user.is_active = True
        profile.user.save()
        profile.save()
        print(f"✓ APPROVED! Status: {profile.status}")
    else:
        print("⚠ Already approved")
        
except AnnotatorProfile.DoesNotExist:
    print(f"✗ Not found: {EMAIL}")
    print("\nPending annotators:")
    for p in AnnotatorProfile.objects.filter(status__in=['pending_verification', 'pending_test', 'test_submitted', 'under_review']).select_related('user'):
        print(f"  - {p.user.email} ({p.status})")
