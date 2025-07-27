#!/usr/bin/env python3
"""
Quick test to verify recibos_julho.csv loads correctly in the main application.
"""

import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, 'src'))

from csv_handler import CSVHandler

def main():
    print("Testing recibos_julho.csv with main application CSV handler...")
    
    csv_file = os.path.join(project_root, 'sample', 'recibos_julho.csv')
    
    if not os.path.exists(csv_file):
        print(f"File not found: {csv_file}")
        return
    
    csv_handler = CSVHandler()
    success, errors = csv_handler.load_csv(csv_file)
    
    if success:
        receipts = csv_handler.get_receipts()
        print(f"✅ SUCCESS: Loaded {len(receipts)} receipts")
        
        for receipt in receipts:
            print(f"   Contract: {receipt.contract_id}")
            print(f"   Period: {receipt.from_date} to {receipt.to_date}")
            print(f"   Payment: {receipt.payment_date}")
            print(f"   Value: €{receipt.value}")
    else:
        print(f"❌ FAILED: {errors}")

if __name__ == "__main__":
    main()
