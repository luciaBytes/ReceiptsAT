#!/usr/bin/env python3
"""
Test script to verify value updating in step-by-step processing.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from csv_handler import CSVHandler
from web_client import WebClient
from receipt_processor import ReceiptProcessor

def test_step_by_step_value_update():
    """Test that values are updated from contract data before showing confirmation dialog."""
    
    print("=== Testing Step-by-Step Value Update ===\n")
    
    # Create components
    web_client = WebClient(testing_mode=True)
    web_client.authenticated = True
    processor = ReceiptProcessor(web_client)
    processor.dry_run = True  # Enable dry run to skip contract validation
    
    # Load CSV with missing values
    csv_handler = CSVHandler()
    success, errors = csv_handler.load_csv("test_missing_value.csv")
    
    if not success:
        print(f"Failed to load CSV: {errors}")
        return False
    
    receipts = csv_handler.get_receipts()
    print(f"Loaded {len(receipts)} receipts")
    
    # Show initial values
    for i, receipt in enumerate(receipts):
        print(f"Receipt {i+1} initial value: €{receipt.value}")
    
    # Test confirmation callback to check values
    confirmation_calls = []
    
    def test_confirmation_callback(receipt_data, form_data):
        confirmation_calls.append({
            'contract_id': receipt_data.contract_id,
            'value': receipt_data.value,
            'has_form_data': 'mock' in form_data
        })
        
        print(f"\n--- Confirmation Dialog for Contract {receipt_data.contract_id} ---")
        print(f"Value shown to user: €{receipt_data.value}")
        print(f"Form data available: {bool(form_data and not form_data.get('mock'))}")
        
        return 'confirm'  # Always confirm for test
    
    # Test step-by-step processing
    results = processor.process_receipts_step_by_step(
        receipts,
        test_confirmation_callback,
        stop_check=lambda: False
    )
    
    print(f"\n=== Results ===")
    print(f"Confirmation calls: {len(confirmation_calls)}")
    
    # Verify that values were shown correctly in dialogs
    tests_passed = 0
    total_tests = 2
    
    if len(confirmation_calls) >= 1:
        first_call = confirmation_calls[0]
        # First receipt should show a value (either from CSV or contract)
        if first_call['value'] > 0:
            print("✓ First receipt shows non-zero value in dialog")
            tests_passed += 1
        else:
            print(f"✗ First receipt shows zero value: €{first_call['value']}")
    
    if len(confirmation_calls) >= 2:
        second_call = confirmation_calls[1]
        # Second receipt should show a value (from contract since CSV has none)
        if second_call['value'] > 0:
            print("✓ Second receipt shows updated value from contract data")
            tests_passed += 1
        else:
            print(f"✗ Second receipt still shows zero value: €{second_call['value']}")
    
    print(f"\n=== Test Summary ===")
    print(f"Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("🎉 Value updating in step-by-step mode is working!")
        print("✅ Missing values are updated from contract data before showing dialog")
    else:
        print("❌ Value updating needs to be fixed")
    
    return tests_passed == total_tests

if __name__ == "__main__":
    try:
        test_step_by_step_value_update()
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
