#!/usr/bin/env python3
"""
Test step-by-step skip functionality with tenant names.
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

def test_step_by_step_skip_with_tenant_names():
    """Test that skipped receipts in step-by-step mode include tenant names in the report."""
    print("=" * 70)
    print("STEP-BY-STEP SKIP WITH TENANT NAMES TEST")
    print("=" * 70)
    
    # Test CSV with receipts to skip
    csv_content = """contractId,fromDate,toDate,receiptType,paymentDate,value
123456,2024-07-01,2024-07-31,rent,2024-07-28,100.00
789012,2024-07-01,2024-07-31,rent,2024-07-28,100.00
345678,2024-07-01,2024-07-31,rent,2024-07-28,750.00"""
    
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
            
            # Mock contract data with tenant names
            mock_contracts = [
                {
                    "numero": "123456",
                    "valorRenda": 100.00,
                    "nomeLocador": "TEST LANDLORD",
                    "nomeLocatario": "Maria Santos Silva"
                },
                {
                    "numero": "789012", 
                    "valorRenda": 100.00,
                    "nomeLocador": "TEST LANDLORD",
                    "nomeLocatario": "João Manuel Costa"
                },
                {
                    "numero": "345678", 
                    "valorRenda": 750.00,
                    "nomeLocador": "TEST LANDLORD",
                    "nomeLocatario": "Ana Cristina Ferreira"
                }
            ]
            web_client._cached_contracts = mock_contracts
            
            processor = ReceiptProcessor(web_client)
            processor.dry_run = False
            
            # Mock get_receipt_form to return contract data with tenant names
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
            
            # Track processing actions
            processed_receipts = []
            
            def mock_confirmation_callback(receipt_data, form_data):
                contract_id = receipt_data.contract_id
                
                # Skip specific contracts for testing
                if contract_id == "123456":
                    print(f"\n📋 Skipping Contract {contract_id}")
                    processed_receipts.append({"action": "skip", "contract_id": contract_id})
                    return 'skip'
                elif contract_id == "789012":
                    print(f"\n📋 Confirming Contract {contract_id}")
                    processed_receipts.append({"action": "confirm", "contract_id": contract_id})
                    return 'confirm'
                else:
                    print(f"\n📋 Cancelling at Contract {contract_id}")
                    processed_receipts.append({"action": "cancel", "contract_id": contract_id})
                    return 'cancel'
            
            # Process receipts step-by-step
            print(f"\n🔄 Processing receipts in step-by-step mode...")
            results = processor.process_receipts_step_by_step(receipts, mock_confirmation_callback)
            
            print(f"\n📊 Processing Results:")
            print(f"  Total results: {len(results)}")
            
            # Verify that skipped receipts have tenant names
            skipped_results = [r for r in results if r.status == "Skipped"]
            confirmed_results = [r for r in results if r.status == "Success"]
            
            print(f"\n📋 Report Export Preview:")
            print("Contract ID | Tenant Name | Status | From Date | To Date | Value")
            print("-" * 70)
            
            for result in results:
                tenant_display = result.tenant_name if result.tenant_name else "NO NAME"
                print(f"{result.contract_id:11} | {tenant_display:20} | {result.status:7} | {result.from_date} | {result.to_date} | €{result.value:.2f}")
            
            # Validation
            print(f"\n✅ Test Results:")
            
            # Check that skipped receipts have tenant names
            skipped_with_names = [r for r in skipped_results if r.tenant_name and r.tenant_name != "Unknown Tenant"]
            if skipped_with_names:
                print(f"   ✅ {len(skipped_with_names)} skipped receipt(s) have tenant names:")
                for result in skipped_with_names:
                    print(f"      - Contract {result.contract_id}: {result.tenant_name}")
            else:
                print(f"   ❌ No skipped receipts have tenant names")
            
            # Check that confirmed receipts also have tenant names
            confirmed_with_names = [r for r in confirmed_results if r.tenant_name and r.tenant_name != "Unknown Tenant"]
            if confirmed_with_names:
                print(f"   ✅ {len(confirmed_with_names)} confirmed receipt(s) have tenant names:")
                for result in confirmed_with_names:
                    print(f"      - Contract {result.contract_id}: {result.tenant_name}")
            
            # Summary
            if len(skipped_with_names) > 0:
                print(f"\n🎉 SUCCESS: Skipped receipts now include tenant names in report!")
                print(f"   This means the exported CSV will show who the tenant is even for skipped receipts.")
            else:
                print(f"\n❌ FAILURE: Skipped receipts still don't have tenant names.")
                
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
    test_step_by_step_skip_with_tenant_names()
