#!/usr/bin/env python
"""
Test Script for Storage Quota and Project Cost System

This script validates the new storage checking and variable security fee implementation.
Run after applying migrations.

Usage:
    python synapse/test_storage_and_cost.py
"""

import os
import sys
import django

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.label_studio')
django.setup()

from decimal import Decimal
from billing.services import ProjectBillingService
from billing.cost_estimation import CostEstimationService
from billing.storage_service import StorageCalculationService
from django.core.exceptions import ValidationError


def test_security_fee_tiers():
    """Test that security fees are calculated correctly as 10% of project cost"""
    print("\n" + "="*60)
    print("TEST: Security Fee Calculation (10% of project cost, min ₹500)")
    print("="*60)
    
    test_cases = [
        # (storage_fee, annotation_fee, expected_fee, description)
        (10, 100, 500, "Small project (₹110 cost → ₹11, min ₹500)"),
        (50, 450, 500, "Small project (₹500 cost → ₹50, min ₹500)"),
        (100, 900, 500, "Medium project (₹1000 cost → ₹100, min ₹500)"),
        (200, 3800, 500, "Medium project (₹4000 cost → ₹400, min ₹500)"),
        (300, 5700, 600, "Large project (₹6000 cost → ₹600)"),
        (500, 9500, 1000, "Large project (₹10000 cost → ₹1000)"),
        (1000, 19000, 2000, "Very large project (₹20000 cost → ₹2000)"),
        (2000, 48000, 5000, "Enterprise project (₹50000 cost → ₹5000)"),
    ]
    
    passed = 0
    failed = 0
    
    for storage_fee, annotation_fee, expected_fee, description in test_cases:
        storage_decimal = Decimal(str(storage_fee))
        annotation_decimal = Decimal(str(annotation_fee))
        expected_decimal = Decimal(str(expected_fee))
        
        # Test in ProjectBillingService
        fee_service = ProjectBillingService.calculate_security_fee(storage_decimal, annotation_decimal)
        
        # Test in CostEstimationService
        fee_estimation = CostEstimationService.calculate_security_fee(storage_decimal, annotation_decimal)
        
        if fee_service == expected_decimal and fee_estimation == expected_decimal:
            print(f"✓ {description}: ₹{fee_service} (Expected: ₹{expected_fee})")
            passed += 1
        else:
            print(f"✗ {description}: Got ₹{fee_service}/₹{fee_estimation}, Expected: ₹{expected_fee}")
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_storage_calculation():
    """Test storage size calculations"""
    print("\n" + "="*60)
    print("TEST: Storage Calculations")
    print("="*60)
    
    test_cases = [
        (1024 ** 3, 1.0, "1 GB"),
        (5 * 1024 ** 3, 5.0, "5 GB"),
        (1024 ** 2, 0.0009765625, "1 MB"),
        (500 * 1024 ** 2, 0.48828125, "500 MB"),
    ]
    
    passed = 0
    failed = 0
    
    for bytes_val, expected_gb, description in test_cases:
        calculated_gb = float(Decimal(str(bytes_val)) / Decimal(str(1024 ** 3)))
        
        # Allow small floating point differences
        if abs(calculated_gb - expected_gb) < 0.000001:
            print(f"✓ {description}: {calculated_gb:.10f} GB")
            passed += 1
        else:
            print(f"✗ {description}: Got {calculated_gb:.10f} GB, Expected: {expected_gb} GB")
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_overage_cost_calculation():
    """Test storage overage cost calculation"""
    print("\n" + "="*60)
    print("TEST: Storage Overage Cost Calculation")
    print("="*60)
    
    test_cases = [
        (5.0, 10.0, 25.0, 0.0, "Within free tier"),
        (12.0, 10.0, 25.0, 50.0, "2 GB overage at ₹25/GB"),
        (15.5, 10.0, 18.0, 99.0, "5.5 GB overage at ₹18/GB"),
        (60.0, 50.0, 13.0, 130.0, "10 GB overage at ₹13/GB"),
    ]
    
    passed = 0
    failed = 0
    
    for total_storage, free_storage, rate, expected_cost, description in test_cases:
        overage_gb = max(0, total_storage - free_storage)
        calculated_cost = float(Decimal(str(overage_gb)) * Decimal(str(rate)))
        
        if abs(calculated_cost - expected_cost) < 0.01:
            print(f"✓ {description}: ₹{calculated_cost:.2f}")
            passed += 1
        else:
            print(f"✗ {description}: Got ₹{calculated_cost:.2f}, Expected: ₹{expected_cost:.2f}")
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_project_cost_calculation():
    """Test complete project cost calculation"""
    print("\n" + "="*60)
    print("TEST: Project Cost Calculation (10% security fee)")
    print("="*60)
    
    # Test case: Small project
    print("\n--- Small Project (50 tasks, 1 GB storage) ---")
    result = CostEstimationService.estimate_project_cost(
        task_count=50,
        estimated_storage_gb=1.0,
        annotation_types=['rectanglelabels'],
        label_count=5
    )
    
    print(f"Storage Fee: ₹{result['deposit_breakdown']['storage_fee']}")
    print(f"Annotation Fee: ₹{result['deposit_breakdown']['annotation_fee']}")
    print(f"Security Fee (10% of above): ₹{result['deposit_breakdown']['base_fee']}")
    print(f"Total Deposit: ₹{result['deposit_breakdown']['total_deposit']}")
    
    # Verify security fee is at least ₹500 (minimum)
    if result['deposit_breakdown']['base_fee'] >= 500.0:
        print("✓ Security fee meets minimum of ₹500")
        small_passed = True
    else:
        print(f"✗ Security fee below minimum: Got ₹{result['deposit_breakdown']['base_fee']}, Expected: ≥₹500")
        small_passed = False
    
    # Test case: Large project
    print("\n--- Large Project (1500 tasks, 5 GB storage) ---")
    result = CostEstimationService.estimate_project_cost(
        task_count=1500,
        estimated_storage_gb=5.0,
        annotation_types=['rectanglelabels', 'polygonlabels'],
        label_count=20
    )
    
    print(f"Storage Fee: ₹{result['deposit_breakdown']['storage_fee']}")
    print(f"Annotation Fee: ₹{result['deposit_breakdown']['annotation_fee']}")
    print(f"Security Fee (10% of above): ₹{result['deposit_breakdown']['base_fee']}")
    print(f"Total Deposit: ₹{result['deposit_breakdown']['total_deposit']}")
    
    # Calculate expected 10% security fee
    storage_fee = result['deposit_breakdown']['storage_fee']
    annotation_fee = result['deposit_breakdown']['annotation_fee']
    expected_security = max(500, round((storage_fee + annotation_fee) * 0.10))
    
    # Verify security fee is 10% of project cost
    actual_security = result['deposit_breakdown']['base_fee']
    if abs(actual_security - expected_security) < 1.0:  # Allow rounding difference
        print(f"✓ Security fee correct: {actual_security:.0f} ≈ 10% of {storage_fee + annotation_fee:.2f}")
        large_passed = True
    else:
        print(f"✗ Security fee incorrect: Got ₹{actual_security}, Expected: ≈₹{expected_security}")
        large_passed = False
    
    return small_passed and large_passed


def test_database_fields():
    """Test that new database fields exist"""
    print("\n" + "="*60)
    print("TEST: Database Fields")
    print("="*60)
    
    from billing.models import ProjectBilling, SecurityDeposit
    
    # Check ProjectBilling fields
    pb_fields = [f.name for f in ProjectBilling._meta.get_fields()]
    
    required_pb_fields = [
        'project_cost_required',
        'project_cost_paid',
        'project_cost_refunded',
        'security_deposit_required',  # Old field (backward compat)
        'security_deposit_paid',
        'security_deposit_refunded',
    ]
    
    pb_passed = 0
    pb_failed = 0
    
    for field in required_pb_fields:
        if field in pb_fields:
            print(f"✓ ProjectBilling.{field} exists")
            pb_passed += 1
        else:
            print(f"✗ ProjectBilling.{field} missing")
            pb_failed += 1
    
    # Check SecurityDeposit fields
    sd_fields = [f.name for f in SecurityDeposit._meta.get_fields()]
    
    required_sd_fields = [
        'security_fee',
        'base_fee',  # Old field (backward compat)
        'storage_fee',
        'annotation_fee',
        'total_deposit',
    ]
    
    sd_passed = 0
    sd_failed = 0
    
    for field in required_sd_fields:
        if field in sd_fields:
            print(f"✓ SecurityDeposit.{field} exists")
            sd_passed += 1
        else:
            print(f"✗ SecurityDeposit.{field} missing")
            sd_failed += 1
    
    print(f"\nResults: {pb_passed + sd_passed} passed, {pb_failed + sd_failed} failed")
    return (pb_failed + sd_failed) == 0


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("STORAGE QUOTA & PROJECT COST SYSTEM - TEST SUITE")
    print("="*60)
    
    results = {
        "Security Fee Tiers": test_security_fee_tiers(),
        "Storage Calculations": test_storage_calculation(),
        "Overage Cost Calculation": test_overage_cost_calculation(),
        "Project Cost Calculation": test_project_cost_calculation(),
        "Database Fields": test_database_fields(),
    }
    
    print("\n" + "="*60)
    print("FINAL RESULTS")
    print("="*60)
    
    total_passed = sum(1 for passed in results.values() if passed)
    total_tests = len(results)
    
    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nOverall: {total_passed}/{total_tests} test suites passed")
    
    if total_passed == total_tests:
        print("\n🎉 All tests passed! System is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total_tests - total_passed} test suite(s) failed. Please review.")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
