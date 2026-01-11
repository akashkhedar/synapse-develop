#!/usr/bin/env python
"""Approve specific annotator by email"""
import os
import sys
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path, override=True)
except ImportError:
    pass

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.synapse')

# Setup Django
import django
django.setup()

from django.utils import timezone
from annotators.models import AnnotatorProfile, AnnotationTest

# Annotator email to approve
EMAIL = "azgmxrk@kemail.uk"

print("\n" + "="*80)
print(f"APPROVING ANNOTATOR: {EMAIL}")
print("="*80 + "\n")

try:
    # Find the annotator
    profile = AnnotatorProfile.objects.select_related('user').get(user__email=EMAIL)
    
    print(f"✓ Found annotator: {profile.user.get_full_name() or profile.user.email}")
    print(f"  Current status: {profile.status}")
    print(f"  Email verified: {profile.email_verified}")
    
    # Get their test if they have one
    test = AnnotationTest.objects.filter(annotator=profile).order_by('-created_at').first()
    
    if test:
        print(f"  Test status: {test.status}")
        
        # Approve the test
        if test.status in ['submitted', 'pending', 'in_progress']:
            test.status = 'passed'
            test.accuracy = 100.00
            test.evaluated_at = timezone.now()
            test.feedback = "Test approved by admin"
            test.save(update_fields=['status', 'accuracy', 'evaluated_at', 'feedback'])
            print(f"\n✓ Test marked as passed (100% accuracy)")
        else:
            print(f"  (Test already {test.status})")
    else:
        print(f"  No test found (skipping test approval)")
    
    # Approve the annotator
    if profile.status != 'approved':
        old_status = profile.status
        profile.status = 'approved'
        profile.approved_at = timezone.now()
        profile.user.is_active = True
        profile.user.save(update_fields=['is_active'])
        profile.save(update_fields=['status', 'approved_at'])
        
        print(f"\n✓ ANNOTATOR APPROVED!")
        print(f"  Status changed: {old_status} → approved")
        print(f"  Approved at: {profile.approved_at}")
        print(f"  User is_active: {profile.user.is_active}")
    else:
        print(f"\n⚠ Annotator already approved")
    
    print("\n" + "="*80)
    print("SUCCESS - Annotator can now use the platform")
    print("="*80 + "\n")
    
except AnnotatorProfile.DoesNotExist:
    print(f"✗ ERROR: No annotator found with email: {EMAIL}")
    print("\nSearching for similar emails...\n")
    
    # Show all pending annotators
    pending = AnnotatorProfile.objects.filter(
        status__in=['pending_verification', 'pending_test', 'test_submitted', 'under_review']
    ).select_related('user')
    
    if pending.exists():
        print("Pending annotators:")
        for p in pending:
            print(f"  - {p.user.email} ({p.status})")
    else:
        print("No pending annotators found")
    
    sys.exit(1)

except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
