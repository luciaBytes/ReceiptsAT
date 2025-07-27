#!/usr/bin/env python3
"""
Test the corrected status reporting for skipped invalid contracts.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from web_client import WebClient
from csv_handler import CSVHandler, ReceiptData
from receipt_processor import ReceiptProcessor

def test_status_reporting():
    """Test that invalid contracts are reported as 'Skipped' not 'Failed'."""
    
    print("=" * 60)
    print("STATUS REPORTING TEST")
    print("=" * 60)
    
    # Initialize components in testing mode
    web_client = WebClient(testing_mode=True)
    processor = ReceiptProcessor(web_client)
    
    # Login with test credentials
    login_success, _ = web_client.login("test", "test")
    print(f"✅ Login successful: {login_success}")
    
    # Create test receipts - mix of valid and invalid contracts
    receipts = [
        ReceiptData("123456", "2024-01-01", "2024-01-31", "rent", 100.00),  # Valid (in mock list)
        ReceiptData("111111", "2024-02-01", "2024-02-29", "rent", 900.50),  # Invalid
        ReceiptData("789012", "2024-03-01", "2024-03-31", "rent", 925.75),  # Valid (in mock list)
        ReceiptData("999999", "2024-04-01", "2024-04-30", "rent", 800.00),  # Invalid
    ]
    
    print(f"Created {len(receipts)} test receipts (mix of valid and invalid contract IDs)")
    
    # Process in dry run mode to ensure no network calls
    processor.set_dry_run(True)
    
    # Process with contract validation enabled
    print(f"\n📊 Processing with contract validation...")
    results = processor.process_receipts_bulk(receipts, validate_contracts=True)
    
    print(f"\nResults by status:")
    status_counts = {}
    
    for result in results:
        status = result.status if result.status else ('Success' if result.success else 'Failed')
        status_counts[status] = status_counts.get(status, 0) + 1
        
        status_emoji = "✅" if status == "Success" else "⏭️" if status == "Skipped" else "❌"
        print(f"  {status_emoji} Contract {result.contract_id}: {status}")
        if result.error_message:
            print(f"     Reason: {result.error_message}")
    
    print(f"\n📋 SUMMARY:")
    for status, count in status_counts.items():
        emoji = "✅" if status == "Success" else "⏭️" if status == "Skipped" else "❌"
        print(f"  {emoji} {status}: {count}")
    
    # Test report generation
    print(f"\n📄 Testing report generation...")
    report_data = processor.generate_report_data()
    
    print(f"Report entries:")
    for entry in report_data:
        status_emoji = "✅" if entry['Status'] == "Success" else "⏭️" if entry['Status'] == "Skipped" else "❌"
        print(f"  {status_emoji} {entry['Contract ID']}: {entry['Status']}")
    
    # Verify correct status reporting
    skipped_count = sum(1 for entry in report_data if entry['Status'] == 'Skipped')
    success_count = sum(1 for entry in report_data if entry['Status'] == 'Success')
    
    print(f"\n🎯 VERIFICATION:")
    print(f"  Expected: 2 Success, 2 Skipped")
    print(f"  Actual: {success_count} Success, {skipped_count} Skipped")
    
    if success_count == 2 and skipped_count == 2:
        print(f"  ✅ SUCCESS: Correct status reporting for mixed valid/invalid contracts")
    else:
        print(f"  ❌ FAILED: Incorrect status counts")
    
    print(f"\n🎯 STATUS REPORTING TEST COMPLETE")

if __name__ == "__main__":
    test_status_reporting()
