# Script to approve annotator - run with: python server.py shell < approve_script.py
from django.utils import timezone
from annotators.models import AnnotatorProfile, AnnotationTest

print("\n" + "="*80)
print("PENDING ANNOTATORS AWAITING APPROVAL")
print("="*80 + "\n")

pending = AnnotatorProfile.objects.filter(
    status__in=['pending_verification', 'pending_test', 'test_submitted', 'under_review']
).select_related('user').order_by('status', '-applied_at')

if not pending.exists():
    print("✨ No pending annotators found\n")
else:
    for profile in pending:
        test = AnnotationTest.objects.filter(annotator=profile).order_by('-created_at').first()
        
        print(f"📧 Email: {profile.user.email}")
        print(f"   Name: {profile.user.get_full_name() or 'Not provided'}")
        print(f"   Status: {profile.status}")
        print(f"   Email Verified: {'✅ Yes' if profile.email_verified else '❌ No'}")
        print(f"   Applied: {profile.applied_at.strftime('%Y-%m-%d %H:%M')}")
        
        if test:
            print(f"   Test Status: {test.status}")
            if test.submitted_at:
                print(f"   Test Submitted: {test.submitted_at.strftime('%Y-%m-%d %H:%M')}")
        
        print("-" * 80)
    
    print(f"\n📊 Total pending: {pending.count()}")

    # Get the first annotator to approve
    if pending.exists():
        annotator = pending.first()
        print(f"\n\n🔄 Approving: {annotator.user.email}")
        
        # Approve test if exists
        test = AnnotationTest.objects.filter(annotator=annotator).order_by('-created_at').first()
        if test and test.status in ['submitted', 'pending', 'in_progress']:
            test.status = 'passed'
            test.accuracy = 100.00
            test.evaluated_at = timezone.now()
            test.feedback = "Test approved by admin"
            test.save()
            print(f"✅ Test marked as passed")
        
        # Approve annotator
        annotator.status = 'approved'
        annotator.approved_at = timezone.now()
        annotator.user.is_active = True
        annotator.user.save()
        annotator.save()
        
        print(f"✅ Annotator approved successfully!")
        print(f"   Email: {annotator.user.email}")
        print(f"   Status: {annotator.status}")
        print(f"   User is_active: {annotator.user.is_active}\n")
