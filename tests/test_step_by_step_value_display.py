#!/usr/bin/env python3
"""
Test step-by-step value display fix.
"""

import sys
import os
import tempfile
from unittest.mock import Mock, patch

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.csv_handler import CSVHandler
from src.web_client import WebClient
from src.receipt_processor import ReceiptProcessor
from src.utils.logger import get_logger

logger = get_logger(__name__)

def test_step_by_step_value_display():
    """Test that step-by-step dialog shows appropriate value information when CSV value is missing."""
    print("=" * 70)
    print("STEP-BY-STEP VALUE DISPLAY TEST")
    print("=" * 70)
    
    # Test CSV with missing values
    csv_content = """contractId,fromDate,toDate,receiptType,paymentDate
123456,2024-07-01,2024-07-31,rent,2024-07-28
789012,2024-07-01,2024-07-31,rent,2024-07-28"""
    
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
            
            # Check if value_defaulted flag is set correctly
            for i, receipt in enumerate(receipts):
                print(f"\nReceipt {i+1}:")
                print(f"  Contract ID: {receipt.contract_id}")
                print(f"  Value: €{receipt.value:.2f}")
                print(f"  Value defaulted: {receipt.value_defaulted}")
                
                # Verify that missing values are flagged correctly
                if receipt.value == 0.0 and receipt.value_defaulted:
                    print(f"  ✅ Correctly identified missing value from CSV")
                elif receipt.value > 0.0 and not receipt.value_defaulted:
                    print(f"  ✅ Correctly identified explicit value from CSV")
                else:
                    print(f"  ❌ Unexpected value/flag combination")
            
            # Test step-by-step processing with mock web client
            web_client = WebClient()
            web_client.testing_mode = True
            web_client.authenticated = True
            
            # Mock contract data with rental values
            mock_contracts = [
                {
                    "numero": "123456",
                    "valorRenda": 100.00,
                    "nomeLocador": "TEST LANDLORD",
                    "nomeLocatario": "Test Tenant 1"
                },
                {
                    "numero": "789012", 
                    "valorRenda": 100.00,
                    "nomeLocador": "TEST LANDLORD",
                    "nomeLocatario": "Test Tenant 2"
                }
            ]
            web_client._cached_contracts = mock_contracts
            
            processor = ReceiptProcessor(web_client)
            processor.dry_run = False
            
            # Mock get_receipt_form to return contract data
            def mock_get_receipt_form(contract_id):
                for contract in mock_contracts:
                    if str(contract['numero']) == str(contract_id):
                        return True, {
                            'contract_details': {
                                'valorRenda': contract['valorRenda'],
                                'locatarios': [{'nome': contract['nomeLocatario']}],
                                'locadores': [{'nome': contract['nomeLocador']}]
                            }
                        }
                return False, {}
                
            web_client.get_receipt_form = mock_get_receipt_form
            
            # Track confirmation dialogs
            dialog_calls = []
            
            def mock_confirmation_callback(receipt_data, form_data):
                dialog_calls.append({
                    'contract_id': receipt_data.contract_id,
                    'value': receipt_data.value,
                    'value_defaulted': getattr(receipt_data, 'value_defaulted', False)
                })
                print(f"\n📋 Step-by-Step Dialog for Contract {receipt_data.contract_id}:")
                print(f"   Value displayed: €{receipt_data.value:.2f}")
                if hasattr(receipt_data, 'value_defaulted') and receipt_data.value_defaulted:
                    if receipt_data.value > 0.0:
                        print(f"   Status: ✅ Shows contract value (defaulted from contract)")
                    else:
                        print(f"   Status: ⚠️  Shows €0.00 (not specified in CSV)")
                else:
                    print(f"   Status: ✅ Shows explicit CSV value")
                return 'confirm'
            
            # Process receipts step-by-step
            print(f"\n🔄 Processing receipts in step-by-step mode...")
            results = processor.process_receipts_step_by_step(receipts, mock_confirmation_callback)
            
            print(f"\n📊 Results:")
            print(f"  Total dialogs shown: {len(dialog_calls)}")
            print(f"  Receipts processed: {len(results)}")
            
            # Verify dialog calls showed appropriate values
            for call in dialog_calls:
                if call['value'] > 0.0:
                    print(f"  ✅ Contract {call['contract_id']}: Dialog showed €{call['value']:.2f}")
                else:
                    print(f"  ⚠️  Contract {call['contract_id']}: Dialog showed €{call['value']:.2f} (will be resolved during processing)")
            
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
    test_step_by_step_value_display()
