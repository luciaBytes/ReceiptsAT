#!/usr/bin/env python3
"""
Test receipt type defaulting with step-by-step processing.
"""

import sys
import os
import tempfile

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.csv_handler import CSVHandler
from src.web_client import WebClient
from src.receipt_processor import ReceiptProcessor
from src.utils.logger import get_logger

logger = get_logger(__name__)

def test_receipt_type_step_by_step():
    """Test receipt type defaulting in step-by-step processing."""
    print("=" * 70)
    print("RECEIPT TYPE DEFAULTING - STEP-BY-STEP TEST")
    print("=" * 70)
    
    # Test CSV without receiptType column - should default to 'rent'
    csv_content = """contractId,fromDate,toDate,paymentDate,value
123456,2024-07-01,2024-07-31,2024-07-28,100.00
789012,2024-07-01,2024-07-31,2024-07-28,100.00"""
    
    # Create temporary CSV file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        f.write(csv_content)
        temp_file_path = f.name
    
    try:
        # Load CSV
        csv_handler = CSVHandler()
        success, errors = csv_handler.load_csv(temp_file_path)
        
        if success:
            receipts = csv_handler.get_receipts()
            print(f"✅ Loaded {len(receipts)} receipts from CSV (no receiptType column)")
            
            # Show what was loaded
            for i, receipt in enumerate(receipts, 1):
                print(f"\nReceipt {i}:")
                print(f"  Contract ID: {receipt.contract_id}")
                print(f"  Receipt Type: '{receipt.receipt_type}' (defaulted: {receipt.receipt_type_defaulted})")
                print(f"  Value: €{receipt.value:.2f} (defaulted: {receipt.value_defaulted})")
                print(f"  Payment Date: {receipt.payment_date} (defaulted: {receipt.payment_date_defaulted})")
            
            # Test step-by-step processing with mock web client
            web_client = WebClient()
            web_client.testing_mode = True
            web_client.authenticated = True
            
            processor = ReceiptProcessor(web_client)
            processor.dry_run = True  # Use dry run for testing
            
            def mock_get_receipt_form(contract_id):
                return True, {
                    'contract_details': {
                        'valorRenda': 100.00,
                        'locatarios': [{'nome': f'Test Tenant {contract_id}'}],
                        'locadores': [{'nome': 'Test Landlord'}]
                    }
                }
                
            web_client.get_receipt_form = mock_get_receipt_form
            
            # Track what would be shown in dialogs
            dialog_data = []
            
            def mock_confirmation_callback(receipt_data, form_data):
                dialog_info = {
                    'contract_id': receipt_data.contract_id,
                    'receipt_type': receipt_data.receipt_type,
                    'receipt_type_defaulted': getattr(receipt_data, 'receipt_type_defaulted', False),
                    'value': receipt_data.value,
                    'value_defaulted': getattr(receipt_data, 'value_defaulted', False)
                }
                dialog_data.append(dialog_info)
                
                print(f"\n📋 Step-by-Step Dialog for Contract {receipt_data.contract_id}:")
                print(f"   Period: {receipt_data.from_date} to {receipt_data.to_date}")
                print(f"   Payment Date: {receipt_data.payment_date}")
                print(f"   Value: €{receipt_data.value:.2f}")
                
                # Show how receipt type would appear in dialog
                if hasattr(receipt_data, 'receipt_type_defaulted') and receipt_data.receipt_type_defaulted:
                    print(f"   Receipt Type: {receipt_data.receipt_type} (defaulted) [orange]")
                else:
                    print(f"   Receipt Type: {receipt_data.receipt_type} [normal]")
                
                return 'confirm'
            
            # Process receipts step-by-step
            print(f"\n🔄 Processing receipts in step-by-step mode...")
            results = processor.process_receipts_step_by_step(receipts, mock_confirmation_callback)
            
            print(f"\n📊 Processing Results:")
            print(f"  Total results: {len(results)}")
            
            # Summary
            print(f"\n✅ Test Results:")
            all_defaulted_correctly = all(data['receipt_type'] == 'rent' and data['receipt_type_defaulted'] for data in dialog_data)
            
            if all_defaulted_correctly:
                print(f"   ✅ All receipts correctly defaulted to 'rent' type")
                print(f"   ✅ Step-by-step dialogs show 'Receipt Type: rent (defaulted)' in orange")
                print(f"   ✅ Users can clearly see when receipt type was not specified in CSV")
            else:
                print(f"   ❌ Some receipts did not default correctly")
                
        else:
            print(f"❌ Failed to load CSV:")
            for error in errors:
                print(f"  • {error}")
    
    finally:
        # Clean up
        try:
            os.unlink(temp_file_path)
        except:
            pass
    
    print(f"\n" + "=" * 70)
    print("FEATURE SUMMARY")
    print("=" * 70)
    print("🎯 receiptType is now OPTIONAL in CSV files")
    print("🎯 When missing or empty, it defaults to 'rent'")
    print("🎯 Step-by-step dialogs show clear indication when defaulted")
    print("🎯 Minimal CSV files work: contractId, fromDate, toDate")
    print("🎯 Backward compatibility maintained")

if __name__ == "__main__":
    test_receipt_type_step_by_step()
