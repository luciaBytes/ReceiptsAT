#!/usr/bin/env python3
"""
Test CSV validation for required payment date.
"""

import sys
import os
import tempfile

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from csv_handler import CSVHandler
from utils.logger import get_logger

logger = get_logger(__name__)

def test_payment_date_validation():
    """Test that CSV validation now requires payment date."""
    print("=" * 70)
    print("CSV PAYMENT DATE VALIDATION TEST")
    print("=" * 70)
    
    test_cases = [
        {
            "name": "Valid CSV with payment dates",
            "csv_content": """contractId,fromDate,toDate,receiptType,value,paymentDate
123456,2024-07-01,2024-07-31,rent,100.00,2024-07-28
789012,2024-06-01,2024-06-30,rent,100.00,2024-06-28""",
            "should_pass": True,
            "expected_error": None
        },
        {
            "name": "Missing paymentDate column",
            "csv_content": """contractId,fromDate,toDate,receiptType,value
123456,2024-07-01,2024-07-31,rent,100.00""",
            "should_pass": False,
            "expected_error": "Missing required columns: paymentDate"
        },
        {
            "name": "Empty payment date value",
            "csv_content": """contractId,fromDate,toDate,receiptType,value,paymentDate
123456,2024-07-01,2024-07-31,rent,100.00,
789012,2024-06-01,2024-06-30,rent,100.00,2024-06-28""",
            "should_pass": False,
            "expected_error": "paymentDate is required and cannot be empty"
        },
        {
            "name": "Invalid payment date format",
            "csv_content": """contractId,fromDate,toDate,receiptType,value,paymentDate
123456,2024-07-01,2024-07-31,rent,100.00,28/07/2024""",
            "should_pass": False,
            "expected_error": "paymentDate must be in YYYY-MM-DD format"
        },
        {
            "name": "Valid different date orders",
            "csv_content": """contractId,fromDate,toDate,receiptType,value,paymentDate
123456,2024-07-01,2024-07-31,rent,100.00,2024-07-15
789012,2024-06-01,2024-06-30,rent,100.00,2024-06-15""",
            "should_pass": True,
            "expected_error": None
        }
    ]
    
    csv_handler = CSVHandler()
    
    for i, test_case in enumerate(test_cases):
        print(f"\n{i+1}. Testing: {test_case['name']}")
        
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as temp_file:
            temp_file.write(test_case['csv_content'])
            temp_file_path = temp_file.name
        
        try:
            # Test CSV loading
            success, errors = csv_handler.load_csv(temp_file_path)
            
            if test_case['should_pass']:
                if success:
                    receipts = csv_handler.get_receipts()
                    print(f"   ✅ PASSED: Loaded {len(receipts)} receipts successfully")
                    
                    # Show payment dates
                    for receipt in receipts:
                        print(f"      - Contract {receipt.contract_id}: Payment date {receipt.payment_date}")
                else:
                    print(f"   ❌ FAILED: Expected success but got errors:")
                    for error in errors:
                        print(f"      • {error}")
            else:
                if not success:
                    print(f"   ✅ PASSED: Correctly rejected with errors:")
                    error_found = False
                    for error in errors:
                        print(f"      • {error}")
                        if test_case['expected_error'] in error:
                            error_found = True
                    
                    if not error_found:
                        print(f"   ⚠️  Expected error containing: '{test_case['expected_error']}'")
                else:
                    print(f"   ❌ FAILED: Expected validation error but CSV was accepted")
        
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_file_path)
            except:
                pass
    
    # Test required columns
    print(f"\n" + "=" * 70)
    print("REQUIRED COLUMNS CHECK")
    print("=" * 70)
    
    print(f"Required columns: {csv_handler.REQUIRED_COLUMNS}")
    print(f"Optional columns: {csv_handler.OPTIONAL_COLUMNS}")
    
    if 'paymentDate' in csv_handler.REQUIRED_COLUMNS:
        print("✅ paymentDate is correctly marked as REQUIRED")
    else:
        print("❌ paymentDate should be marked as REQUIRED")
    
    print(f"\n" + "=" * 70)
    print("CSV PAYMENT DATE VALIDATION TEST COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    test_payment_date_validation()
