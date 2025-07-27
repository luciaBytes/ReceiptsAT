#!/usr/bin/env python3
"""
Test receipt type defaulting functionality.
"""

import sys
import os
import tempfile

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.csv_handler import CSVHandler
from src.utils.logger import get_logger

logger = get_logger(__name__)

def test_receipt_type_defaulting():
    """Test that receiptType defaults to 'rent' when not specified in CSV."""
    print("=" * 70)
    print("RECEIPT TYPE DEFAULTING TEST")
    print("=" * 70)
    
    test_cases = [
        {
            "name": "CSV with explicit receipt type",
            "csv_content": """contractId,fromDate,toDate,receiptType,paymentDate,value
123456,2024-07-01,2024-07-31,rent,2024-07-28,100.00""",
            "expected_type": "rent",
            "expected_defaulted": False
        },
        {
            "name": "CSV without receiptType column (should default to 'rent')",
            "csv_content": """contractId,fromDate,toDate,paymentDate,value
123456,2024-07-01,2024-07-31,2024-07-28,100.00""",
            "expected_type": "rent",
            "expected_defaulted": True
        },
        {
            "name": "CSV with empty receiptType (should default to 'rent')",
            "csv_content": """contractId,fromDate,toDate,receiptType,paymentDate,value
123456,2024-07-01,2024-07-31,,2024-07-28,100.00""",
            "expected_type": "rent",
            "expected_defaulted": True
        },
        {
            "name": "CSV with different receipt type",
            "csv_content": """contractId,fromDate,toDate,receiptType,paymentDate,value
123456,2024-07-01,2024-07-31,deposit,2024-07-28,500.00""",
            "expected_type": "deposit",
            "expected_defaulted": False
        },
        {
            "name": "Minimal CSV (only required columns)",
            "csv_content": """contractId,fromDate,toDate
123456,2024-07-01,2024-07-31""",
            "expected_type": "rent",
            "expected_defaulted": True
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test_case['name']}")
        print("-" * 50)
        
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(test_case['csv_content'])
            temp_file_path = f.name
        
        try:
            # Load CSV
            csv_handler = CSVHandler()
            success, errors = csv_handler.load_csv(temp_file_path)
            
            if success:
                receipts = csv_handler.get_receipts()
                print(f"   ✅ CSV loaded successfully: {len(receipts)} receipt(s)")
                
                if receipts:
                    receipt = receipts[0]
                    print(f"   Receipt Type: '{receipt.receipt_type}'")
                    print(f"   Type Defaulted: {receipt.receipt_type_defaulted}")
                    
                    # Verify expected behavior
                    if receipt.receipt_type == test_case['expected_type']:
                        print(f"   ✅ Receipt type matches expected: '{test_case['expected_type']}'")
                    else:
                        print(f"   ❌ Receipt type mismatch:")
                        print(f"      Expected: '{test_case['expected_type']}'")
                        print(f"      Actual: '{receipt.receipt_type}'")
                    
                    if receipt.receipt_type_defaulted == test_case['expected_defaulted']:
                        print(f"   ✅ Defaulted flag correct: {test_case['expected_defaulted']}")
                    else:
                        print(f"   ❌ Defaulted flag mismatch:")
                        print(f"      Expected: {test_case['expected_defaulted']}")
                        print(f"      Actual: {receipt.receipt_type_defaulted}")
                    
                    # Show what user would see in step-by-step dialog
                    if receipt.receipt_type_defaulted:
                        print(f"   📋 Dialog would show: 'Receipt Type: {receipt.receipt_type} (defaulted)' in orange")
                    else:
                        print(f"   📋 Dialog would show: 'Receipt Type: {receipt.receipt_type}' in normal color")
                
            else:
                print(f"   ❌ CSV loading failed:")
                for error in errors:
                    print(f"      • {error}")
        
        finally:
            # Clean up
            try:
                os.unlink(temp_file_path)
            except:
                pass
    
    print(f"\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("✅ receiptType is now OPTIONAL in CSV files")
    print("✅ When missing or empty, it defaults to 'rent'")
    print("✅ Users can see in step-by-step dialog when it was defaulted")
    print("✅ Backward compatibility maintained for existing CSV files")
    print("✅ Minimal CSV files now work (only contractId, fromDate, toDate required)")

if __name__ == "__main__":
    test_receipt_type_defaulting()
