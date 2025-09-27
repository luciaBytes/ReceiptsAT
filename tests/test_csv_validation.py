"""
Test script to debug CSV validation issues
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from csv_handler import CSVHandler

def test_csv_validation():
    """Test CSV validation functionality"""
    
    print("=== CSV Validation Test ===")
    
    # Create a CSV handler
    handler = CSVHandler()
    
    # Test with valid data
    print("\n1. Testing valid CSV file...")
    if os.path.exists("test_data.csv"):
        success, errors = handler.load_csv("test_data.csv")
        print(f"Success: {success}")
        print(f"Errors: {errors}")
        print(f"Receipts loaded: {len(handler.get_receipts())}")
        
        for receipt in handler.get_receipts():
            print(f"  - Contract: {receipt.contract_id}, Value: {receipt.value}")
    else:
        print("test_data.csv not found")
    
    # Test with invalid data
    print("\n2. Testing invalid CSV file...")
    if os.path.exists("test_data_invalid.csv"):
        success, errors = handler.load_csv("test_data_invalid.csv")
        print(f"Success: {success}")
        print(f"Errors: {len(errors)} error(s)")
        for error in errors[:5]:  # Show first 5 errors
            print(f"  - {error}")
        print(f"Receipts loaded: {len(handler.get_receipts())}")
    else:
        print("test_data_invalid.csv not found")
    
    # Test with user's credentials file (should fail)
    print("\n3. Testing credentials file (should fail)...")
    if os.path.exists("credentials"):
        success, errors = handler.load_csv("credentials")
        print(f"Success: {success}")
        print(f"Errors: {len(errors)} error(s)")
        for error in errors[:3]:  # Show first 3 errors
            print(f"  - {error}")
    else:
        print("credentials file not found")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_csv_validation()
