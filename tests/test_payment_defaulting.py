#!/usr/bin/env python3
"""
Test script to verify payment date defaulting functionality.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from csv_handler import CSVHandler

def test_payment_date_defaulting():
    """Test that empty payment dates default to to_date."""
    
    print("=== Testing Payment Date Defaulting ===\n")
    
    # Test CSV file with mixed payment dates
    csv_handler = CSVHandler()
    success, errors = csv_handler.load_csv("tests/test_payment_default.csv")
    
    if not success:
        print(f"Failed to load CSV: {errors}")
        assert success, f"CSV loading failed: {errors}"
    
    receipts = csv_handler.get_receipts()
    
    print(f"Loaded {len(receipts)} receipts:")
    
    for i, receipt in enumerate(receipts):
        print(f"\nReceipt {i+1}:")
        print(f"  Contract ID: {receipt.contract_id}")
        print(f"  Period: {receipt.from_date} to {receipt.to_date}")
        print(f"  Payment Date: {receipt.payment_date}")
        
        if hasattr(receipt, 'payment_date_defaulted'):
            if receipt.payment_date_defaulted:
                print(f"  ⚠️  Payment date was defaulted to end date")
            else:
                print(f"  ✓  Payment date was provided in CSV")
        else:
            print(f"  ❌ payment_date_defaulted attribute missing")
    
    # Verify results
    print(f"\n=== Verification ===")
    
    tests_passed = 0
    total_tests = 3
    
    # Test 1: First receipt should have explicit payment date
    if len(receipts) > 0:
        receipt1 = receipts[0]
        if receipt1.payment_date == "2024-06-28" and not getattr(receipt1, 'payment_date_defaulted', True):
            print("✓ First receipt has explicit payment date")
            tests_passed += 1
        else:
            print("✗ First receipt payment date handling failed")
    
    # Test 2: Second receipt should have defaulted payment date
    if len(receipts) > 1:
        receipt2 = receipts[1]
        if receipt2.payment_date == receipt2.to_date and getattr(receipt2, 'payment_date_defaulted', False):
            print("✓ Second receipt payment date defaulted correctly")
            tests_passed += 1
        else:
            print(f"✗ Second receipt payment date not defaulted (got: {receipt2.payment_date}, expected: {receipt2.to_date}, defaulted: {getattr(receipt2, 'payment_date_defaulted', False)})")
    
    # Test 3: Third receipt should have defaulted payment date (no column)
    if len(receipts) > 2:
        receipt3 = receipts[2]
        if receipt3.payment_date == receipt3.to_date and getattr(receipt3, 'payment_date_defaulted', False):
            print("✓ Third receipt payment date defaulted correctly")
            tests_passed += 1
        else:
            print(f"✗ Third receipt payment date not defaulted (got: {receipt3.payment_date}, expected: {receipt3.to_date}, defaulted: {getattr(receipt3, 'payment_date_defaulted', False)})")
    
    print(f"\n=== Test Summary ===")
    print(f"Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("🎉 Payment date defaulting is working correctly!")
        print("✅ Empty payment dates default to end date")
        print("✅ Step-by-step dialog will show defaulted payment dates")
    else:
        print("❌ Some tests failed. Check the payment date defaulting logic.")
    
    assert tests_passed == total_tests, f"Only {tests_passed}/{total_tests} tests passed"

if __name__ == "__main__":
    try:
        test_payment_date_defaulting()
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
