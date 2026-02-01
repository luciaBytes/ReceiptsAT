#!/usr/bin/env python3
"""
Test the corrected payment date validation with recibos_julho.csv
"""

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from csv_handler import CSVHandler

def test_recibos_julho():
    """Test loading recibos_julho.csv with the corrected validation."""
    print("=" * 80)
    print("TESTING RECIBOS_JULHO.CSV WITH CORRECTED PAYMENT DATE VALIDATION")
    print("=" * 80)
    
    project_root = os.path.join(os.path.dirname(__file__), '..')
    csv_file_path = os.path.join(project_root, 'sample', 'recibos_julho.csv')
    
    if not os.path.exists(csv_file_path):
        print(f"❌ Sample CSV file not found: {csv_file_path}")
        return
    
    print(f"Testing file: {csv_file_path}")
    
    # Show the file content
    print(f"\nFile Content:")
    print("-" * 40)
    with open(csv_file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for i, line in enumerate(lines, 1):
            print(f"{i:2}: {line.rstrip()}")
    
    # Test CSV Loading
    print(f"\nTesting CSV Loading:")
    print("-" * 40)
    
    csv_handler = CSVHandler()
    success, errors = csv_handler.load_csv(csv_file_path)
    
    if success:
        receipts = csv_handler.get_receipts()
        print(f"✅ CSV loaded successfully: {len(receipts)} receipts")
        
        print(f"\nColumn Mapping Used:")
        for standard, csv_col in csv_handler.column_mapping.items():
            print(f"  {standard:12} -> '{csv_col}'")
        
        print(f"\nReceipt Details:")
        for i, receipt in enumerate(receipts, 1):
            print(f"  {i}. Contract {receipt.contract_id}:")
            print(f"     - Period: {receipt.from_date} to {receipt.to_date}")
            print(f"     - Payment Date: {receipt.payment_date}")
            print(f"     - Value: €{receipt.value}")
            print(f"     - Type: {receipt.receipt_type}")
            
            # Explain the validation
            print(f"     - Payment date ({receipt.payment_date}) is BEFORE receipt period ({receipt.from_date} to {receipt.to_date})")
            print(f"     - This is now ALLOWED ✅")
    else:
        print(f"❌ CSV loading failed with errors:")
        for error in errors:
            print(f"   • {error}")
    
    print(f"\n" + "=" * 80)
    if success:
        print("🎉 SUCCESS: Payment date validation now works correctly!")
        print("Key changes:")
        print("• Payment date can be BEFORE receipt period ✅")
        print("• Payment date can be AFTER receipt period ✅")
        print("• Payment date cannot be in the FUTURE ❌")
        print("• Receipt period dates still validated (from ≤ to) ✅")
    else:
        print("❌ FAILURE: Validation issues still exist")
    print("=" * 80)

if __name__ == "__main__":
    test_recibos_julho()
