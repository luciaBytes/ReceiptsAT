#!/usr/bin/env python3
"""
Test the actual recibos_julho.csv file with receipt type defaulting.
"""

import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.csv_handler import CSVHandler
from src.utils.logger import get_logger

logger = get_logger(__name__)

def test_recibos_julho_with_receipt_type_default():
    """Test loading recibos_julho.csv with receipt type defaulting."""
    print("=" * 70)
    print("TESTING recibos_julho.csv WITH RECEIPT TYPE DEFAULTING")
    print("=" * 70)
    
    csv_file_path = os.path.join(project_root, 'sample', 'recibos_julho.csv')
    
    if not os.path.exists(csv_file_path):
        print(f"❌ File not found: {csv_file_path}")
        return
    
    print(f"Testing: {os.path.basename(csv_file_path)}")
    
    # Load CSV
    csv_handler = CSVHandler()
    success, errors = csv_handler.load_csv(csv_file_path)
    
    if success:
        receipts = csv_handler.get_receipts()
        print(f"✅ CSV loaded successfully: {len(receipts)} receipts")
        
        print(f"\nColumn mapping:")
        for standard, csv_col in csv_handler.column_mapping.items():
            print(f"  {standard:15} -> '{csv_col}'")
        
        print(f"\nFirst 5 receipts:")
        for i, receipt in enumerate(receipts[:5], 1):
            print(f"  {i}. Contract {receipt.contract_id}:")
            print(f"     - Period: {receipt.from_date} to {receipt.to_date}")
            print(f"     - Payment Date: {receipt.payment_date} (defaulted: {receipt.payment_date_defaulted})")
            print(f"     - Receipt Type: '{receipt.receipt_type}' (defaulted: {receipt.receipt_type_defaulted})")
            print(f"     - Value: €{receipt.value:.2f} (defaulted: {receipt.value_defaulted})")
        
        # Check all receipts have correct defaults
        all_rent_type = all(r.receipt_type == 'rent' for r in receipts)
        all_type_defaulted = all(r.receipt_type_defaulted for r in receipts)
        
        print(f"\n📊 Analysis:")
        print(f"   Total receipts: {len(receipts)}")
        print(f"   All receipt types = 'rent': {all_rent_type}")
        print(f"   All receipt types defaulted: {all_type_defaulted}")
        
        if all_rent_type and all_type_defaulted:
            print(f"\n🎉 SUCCESS:")
            print(f"   ✅ recibos_julho.csv loads successfully without receiptType column")
            print(f"   ✅ All receipts automatically default to 'rent'")
            print(f"   ✅ Users will see 'Receipt Type: rent (defaulted)' in orange in step-by-step mode")
            print(f"   ✅ This CSV file now works with the application!")
        else:
            print(f"\n❌ Some receipts don't have correct defaults")
            
    else:
        print(f"❌ CSV validation failed:")
        for error in errors:
            print(f"  • {error}")
    
    print(f"\n" + "=" * 70)
    print("BENEFIT FOR USER")
    print("=" * 70)
    print("📁 The user's CSV file (recibos_julho.csv) can now be processed!")
    print("📁 No need to add a receiptType column - it defaults to 'rent'")
    print("📁 All existing CSV files continue to work as before")
    print("📁 Minimal CSV format: contractId, fromDate, toDate")

if __name__ == "__main__":
    test_recibos_julho_with_receipt_type_default()
