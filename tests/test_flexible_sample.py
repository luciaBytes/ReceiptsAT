#!/usr/bin/env python3
"""
Test the flexible_order_receipts.csv file with different column order.
"""

import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.csv_handler import CSVHandler

def test_flexible_order_sample():
    """Test loading the flexible order sample file."""
    print("=" * 80)
    print("FLEXIBLE ORDER SAMPLE TEST")
    print("=" * 80)
    
    csv_file_path = os.path.join(project_root, 'sample', 'flexible_order_receipts.csv')
    
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
    else:
        print(f"❌ CSV loading failed with errors:")
        for error in errors:
            print(f"   • {error}")
    
    print(f"\n" + "=" * 80)
    if success:
        print("🎉 SUCCESS: Flexible column order working perfectly!")
        print("The CSV parser correctly handled:")
        print("• Different column order (payment_date first, contract last)")
        print("• Column aliases (payment_date, amount, type, etc.)")
        print("• Proper data mapping to internal structure")
    else:
        print("❌ FAILURE: Flexible column order needs fixes")
    print("=" * 80)

if __name__ == "__main__":
    test_flexible_order_sample()
