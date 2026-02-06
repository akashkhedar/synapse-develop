"""
Test Script 1: User Account Setup
Creates all test accounts needed for platform testing.

Run with:
    python manage.py shell < tests/integration/test_01_user_setup.py
Or:
    python manage.py runscript tests.integration.test_01_user_setup
"""

import os
import sys

# Ensure Django is set up
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.synapse')

import django
django.setup()

from django.contrib.auth import get_user_model
from django.db import transaction
from organizations.models import Organization, OrganizationMember
from annotators.models import (
    AnnotatorProfile, ExpertProfile, ExpertiseCategory, 
    ExpertiseSpecialization, AnnotatorExpertise, ExpertExpertise
)

User = get_user_model()

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def log_success(msg):
    print(f"{GREEN}✓ {msg}{RESET}")

def log_error(msg):
    print(f"{RED}✗ {msg}{RESET}")

def log_info(msg):
    print(f"{BLUE}ℹ {msg}{RESET}")

def log_section(msg):
    print(f"\n{YELLOW}{'='*60}{RESET}")
    print(f"{YELLOW}{msg}{RESET}")
    print(f"{YELLOW}{'='*60}{RESET}")


# Test account configurations
TEST_ACCOUNTS = {
    'admin': {
        'email': 'admin@test.com',
        'password': 'TestAdmin123!',
        'first_name': 'Admin',
        'last_name': 'User',
        'is_superuser': True,
        'is_staff': True,
    },
    'annotators': [
        {'email': 'annotator1@test.com', 'first_name': 'Alice', 'last_name': 'Annotator', 'expertise': 'computer-vision'},
        {'email': 'annotator2@test.com', 'first_name': 'Bob', 'last_name': 'Annotator', 'expertise': 'computer-vision'},
        {'email': 'annotator3@test.com', 'first_name': 'Carol', 'last_name': 'Annotator', 'expertise': 'computer-vision'},
        {'email': 'annotator4@test.com', 'first_name': 'Dave', 'last_name': 'Annotator', 'expertise': 'natural-language-processing'},
        {'email': 'annotator5@test.com', 'first_name': 'Eve', 'last_name': 'Annotator', 'expertise': 'natural-language-processing'},
    ],
    'experts': [
        {'email': 'expert1@test.com', 'first_name': 'Expert', 'last_name': 'One', 'expertise': 'computer-vision'},
        {'email': 'expert2@test.com', 'first_name': 'Expert', 'last_name': 'Two', 'expertise': 'natural-language-processing'},
    ],
}

DEFAULT_PASSWORD = 'TestPassword123!'


@transaction.atomic
def create_admin_user():
    """Create admin/superuser account"""
    log_section("Phase 1.1: Creating Admin Account")
    
    admin_config = TEST_ACCOUNTS['admin']
    
    user, created = User.objects.get_or_create(
        email=admin_config['email'],
        defaults={
            'username': admin_config['email'],
            'first_name': admin_config['first_name'],
            'last_name': admin_config['last_name'],
            'is_superuser': admin_config['is_superuser'],
            'is_staff': admin_config['is_staff'],
            'is_active': True,
        }
    )
    
    if created:
        user.set_password(admin_config['password'])
        user.save()
        log_success(f"Created admin: {admin_config['email']}")
    else:
        log_info(f"Admin already exists: {admin_config['email']}")
    
    return user


@transaction.atomic
def create_organization(admin_user):
    """Create test organization"""
    log_section("Phase 1.1: Creating Organization")
    
    org, created = Organization.objects.get_or_create(
        title='Test Organization',
        defaults={
            'created_by': admin_user,
        }
    )
    
    if created:
        # Add admin as organization member
        OrganizationMember.objects.get_or_create(
            organization=org,
            user=admin_user,
            defaults={'role': 'owner'}
        )
        log_success(f"Created organization: {org.title}")
    else:
        log_info(f"Organization already exists: {org.title}")
    
    return org


@transaction.atomic
def create_annotator_accounts(organization):
    """Create annotator accounts with profiles"""
    log_section("Phase 1.2: Creating Annotator Accounts")
    
    annotators = []
    
    for config in TEST_ACCOUNTS['annotators']:
        # Create user
        user, created = User.objects.get_or_create(
            email=config['email'],
            defaults={
                'username': config['email'],
                'first_name': config['first_name'],
                'last_name': config['last_name'],
                'is_active': True,
            }
        )
        
        if created:
            user.set_password(DEFAULT_PASSWORD)
            user.save()
            log_success(f"Created user: {config['email']}")
        else:
            log_info(f"User exists: {config['email']}")
        
        # Create annotator profile
        profile, profile_created = AnnotatorProfile.objects.get_or_create(
            user=user,
            defaults={
                'status': 'approved',  # Use status field, not is_approved
                'is_active_for_assignments': True,
            }
        )
        
        if profile_created:
            log_success(f"Created annotator profile for: {config['email']}")
        
        # Apply for expertise
        expertise_slug = config['expertise']
        try:
            category = ExpertiseCategory.objects.get(slug=expertise_slug)
            
            expertise, exp_created = AnnotatorExpertise.objects.get_or_create(
                annotator=profile,
                category=category,
                defaults={
                    'status': 'verified',  # Auto-verify for testing
                    'self_rating': 7,  # Use self_rating (1-10 scale)
                }
            )
            
            if exp_created:
                log_success(f"Assigned {expertise_slug} expertise to {config['email']}")
            else:
                # Update to verified if pending
                if expertise.status != 'verified':
                    expertise.status = 'verified'
                    expertise.save()
                    log_success(f"Verified expertise for {config['email']}")
                    
        except ExpertiseCategory.DoesNotExist:
            log_error(f"Expertise category not found: {expertise_slug}")
        
        annotators.append({'user': user, 'profile': profile, 'config': config})
    
    return annotators


@transaction.atomic
def create_expert_accounts(organization):
    """Create expert accounts with profiles"""
    log_section("Phase 1.3: Creating Expert Accounts")
    
    experts = []
    
    for config in TEST_ACCOUNTS['experts']:
        # Create user
        user, created = User.objects.get_or_create(
            email=config['email'],
            defaults={
                'username': config['email'],
                'first_name': config['first_name'],
                'last_name': config['last_name'],
                'is_active': True,
            }
        )
        
        if created:
            user.set_password(DEFAULT_PASSWORD)
            user.save()
            log_success(f"Created user: {config['email']}")
        else:
            log_info(f"User exists: {config['email']}")
        
        # Create expert profile with raw SQL to handle cached_availability_score
        from django.db import connection
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM expert_profile WHERE user_id = %s", [user.id])
            result = cursor.fetchone()
            
            if result:
                log_info(f"Expert profile exists for: {config['email']}")
                profile = ExpertProfile.objects.get(user=user)
                profile_created = False
            else:
                cursor.execute("""
                    INSERT INTO expert_profile (
                        user_id, status, expertise_areas,
                        total_reviews_completed, total_approvals, total_rejections, total_corrections,
                        average_review_time, correction_accuracy, consistency_score,
                        total_earned, pending_payout, available_balance, total_withdrawn,
                        minimum_payout, payment_method, bank_details,
                        bank_name, account_number, ifsc_code, account_holder_name, upi_id,
                        total_payouts_count, total_payouts_amount,
                        max_concurrent_reviews, current_workload, assigned_at,
                        is_active_for_assignments, cached_availability_score
                    ) VALUES (
                        %s, 'active', '[]',
                        0, 0, 0, 0,
                        0, 0.0, 0.0,
                        0.0, 0.0, 0.0, 0.0,
                        100.0, 'bank_transfer', '{}',
                        '', '', '', '', '',
                        0, 0.0,
                        50, 0, NOW(),
                        TRUE, 100.0
                    )
                """, [user.id])
                profile = ExpertProfile.objects.get(user=user)
                profile_created = True
                log_success(f"Created expert profile for: {config['email']}")
        
        # Assign expertise
        expertise_slug = config['expertise']
        try:
            category = ExpertiseCategory.objects.get(slug=expertise_slug)
            
            expertise, exp_created = ExpertExpertise.objects.get_or_create(
                expert=profile,
                category=category,
                defaults={
                    'status': 'active',
                }
            )
            
            if exp_created:
                log_success(f"Assigned {expertise_slug} expertise to {config['email']}")
                    
        except ExpertiseCategory.DoesNotExist:
            log_error(f"Expertise category not found: {expertise_slug}")
        
        experts.append({'user': user, 'profile': profile, 'config': config})
    
    return experts


def verify_expertise_categories():
    """Verify expertise categories exist"""
    log_section("Verifying Expertise Categories")
    
    required_categories = ['computer-vision', 'natural-language-processing', 'audiospeech-processing']
    
    for slug in required_categories:
        try:
            cat = ExpertiseCategory.objects.get(slug=slug)
            log_success(f"Found category: {cat.name} ({slug})")
        except ExpertiseCategory.DoesNotExist:
            log_error(f"Missing category: {slug} - Run expertise migration first!")
            return False
    
    return True


def print_summary(admin, annotators, experts):
    """Print summary of created accounts"""
    log_section("Test Accounts Summary")
    
    print(f"\n{'Email':<30} {'Role':<15} {'Expertise':<25} {'Password'}")
    print("-" * 90)
    
    admin_config = TEST_ACCOUNTS['admin']
    print(f"{admin_config['email']:<30} {'Admin':<15} {'-':<25} {admin_config['password']}")
    
    for ann in annotators:
        print(f"{ann['config']['email']:<30} {'Annotator':<15} {ann['config']['expertise']:<25} {DEFAULT_PASSWORD}")
    
    for exp in experts:
        print(f"{exp['config']['email']:<30} {'Expert':<15} {exp['config']['expertise']:<25} {DEFAULT_PASSWORD}")
    
    print("\n")


def run():
    """Main test execution"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}       SYNAPSE PLATFORM - USER SETUP TEST{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    # Verify prerequisites
    if not verify_expertise_categories():
        log_error("Prerequisites not met. Aborting.")
        return False
    
    # Create accounts
    admin = create_admin_user()
    org = create_organization(admin)
    annotators = create_annotator_accounts(org)
    experts = create_expert_accounts(org)
    
    # Print summary
    print_summary(admin, annotators, experts)
    
    log_section("User Setup Complete!")
    log_success(f"Created 1 admin, {len(annotators)} annotators, {len(experts)} experts")
    
    return True


if __name__ == '__main__':
    run()
elif not os.environ.get('SYNAPSE_TEST_IMPORT'):
    # Auto-run when loaded via Django shell (not when imported)
    run()
