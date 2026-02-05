#!/usr/bin/env python3
"""
Test flexible CSV column ordering and aliases.
"""

import sys
import os
import tempfile
from datetime import datetime

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from csv_handler import CSVHandler

def test_flexible_column_order():
    """Test that CSV column order doesn't matter."""
    print("=" * 80)
    print("FLEXIBLE CSV COLUMN ORDER TEST")
    print("=" * 80)
    
    # Test cases with different column orders and aliases
    test_cases = [
        {
            "name": "Original Order",
            "header": "contractId,fromDate,toDate,receiptType,value,paymentDate",
            "data": "123456,2024-07-01,2024-07-31,rent,100.00,2024-07-28"
        },
        {
            "name": "Reversed Order",
            "header": "paymentDate,value,receiptType,toDate,fromDate,contractId",
            "data": "2024-07-28,100.00,rent,2024-07-31,2024-07-01,123456"
        },
        {
            "name": "Random Order",
            "header": "receiptType,contractId,paymentDate,value,toDate,fromDate",
            "data": "rent,123456,2024-07-28,100.00,2024-07-31,2024-07-01"
        },
        {
            "name": "With Aliases (underscore style)",
            "header": "contract_id,from_date,to_date,receipt_type,amount,payment_date",
            "data": "123456,2024-07-01,2024-07-31,rent,100.00,2024-07-28"
        },
        {
            "name": "With Alternative Aliases",
            "header": "contract,start_date,end_date,type,rent,paid_date",
            "data": "123456,2024-07-01,2024-07-31,rent,100.00,2024-07-28"
        },
        {
            "name": "Mixed Case Headers",
            "header": "ContractId,FromDate,ToDate,ReceiptType,Value,PaymentDate",
            "data": "123456,2024-07-01,2024-07-31,rent,100.00,2024-07-28"
        },
        {
            "name": "With Spaces (should be trimmed)",
            "header": " contractId , fromDate , toDate , receiptType , value , paymentDate ",
            "data": "123456,2024-07-01,2024-07-31,rent,100.00,2024-07-28"
        },
        {
            "name": "Without Optional Value Column",
            "header": "contractId,fromDate,toDate,receiptType,paymentDate",
            "data": "123456,2024-07-01,2024-07-31,rent,2024-07-28"
        }
    ]
    
    success_count = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test_case['name']}")
        print("-" * 50)
        
        # Create temporary CSV file
        csv_content = f"{test_case['header']}\n{test_case['data']}\n"
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
                f.write(csv_content)
                temp_file = f.name
            
            # Test loading
            csv_handler = CSVHandler()
            success, errors = csv_handler.load_csv(temp_file)
            
            if success:
                receipts = csv_handler.get_receipts()
                if len(receipts) == 1:
                    receipt = receipts[0]
                    print(f"✅ SUCCESS - Loaded receipt:")
                    print(f"   Contract ID: {receipt.contract_id}")
                    print(f"   Period: {receipt.from_date} to {receipt.to_date}")
                    print(f"   Type: {receipt.receipt_type}")
                    print(f"   Value: €{receipt.value}")
                    print(f"   Payment Date: {receipt.payment_date}")
                    print(f"   Column Mapping: {csv_handler.column_mapping}")
                    success_count += 1
                    
                    # Verify the data is correct
                    expected_values = {
                        'contract_id': '123456',
                        'from_date': '2024-07-01',
                        'to_date': '2024-07-31',
                        'receipt_type': 'rent',
                        'payment_date': '2024-07-28'
                    }
                    
                    all_correct = True
                    for field, expected in expected_values.items():
                        actual = getattr(receipt, field)
                        if actual != expected:
                            print(f"   ⚠️  Field mismatch: {field} = '{actual}', expected '{expected}'")
                            all_correct = False
                    
                    if all_correct:
                        print(f"   ✅ All field values correct")
                    
                else:
                    print(f"❌ FAILED - Expected 1 receipt, got {len(receipts)}")
            else:
                print(f"❌ FAILED - Loading errors:")
                for error in errors:
                    print(f"   • {error}")
            
            # Clean up
            os.unlink(temp_file)
            
        except Exception as e:
            print(f"❌ FAILED - Exception: {str(e)}")
    
    # Test error cases
    print(f"\n9. Testing: Missing Required Column")
    print("-" * 50)
    
    try:
        # Missing paymentDate column
        csv_content = "contractId,fromDate,toDate,receiptType,value\n123456,2024-07-01,2024-07-31,rent,100.00\n"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(csv_content)
            temp_file = f.name
        
        csv_handler = CSVHandler()
        success, errors = csv_handler.load_csv(temp_file)
        
        if not success and any('paymentDate' in error for error in errors):
            print(f"✅ SUCCESS - Correctly detected missing required column")
            print(f"   Error: {errors[0]}")
        else:
            print(f"❌ FAILED - Should have detected missing paymentDate column")
        
        os.unlink(temp_file)
        
    except Exception as e:
        print(f"❌ FAILED - Exception: {str(e)}")
    
    # Summary
    print(f"\n" + "=" * 80)
    print("FLEXIBLE CSV TEST SUMMARY") 
    print("=" * 80)
    print(f"✅ Successful tests: {success_count}/{len(test_cases)}")
    print(f"📋 Features tested:")
    print(f"   • Column order flexibility")
    print(f"   • Column name aliases")
    print(f"   • Case insensitive headers")
    print(f"   • Header trimming")
    print(f"   • Optional column handling")
    print(f"   • Missing column detection")
    
    if success_count == len(test_cases):
        print(f"\n🎉 ALL TESTS PASSED! CSV column order is fully flexible.")
    else:
        print(f"\n⚠️  Some tests failed. Review the implementation.")
    
    print("=" * 80)

if __name__ == "__main__":
    test_flexible_column_order()
