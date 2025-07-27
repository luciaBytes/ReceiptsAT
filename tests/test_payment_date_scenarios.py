#!/usr/bin/env python3
"""
Comprehensive test of payment date validation scenarios.
"""

import sys
import os
import tempfile
from datetime import datetime, timedelta

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.csv_handler import CSVHandler

def test_payment_date_scenarios():
    """Test various payment date scenarios."""
    print("=" * 80)
    print("COMPREHENSIVE PAYMENT DATE VALIDATION TEST")
    print("=" * 80)
    
    # Test scenarios
    scenarios = [
        {
            "name": "Payment BEFORE receipt period",
            "from_date": "2024-06-01",
            "to_date": "2024-06-30", 
            "payment_date": "2024-05-15",
            "should_pass": True,
            "description": "Payment made before the rental period starts"
        },
        {
            "name": "Payment DURING receipt period",
            "from_date": "2024-06-01",  
            "to_date": "2024-06-30",
            "payment_date": "2024-06-15",
            "should_pass": True,
            "description": "Payment made during the rental period"
        },
        {
            "name": "Payment AFTER receipt period",
            "from_date": "2024-06-01",
            "to_date": "2024-06-30",
            "payment_date": "2024-07-15", 
            "should_pass": True,
            "description": "Payment made after the rental period ends"
        },
        {
            "name": "Payment in the FUTURE",
            "from_date": "2024-06-01",
            "to_date": "2024-06-30",
            "payment_date": (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            "should_pass": False,
            "description": "Payment date in the future (should be rejected)"
        },
        {
            "name": "Invalid receipt period (from > to)",
            "from_date": "2024-06-30",
            "to_date": "2024-06-01", 
            "payment_date": "2024-06-15",
            "should_pass": False,
            "description": "Invalid receipt period with valid payment date"
        }
    ]
    
    success_count = 0
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. Testing: {scenario['name']}")
        print("-" * 50)
        print(f"   Description: {scenario['description']}")
        print(f"   Receipt Period: {scenario['from_date']} to {scenario['to_date']}")
        print(f"   Payment Date: {scenario['payment_date']}")
        print(f"   Expected Result: {'✅ PASS' if scenario['should_pass'] else '❌ FAIL'}")
        
        # Create test CSV
        csv_content = f"""contractId,fromDate,toDate,receiptType,value,paymentDate
123456,{scenario['from_date']},{scenario['to_date']},rent,100.00,{scenario['payment_date']}"""
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
                f.write(csv_content)
                temp_file = f.name
            
            csv_handler = CSVHandler()
            success, errors = csv_handler.load_csv(temp_file)
            
            # Check if result matches expectation
            if success == scenario['should_pass']:
                print(f"   ✅ CORRECT: {'Passed' if success else 'Failed'} as expected")
                if not success:
                    print(f"      Error: {errors[0] if errors else 'No specific error'}")
                success_count += 1
            else:
                print(f"   ❌ INCORRECT: Expected {'pass' if scenario['should_pass'] else 'fail'}, got {'pass' if success else 'fail'}")
                if errors:
                    print(f"      Errors: {errors}")
            
            # Clean up
            os.unlink(temp_file)
            
        except Exception as e:
            print(f"   ❌ EXCEPTION: {str(e)}")
    
    # Summary
    print(f"\n" + "=" * 80)
    print("PAYMENT DATE VALIDATION TEST SUMMARY")
    print("=" * 80)
    print(f"✅ Correct scenarios: {success_count}/{len(scenarios)}")
    
    print(f"\n📋 Validation Rules Applied:")
    print(f"   1. Payment date cannot be in the future ❌")
    print(f"   2. Payment date CAN be before receipt period ✅")
    print(f"   3. Payment date CAN be during receipt period ✅") 
    print(f"   4. Payment date CAN be after receipt period ✅")
    print(f"   5. Receipt period dates must be valid (from ≤ to) ✅")
    
    if success_count == len(scenarios):
        print(f"\n🎉 ALL SCENARIOS BEHAVED CORRECTLY!")
        print(f"Payment date validation is now properly flexible.")
    else:
        print(f"\n⚠️  Some scenarios didn't behave as expected.")
    
    print("=" * 80)

if __name__ == "__main__":
    test_payment_date_scenarios()
