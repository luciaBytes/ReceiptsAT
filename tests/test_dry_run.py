#!/usr/bin/env python3
"""
Test dry run functionality to ensure no network requests are made.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from web_client import WebClient
from csv_handler import CSVHandler, ReceiptData
from receipt_processor import ReceiptProcessor

def test_dry_run():
    """Test that dry run mode doesn't make network requests."""
    
    print("=" * 60)
    print("DRY RUN TEST")
    print("=" * 60)
    
    # Initialize components
    web_client = WebClient(testing_mode=True)  # Use testing mode to be safe
    processor = ReceiptProcessor(web_client)
    
    # Enable dry run
    processor.set_dry_run(True)
    print(f"✅ Dry run mode enabled")
    
    # Create test receipts
    receipts = [
        ReceiptData("123456", "2024-01-01", "2024-01-31", "rent", 100.00),
        ReceiptData("789012", "2024-02-01", "2024-02-29", "rent", 900.50),
        ReceiptData("345678", "2024-03-01", "2024-03-31", "rent", 925.75)
    ]
    
    print(f"Created {len(receipts)} test receipts")
    
    # Test bulk processing
    print(f"\n📊 Testing bulk processing in dry run mode...")
    results = processor.process_receipts_bulk(receipts, validate_contracts=False)
    
    print(f"Results:")
    for result in results:
        status = "✅ Success" if result.success else "❌ Failed"
        print(f"  Contract {result.contract_id}: {status}")
        print(f"    Receipt: {result.receipt_number}")
        print(f"    Tenant: {result.tenant_name}")
        if result.error_message:
            print(f"    Error: {result.error_message}")
    
    # Verify no actual requests were made
    successful_count = sum(1 for r in results if r.success)
    print(f"\n📋 SUMMARY:")
    print(f"  Total receipts processed: {len(results)}")
    print(f"  Successful: {successful_count}")
    print(f"  Failed: {len(results) - successful_count}")
    
    if all(r.success and "DRY-RUN" in r.receipt_number for r in results):
        print(f"  ✅ All receipts processed in dry run mode (no network requests)")
    else:
        print(f"  ❌ Some receipts may have made actual requests")
    
    print(f"\n🎯 DRY RUN TEST COMPLETE")

if __name__ == "__main__":
    test_dry_run()
