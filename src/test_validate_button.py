#!/usr/bin/env python3
"""
Test the validate contracts button functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from web_client import WebClient
from csv_handler import CSVHandler
from receipt_processor import ReceiptProcessor

def test_validate_button_functionality():
    """Test the contract validation functionality that powers the validation button."""
    
    print("=" * 70)
    print("VALIDATE CONTRACTS BUTTON TEST")
    print("=" * 70)
    
    # Initialize components
    web_client = WebClient()
    csv_handler = CSVHandler()
    processor = ReceiptProcessor(web_client)
    
    # Step 1: Mock login
    print("1. Testing authentication...")
    login_success, login_message = web_client.login("demo", "demo")
    print(f"   Login: {' Success' if login_success else ' Failed'} - {login_message}")
    
    if not login_success:
        print("Cannot proceed without authentication")
        return
    
    # Step 2: Create test CSV with some valid and invalid contracts
    print("\n2. Creating test CSV with mixed contract validity...")
    test_csv_content = """contractId,fromDate,toDate,receiptType,value,paymentDate
12345,2024-01-01,2024-01-31,monthly,500.00,2024-01-15
67890,2024-02-01,2024-02-29,monthly,600.00,2024-02-15
99999,2024-03-01,2024-03-31,monthly,550.00,2024-03-15
11111,2024-04-01,2024-04-30,monthly,500.00,2024-04-15
88888,2024-05-01,2024-05-31,monthly,650.00,2024-05-15"""
    
    csv_file = "validation_test.csv"
    with open(csv_file, 'w', encoding='utf-8') as f:
        f.write(test_csv_content)
    
    print(f"   Created CSV with 5 contracts")
    
    # Step 3: Load CSV
    print("\n3. Loading CSV...")
    csv_success, csv_errors = csv_handler.load_csv(csv_file)
    print(f"   CSV loading: {' Success' if csv_success else ' Failed'}")
    
    if csv_errors:
        for error in csv_errors:
            print(f"   Error: {error}")
    
    receipts = csv_handler.get_receipts()
    print(f"   Loaded {len(receipts)} receipts")
    
    # Step 4: Simulate what happens when user clicks "Validate Contracts" button
    print(f"\n4.  SIMULATING 'VALIDATE CONTRACTS' BUTTON CLICK...")
    print("   This is exactly what happens when the user clicks the validation button:")
    
    # This is the same call made by the GUI validation button
    validation_report = processor.validate_contracts(receipts)
    
    # Step 5: Display results exactly as shown in the GUI popup
    print(f"\n5.  VALIDATION RESULTS (as shown in GUI popup):")
    
    message_parts = []
    message_parts.append(f" VALIDATION SUMMARY:")
    message_parts.append(f"Portal contracts: {validation_report['portal_contracts_count']}")
    message_parts.append(f"CSV contracts: {validation_report['csv_contracts_count']}")
    message_parts.append(f"Valid matches: {len(validation_report['valid_contracts'])}")
    
    if validation_report['valid_contracts']:
        message_parts.append(f"\n VALID CONTRACTS:")
        for contract in validation_report['valid_contracts']:
            message_parts.append(f"  • {contract}")
    
    if validation_report['invalid_contracts']:
        message_parts.append(f"\n INVALID CONTRACTS (not found in portal):")
        for contract in validation_report['invalid_contracts']:
            message_parts.append(f"  • {contract}")
    
    if validation_report['missing_from_csv']:
        message_parts.append(f"\n PORTAL CONTRACTS NOT IN CSV:")
        for contract in validation_report['missing_from_csv']:
            message_parts.append(f"  • {contract}")
    
    if validation_report['validation_errors']:
        message_parts.append(f"\n VALIDATION ISSUES:")
        for error in validation_report['validation_errors']:
            message_parts.append(f"  • {error}")
    
    # Display the message that would appear in the GUI popup
    for line in message_parts:
        print(f"   {line}")
    
    # Step 6: Show button behavior
    print(f"\n6. 🔘 BUTTON BEHAVIOR:")
    print(f"    Button enabled when: Authenticated + CSV loaded")
    print(f"    Button disabled when: Not authenticated OR no CSV")
    print(f"    Button shows: Detailed popup with validation results")
    print(f"    Processing: Button disabled during validation, re-enabled after")
    
    # Cleanup
    try:
        os.remove(csv_file)
        print(f"\n   🧹 Cleaned up test file: {csv_file}")
    except:
        pass
    
    print(f"\n🎉 Validate Contracts button test completed!")
    print(f"\n SUMMARY:")
    print(f"   The 'Validate Contracts' button provides users with:")
    print(f"   • Immediate contract validation without starting processing")
    print(f"   • Clear identification of valid vs invalid contracts")
    print(f"   • Awareness of portal contracts not included in CSV")
    print(f"   • Detailed popup with all validation results")

if __name__ == "__main__":
    test_validate_button_functionality()
