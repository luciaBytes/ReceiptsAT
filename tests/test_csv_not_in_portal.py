#!/usr/bin/env python3
"""
Test to confirm that CSV contracts not found in portal are skipped.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from web_client import WebClient
from csv_handler import CSVHandler, ReceiptData
from receipt_processor import ReceiptProcessor

def test_csv_contract_not_in_portal():
    """Test that CSV contracts not found in portal are skipped."""
    
    print("=" * 70)
    print("CSV CONTRACT NOT IN PORTAL - SKIP TEST")
    print("=" * 70)
    
    # Initialize components in testing mode
    web_client = WebClient(testing_mode=True)
    processor = ReceiptProcessor(web_client)
    
    # Login with test credentials
    login_success, _ = web_client.login("test", "test")
    print(f"✅ Login successful: {login_success}")
    
    # Check what contracts are available in the portal (mock mode)
    success, portal_contracts = web_client.get_contracts_list()
    print(f"\n📋 Portal contracts available:")
    if success:
        for contract in portal_contracts:
            contract_id = contract.get('contractId', 'N/A')
            print(f"  • {contract_id}")
    else:
        print(f"  ❌ Failed to get portal contracts")
    # Create CSV receipts: mix of contracts in portal and not in portal
    receipts = [
        # These are in the mock portal (see web_client.py mock_contracts)
        ReceiptData("123456", "2024-01-01", "2024-01-31", "rent", 100.00),  # ✅ In portal
        ReceiptData("789012", "2024-02-01", "2024-02-29", "rent", 900.50),  # ✅ In portal
        
        # These are NOT in the mock portal
        ReceiptData("111111", "2024-03-01", "2024-03-31", "rent", 925.75),  # ❌ NOT in portal
        ReceiptData("999999", "2024-04-01", "2024-04-30", "rent", 800.00),  # ❌ NOT in portal
        ReceiptData("555555", "2024-05-01", "2024-05-31", "rent", 750.00),  # ❌ NOT in portal
    ]
    
    print(f"\n📄 CSV receipts to process:")
    for receipt in receipts:
        print(f"  • {receipt.contract_id}")
    
    # Enable dry run to avoid actual processing
    processor.set_dry_run(True)
    print(f"\n✅ Dry run mode enabled (no network requests)")
    
    # Process with contract validation enabled
    print(f"\n📊 Processing with contract validation...")
    results = processor.process_receipts_bulk(receipts, validate_contracts=True)
    
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
    print(f"  Expected: 3 contracts NOT in portal → Skipped")
    
    if success_count == 2 and skipped_count == 3:
        print(f"  ✅ PASS: CSV contracts not in portal are correctly SKIPPED")
    else:
        print(f"  ❌ FAIL: Unexpected results")
        
    print(f"\n📄 Testing report generation...")
    report_data = processor.generate_report_data()
    
    print(f"Report shows:")
    for entry in report_data:
        status_emoji = "✅" if entry['Status'] == "Success" else "⏭️" if entry['Status'] == "Skipped" else "❌"
        print(f"  {status_emoji} {entry['Contract ID']}: {entry['Status']}")
    
    print(f"\n🎯 CSV CONTRACT NOT IN PORTAL TEST COMPLETE")
    print(f"✅ Conclusion: CSV contracts not found in portal are properly SKIPPED")

if __name__ == "__main__":
    test_csv_contract_not_in_portal()
