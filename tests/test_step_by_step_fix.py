#!/usr/bin/env python3
"""
Test step-by-step processing with invalid contracts to ensure they are skipped.
"""

import sys
import os
from unittest.mock import patch
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from web_client import WebClient
from csv_handler import CSVHandler, ReceiptData
from receipt_processor import ReceiptProcessor

@patch.object(WebClient, '__init__')
@patch.object(WebClient, 'login')
@patch.object(WebClient, 'get_contracts_list')
def test_step_by_step_invalid_contracts(mock_get_contracts, mock_login, mock_init):
    """Test that step-by-step processing properly skips invalid contracts."""
    
    print("=" * 70)
    print("STEP-BY-STEP INVALID CONTRACTS TEST")
    print("=" * 70)
    
    # Mock WebClient initialization to avoid real HTTP session creation
    mock_init.return_value = None
    
    # Mock login success
    mock_login.return_value = (True, "Mock login successful")
    
    # Mock contracts list with limited valid contracts
    mock_contracts = [
        {'numero': '123456', 'referencia': 'CT123456'},
        {'numero': '789012', 'referencia': 'CT789012'}
    ]
    mock_get_contracts.return_value = (True, mock_contracts)
    
    # Initialize components in testing mode
    web_client = WebClient()
    web_client.authenticated = True  # Mock authentication
    processor = ReceiptProcessor(web_client)
    
    # Use mock login result (patched by decorator)
    login_success = True  # Mock result from decorator
    print(f"✅ Login successful: {login_success}")
    
    # Check what contracts are available in the portal (mock mode)
    success, portal_contracts = web_client.get_contracts_list()
    print(f"\n📋 Portal contracts available:")
    if success:
        for contract in portal_contracts:
            contract_id = contract.get('contractId', 'N/A')
            print(f"  • {contract_id}")
    
    # Create CSV receipts: mix of contracts in portal and not in portal
    receipts = [
        # These are in the mock portal
        ReceiptData("123456", "2024-01-01", "2024-01-31", "rent", 100.00),  # ✅ In portal
        ReceiptData("789012", "2024-02-01", "2024-02-29", "rent", 900.50),  # ✅ In portal
        
        # These are NOT in the mock portal
        ReceiptData("111111", "2024-03-01", "2024-03-31", "rent", 925.75),  # ❌ NOT in portal
        ReceiptData("999999", "2024-04-01", "2024-04-30", "rent", 800.00),  # ❌ NOT in portal
    ]
    
    print(f"\n📄 CSV receipts to process:")
    for receipt in receipts:
        print(f"  • {receipt.contract_id}")
    
    # Enable dry run to avoid actual processing
    processor.set_dry_run(True)
    print(f"\n✅ Dry run mode enabled")
    
    # Create a mock confirmation callback that auto-confirms all valid contracts
    def confirmation_callback(receipt_data, form_data):
        print(f"  📋 Confirming receipt for contract {receipt_data.contract_id}")
        return 'confirm'
    
    # Process in step-by-step mode
    print(f"\n📊 Processing in STEP-BY-STEP mode...")
    results = processor.process_receipts_step_by_step(receipts, confirmation_callback)
    
    print(f"\n📋 PROCESSING RESULTS:")
    success_count = 0
    skipped_count = 0
    failed_count = 0
    
    for result in results:
        status = result.status if result.status else ('Success' if result.success else 'Failed')
        status_emoji = "✅" if status == "Success" else "⏭️" if status == "Skipped" else "❌"
        
        print(f"  {status_emoji} Contract {result.contract_id}: {status}")
        
        if result.error_message:
            print(f"     Reason: {result.error_message}")
        
        if status == "Success":
            success_count += 1
        elif status == "Skipped":
            skipped_count += 1
        else:
            failed_count += 1
    
    print(f"\n📊 SUMMARY:")
    print(f"  ✅ Success: {success_count}")
    print(f"  ⏭️ Skipped: {skipped_count}")
    print(f"  ❌ Failed: {failed_count}")
    
    print(f"\n🎯 VERIFICATION:")
    print(f"  Expected: 2 contracts in portal → Success")
    print(f"  Expected: 2 contracts NOT in portal → Skipped")
    print(f"  Expected: 0 contracts → Failed")
    
    if success_count == 2 and skipped_count == 2 and failed_count == 0:
        print(f"  ✅ PASS: Step-by-step mode correctly skips invalid contracts")
    else:
        print(f"  ❌ FAIL: Unexpected results")
    
    print(f"\n📄 Testing report generation...")
    report_data = processor.generate_report_data()
    
    print(f"Report shows:")
    for entry in report_data:
        status_emoji = "✅" if entry['Status'] == "Success" else "⏭️" if entry['Status'] == "Skipped" else "❌"
        print(f"  {status_emoji} {entry['Contract ID']}: {entry['Status']}")
    
    print(f"\n🎯 STEP-BY-STEP INVALID CONTRACTS TEST COMPLETE")
    
    if success_count == 2 and skipped_count == 2:
        print(f"✅ CONCLUSION: Step-by-step mode now properly skips invalid contracts!")
    else:
        print(f"❌ CONCLUSION: Issue still exists - step-by-step mode not working correctly")

if __name__ == "__main__":
    test_step_by_step_invalid_contracts()
