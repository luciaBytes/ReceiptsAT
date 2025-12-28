#!/usr/bin/env python3
"""
Test script to verify value updating in step-by-step processing.
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from csv_handler import CSVHandler
from web_client import WebClient
from receipt_processor import ReceiptProcessor

@patch.object(WebClient, 'validate_csv_contracts')
@patch.object(WebClient, 'get_contract_rent_value')
@patch.object(WebClient, 'is_authenticated')
def test_step_by_step_value_update(mock_is_authenticated, mock_get_rent_value, mock_validate_contracts):
    """Test that values are updated from contract data before showing confirmation dialog."""
    
    print("=== Testing Step-by-Step Value Update ===\n")
    
    # Mock authentication
    mock_is_authenticated.return_value = True
    
    # Mock contract validation to return success with valid contracts
    mock_validate_contracts.return_value = {
        'success': True,
        'portal_contracts_count': 2,
        'csv_contracts_count': 2,
        'valid_contracts': ['12345', '67890'],
        'valid_contracts_data': [],
        'invalid_contracts': [],
        'missing_from_csv': [],
        'validation_errors': []
    }
    
    # Mock rent value retrieval to return test values
    def mock_rent_value(contract_id):
        if contract_id == "12345":
            return True, 150.0  # Return successful rent value
        elif contract_id == "67890":
            return True, 250.0  # Return successful rent value
        else:
            return False, 0.0
    
    mock_get_rent_value.side_effect = mock_rent_value
    
    # Create components
    web_client = WebClient()
    web_client.authenticated = True
    processor = ReceiptProcessor(web_client)
    processor.dry_run = True  # Enable dry run to skip contract validation
    
    # Load CSV with missing values
    csv_handler = CSVHandler()
    success, errors = csv_handler.load_csv("tests/test_missing_value.csv")
    
    if not success:
        print(f"Failed to load CSV: {errors}")
        assert success, f"CSV loading failed: {errors}"
    
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
    
    # Verify that values were properly updated from contract data
    tests_passed = 0
    total_tests = 2
    
    if len(confirmation_calls) >= 1:
        first_call = confirmation_calls[0]
        # First receipt should show a realistic value (updated from contract data)
        if first_call['value'] > 0:
            print(f"✓ First receipt correctly shows updated value from contract: €{first_call['value']}")
            tests_passed += 1
        else:
            print(f"✗ First receipt shows missing/zero value: €{first_call['value']}")
    
    if len(confirmation_calls) >= 2:
        second_call = confirmation_calls[1]
        # Second receipt should also show a realistic value (updated from contract data)
        if second_call['value'] > 0:
            print(f"✓ Second receipt correctly shows updated value from contract: €{second_call['value']}")
            tests_passed += 1
        else:
            print(f"✗ Second receipt shows missing/zero value: €{second_call['value']}")
    
    print(f"\n=== Test Summary ===")
    print(f"Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("✅ Value updating from contract data is working perfectly!")
        print("✅ Missing values (-1.0) are correctly updated from contract data before showing dialog")
    else:
        print("❌ Value updating from contract data needs to be fixed")
    
    assert tests_passed == total_tests, f"Only {tests_passed}/{total_tests} tests passed"

if __name__ == "__main__":
    try:
        test_step_by_step_value_update()
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
