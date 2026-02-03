
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.synapse')
django.setup()

from users.models import User
from annotators.models import ExpertProfile
from django.db import connection

print("Creating ExpertProfile for expert@gmail.com...")
print("=" * 60)

try:
    user = User.objects.get(email="expert@gmail.com")
    
    # Try to create the expert profile using raw SQL to handle the cached_availability_score field
    with connection.cursor() as cursor:
        # Check if profile exists
        cursor.execute("SELECT id FROM expert_profile WHERE user_id = %s", [user.id])
        result = cursor.fetchone()
        
        if result:
            print(f"✓ ExpertProfile already exists for {user.email}")
        else:
            # Insert with all required fields including cached_availability_score and bank fields
            cursor.execute("""
                INSERT INTO expert_profile (
                    user_id, status, expertise_level, expertise_areas,
                    total_reviews_completed, total_approvals, total_rejections, total_corrections,
                    average_review_time, correction_accuracy, consistency_score,
                    total_earned, pending_payout, available_balance, total_withdrawn,
                    minimum_payout, payment_method, bank_details,
                    bank_name, account_number, ifsc_code, account_holder_name, upi_id,
                    total_payouts_count, total_payouts_amount,
                    max_reviews_per_day, current_workload, assigned_at,
                    cached_availability_score
                ) VALUES (
                    %s, 'active', 'senior_expert', '[]',
                    0, 0, 0, 0,
                    0, 0.0, 0.0,
                    0.0, 0.0, 0.0, 0.0,
                    100.0, 'bank_transfer', '{}',
                    '', '', '', '', '',
                    0, 0.0,
                    50, 0, NOW(),
                    100.0
                )
            """, [user.id])
            
            print(f"✓ Created ExpertProfile for {user.email}")
            print(f"  - Status: active")
            print(f"  - Expertise Level: senior_expert")
            print(f"  - Cached Availability Score: 100.0")
        
except User.DoesNotExist:
    print("✗ User expert@gmail.com not found")
except Exception as e:
    print(f"✗ Error: {e}")

print("=" * 60)
print("Complete.")
