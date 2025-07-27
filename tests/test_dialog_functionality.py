#!/usr/bin/env python3
"""
Test script to verify step-by-step processing dialog functionality.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from csv_handler import CSVHandler, ReceiptData
from web_client import WebClient
from receipt_processor import ReceiptProcessor

def test_step_by_step_dialog():
    """Test the step-by-step processing with simulated dialogs."""
    
    print("=== Testing Step-by-Step Dialog Functionality ===\n")
    
    # Create components
    web_client = WebClient(testing_mode=True)
    web_client.authenticated = True
    processor = ReceiptProcessor(web_client)
    
    # Create sample receipt data
    receipts = [
        ReceiptData(
            contract_id="123456",
            from_date="2024-07-01",
            to_date="2024-07-31", 
            payment_date="2024-07-28",
            receipt_type="rent",
            value=850.0
        ),
        ReceiptData(
            contract_id="789012",
            from_date="2024-07-01",
            to_date="2024-07-31",
            payment_date="2024-07-28", 
            receipt_type="rent",
            value=900.0
        )
    ]
    
    print(f"Created {len(receipts)} test receipts")
    
    # Test confirmation callback
    confirmation_calls = []
    
    def test_confirmation_callback(receipt_data, form_data):
        confirmation_calls.append({
            'contract_id': receipt_data.contract_id,
            'value': receipt_data.value
        })
        
        print(f"\n--- Confirmation Dialog for Contract {receipt_data.contract_id} ---")
        print(f"Receipt Details:")
        print(f"  Contract ID: {receipt_data.contract_id}")
        print(f"  Period: {receipt_data.from_date} to {receipt_data.to_date}")
        print(f"  Payment Date: {receipt_data.payment_date}")
        print(f"  Type: {receipt_data.receipt_type}")
        print(f"  Value: €{receipt_data.value}")
        
        if form_data:
            print(f"\nContract Information:")
            if 'locatarios' in form_data:
                print(f"  Tenants: {len(form_data['locatarios'])}")
                for i, tenant in enumerate(form_data['locatarios']):
                    print(f"    {i+1}. {tenant.get('nome', 'Unknown')} (NIF: {tenant.get('nif', 'Unknown')}) - {tenant.get('quota', 0)}%")
            
            if 'locadores' in form_data:
                print(f"  Landlords: {len(form_data['locadores'])}")
                for i, landlord in enumerate(form_data['locadores']):
                    print(f"    {i+1}. {landlord.get('nome', 'Unknown')} (NIF: {landlord.get('nif', 'Unknown')}) - {landlord.get('quota', 0)}%")
        
        print(f"\nDialog would show: [Confirm] [Skip] [Cancel] buttons")
        
        # Simulate user choices: confirm first, skip second
        if receipt_data.contract_id == "123456":
            print("Simulating user click: CONFIRM")
            return 'confirm'
        else:
            print("Simulating user click: SKIP")
            return 'skip'
    
    # Test processing
    print("\n=== Starting Step-by-Step Processing ===")
    
    results = processor.process_receipts_step_by_step(
        receipts,
        test_confirmation_callback,
        stop_check=lambda: False  # Don't stop
    )
    
    print(f"\n=== Processing Results ===")
    print(f"Confirmation dialogs shown: {len(confirmation_calls)}")
    print(f"Processing results: {len(results)}")
    
    for i, result in enumerate(results):
        print(f"\nResult {i+1}:")
        print(f"  Contract: {result.contract_id}")
        print(f"  Success: {result.success}")
        print(f"  Status: {result.status}")
        print(f"  Message: {result.error_message or result.status}")
    
    # Verify behavior
    print(f"\n=== Verification ===")
    
    tests_passed = 0
    total_tests = 4
    
    if len(confirmation_calls) == 2:
        print("✓ Confirmation dialog called for each receipt")
        tests_passed += 1
    else:
        print(f"✗ Expected 2 confirmation calls, got {len(confirmation_calls)}")
    
    if len(results) == 2:
        print("✓ Got results for all receipts")
        tests_passed += 1
    else:
        print(f"✗ Expected 2 results, got {len(results)}")
    
    confirmed_result = next((r for r in results if r.contract_id == "123456"), None)
    if confirmed_result and confirmed_result.success:
        print("✓ Confirmed receipt was processed successfully")
        tests_passed += 1
    else:
        print("✗ Confirmed receipt was not processed correctly")
    
    skipped_result = next((r for r in results if r.contract_id == "789012"), None)
    if skipped_result and not skipped_result.success and skipped_result.status == "Skipped":
        print("✓ Skipped receipt was marked as skipped")
        tests_passed += 1
    else:
        print("✗ Skipped receipt was not handled correctly")
    
    print(f"\n=== Test Summary ===")
    print(f"Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! Step-by-step processing is working correctly.")
        print("\nIn the GUI:")
        print("- Each contract will show a confirmation dialog")
        print("- Dialog shows receipt and contract details")
        print("- User can Confirm, Skip, or Cancel processing")
        print("- Processing stops between each contract for user input")
    else:
        print("❌ Some tests failed. Check the step-by-step implementation.")
    
    return tests_passed == total_tests

if __name__ == "__main__":
    test_step_by_step_dialog()
