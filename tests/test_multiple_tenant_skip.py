#!/usr/bin/env python3
"""
Test step-by-step skip functionality with multiple tenant names.
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

def test_step_by_step_skip_multiple_tenants():
    """Test that skipped receipts with multiple tenants show combined names."""
    print("=" * 70)
    print("STEP-BY-STEP SKIP WITH MULTIPLE TENANTS TEST")
    print("=" * 70)
    
    # Test CSV
    csv_content = """contractId,fromDate,toDate,receiptType,paymentDate,value
123456,2024-07-01,2024-07-31,rent,2024-07-28,100.00"""
    
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
            print(f"✅ Loaded {len(receipts)} receipts from CSV")
            
            # Test step-by-step processing with mock web client
            web_client = WebClient()
            web_client.testing_mode = True
            web_client.authenticated = True
            
            processor = ReceiptProcessor(web_client)
            processor.dry_run = False
            
            # Mock get_receipt_form to return contract data with multiple tenants
            def mock_get_receipt_form(contract_id):
                if contract_id == "123456":
                    return True, {
                        'contract_details': {
                            'valorRenda': 100.00,
                            'locatarios': [
                                {'nome': 'Maria Santos Silva'},
                                {'nome': 'João Manuel Costa'}
                            ],
                            'locadores': [{'nome': 'TEST LANDLORD'}]
                        }
                    }
                return False, {}
                
            web_client.get_receipt_form = mock_get_receipt_form
            
            # Skip the receipt to test tenant name extraction
            def mock_confirmation_callback(receipt_data, form_data):
                print(f"\n📋 Skipping Contract {receipt_data.contract_id} (Multiple Tenants)")
                return 'skip'
            
            # Process receipts step-by-step
            print(f"\n🔄 Processing receipts in step-by-step mode...")
            results = processor.process_receipts_step_by_step(receipts, mock_confirmation_callback)
            
            print(f"\n📊 Processing Results:")
            
            for result in results:
                print(f"Contract ID: {result.contract_id}")
                print(f"Tenant Name: {result.tenant_name}")
                print(f"Status: {result.status}")
                print(f"Value: €{result.value:.2f}")
                
                # Validate multiple tenant name format
                if "tenants)" in result.tenant_name:
                    print(f"✅ Multiple tenant format detected: '{result.tenant_name}'")
                elif result.tenant_name and result.tenant_name != "Unknown Tenant":
                    print(f"✅ Single tenant name: '{result.tenant_name}'")
                else:
                    print(f"❌ No tenant name found")
                
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

if __name__ == "__main__":
    test_step_by_step_skip_multiple_tenants()
