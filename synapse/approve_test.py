# Approve test for annotator
from django.utils import timezone
from annotators.models import AnnotatorProfile, AnnotationTest

email = 'azgmxrk@kemail.uk'
print(f"\nApproving test for: {email}\n")

profile = AnnotatorProfile.objects.get(user__email=email)

# Get all tests for this annotator
tests = AnnotationTest.objects.filter(annotator=profile).order_by('-created_at')

if not tests.exists():
    print("✗ No tests found")
    print("Creating a default approved test...")
    
    # Create a test record
    test = AnnotationTest.objects.create(
        annotator=profile,
        test_type='general',
        status='passed',
        accuracy=100.00,
        evaluated_at=timezone.now(),
        feedback='Test approved by admin',
        submitted_at=timezone.now(),
    )
    print(f"✓ Created and approved test (ID: {test.id})")
else:
    print(f"Found {tests.count()} test(s):")
    
    for test in tests:
        print(f"\n  Test ID: {test.id}")
        print(f"  Status: {test.status}")
        print(f"  Test type: {test.test_type}")
        
        if test.status not in ['passed', 'approved']:
            test.status = 'passed'
            test.accuracy = 100.00
            test.evaluated_at = timezone.now()
            test.feedback = 'Test approved by admin'
            if not test.submitted_at:
                test.submitted_at = timezone.now()
            test.save()
            print(f"  ✓ Approved (set to passed with 100% accuracy)")
        else:
            print(f"  (Already {test.status})")

print(f"\n✓ All tests approved for {email}\n")
