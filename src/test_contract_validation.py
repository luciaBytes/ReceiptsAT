#!/usr/bin/env python3
"""
Test script for contract validation functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from web_client import WebClient
from csv_handler import CSVHandler
from receipt_processor import ReceiptProcessor
import json

def test_contract_validation():
    """Test the contract validation functionality."""
    
    print("=" * 70)
    print("CONTRACT VALIDATION TEST")
    print("=" * 70)
    
    # Initialize components
    web_client = WebClient()  # Demo purposes
    csv_handler = CSVHandler()
    processor = ReceiptProcessor(web_client)
    
    # Test 1: Mock login
    print("\n1. Testing authentication...")
    login_success, login_message = web_client.login("demo", "demo")
    print(f"   Login: {'✅ Success' if login_success else '❌ Failed'} - {login_message}")
    
    if not login_success:
        print("Cannot proceed without authentication")
        return
    
    # Test 2: Get contract IDs from portal (mock)
    print("\n2. Fetching contract IDs from portal...")
    success, portal_contracts, message = web_client.get_contract_ids()
    print(f"   Portal contracts: {'✅ Success' if success else '❌ Failed'} - {message}")
    if success:
        print(f"   Found contracts: {portal_contracts}")
    
    # Test 3: Create sample CSV data for testing
    print("\n3. Creating sample CSV data...")
    sample_csv_content = """contractId,fromDate,toDate,receiptType,value
12345,2024-01-01,2024-01-31,monthly,500.00
67890,2024-02-01,2024-02-29,monthly,600.00
99999,2024-03-01,2024-03-31,monthly,550.00
11111,2024-04-01,2024-04-30,monthly,500.00
88888,2024-05-01,2024-05-31,monthly,650.00"""
    
    # Write sample CSV
    csv_file = "test_contracts.csv"
    with open(csv_file, 'w', encoding='utf-8') as f:
        f.write(sample_csv_content)
    
    print(f"   Created sample CSV: {csv_file}")
    
    # Test 4: Load CSV data
    print("\n4. Loading and validating CSV...")
    csv_success, csv_errors = csv_handler.load_csv(csv_file)
    print(f"   CSV loading: {'✅ Success' if csv_success else '❌ Failed'}")
    
    if csv_errors:
        for error in csv_errors:
            print(f"   CSV Error: {error}")
    
    if not csv_success:
        return
    
    # Get contract IDs from CSV
    csv_contracts = csv_handler.get_contract_ids()
    print(f"   CSV contracts: {csv_contracts}")
    
    # Test 5: Contract validation
    print("\n5. Validating contracts...")
    validation_report = web_client.validate_csv_contracts(csv_contracts)
    
    print(f"   Validation: {'✅ Success' if validation_report['success'] else '❌ Failed'}")
    print(f"   Message: {validation_report['message']}")
    
    # Display detailed validation results
    print(f"\n   📊 VALIDATION RESULTS:")
    print(f"   Portal contracts: {validation_report['portal_contracts_count']} - {validation_report['portal_contracts']}")
    print(f"   CSV contracts: {validation_report['csv_contracts_count']} - {validation_report['csv_contracts']}")
    print(f"   Valid matches: {len(validation_report['valid_contracts'])} - {validation_report['valid_contracts']}")
    print(f"   Invalid contracts: {len(validation_report['invalid_contracts'])} - {validation_report['invalid_contracts']}")
    print(f"   Missing from CSV: {len(validation_report['missing_from_csv'])} - {validation_report['missing_from_csv']}")
    
    if validation_report['validation_errors']:
        print(f"\n   ⚠️  VALIDATION ISSUES:")
        for error in validation_report['validation_errors']:
            print(f"      • {error}")
    
    # Test 6: Receipt processor validation
    print("\n6. Testing receipt processor validation...")
    receipts = csv_handler.get_receipts()
    processor_validation = processor.validate_contracts(receipts)
    
    print(f"   Processor validation: {'✅ Success' if processor_validation['success'] else '❌ Failed'}")
    
    # Test 7: Bulk processing with validation
    print("\n7. Testing bulk processing with contract validation...")
    
    def progress_callback(current, total, message):
        print(f"   Progress: {current}/{total} - {message}")
    
    results = processor.process_receipts_bulk(receipts, progress_callback, validate_contracts=True)
    
    print(f"\n   📋 PROCESSING RESULTS:")
    for result in results:
        status = "✅ Success" if result.success else "❌ Failed"
        print(f"      Contract {result.contract_id}: {status}")
        if not result.success:
            print(f"         Error: {result.error_message}")
    
    # Summary
    successful_count = sum(1 for r in results if r.success)
    failed_count = len(results) - successful_count
    
    print(f"\n   📈 SUMMARY:")
    print(f"      Total receipts: {len(results)}")
    print(f"      Successful: {successful_count}")
    print(f"      Failed: {failed_count}")
    
    # Cleanup
    try:
        os.remove(csv_file)
        print(f"\n   🧹 Cleaned up test file: {csv_file}")
    except:
        pass
    
    print(f"\n🎉 Contract validation test completed!")

if __name__ == "__main__":
    test_contract_validation()
