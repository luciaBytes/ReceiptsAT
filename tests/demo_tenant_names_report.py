#!/usr/bin/env python3
"""
Demonstration of tenant names in exported reports for skipped receipts.
"""

import sys
import os
import tempfile

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from csv_handler import CSVHandler
from web_client import WebClient
from receipt_processor import ReceiptProcessor
from utils.logger import get_logger

logger = get_logger(__name__)

def demonstrate_tenant_names_in_report():
    """Demonstrate how tenant names appear in exported reports for skipped receipts."""
    print("=" * 80)
    print("TENANT NAMES IN EXPORTED REPORTS - DEMONSTRATION")
    print("=" * 80)
    
    # Create a temporary CSV file with receipts
    csv_content = """contractId,fromDate,toDate,receiptType,paymentDate,value
123456,2024-07-01,2024-07-31,rent,2024-07-28,100.00
789012,2024-07-01,2024-07-31,rent,2024-07-28,100.00"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        f.write(csv_content)
        temp_file_path = f.name
    
    # Create a temporary report file
    report_file_path = temp_file_path.replace('.csv', '_report.csv')
    
    try:
        # Load CSV
        csv_handler = CSVHandler()
        success, errors = csv_handler.load_csv(temp_file_path)
        
        if success:
            receipts = csv_handler.get_receipts()
            print(f"📂 Loaded {len(receipts)} receipts from CSV")
            
            # Setup mock web client with tenant data
            web_client = WebClient()
            # Demo mode
            web_client.authenticated = True
            
            processor = ReceiptProcessor(web_client)
            processor.dry_run = False
            
            def mock_get_receipt_form(contract_id):
                if contract_id == "123456":
                    return True, {
                        'contract_details': {
                            'valorRenda': 100.00,
                            'locatarios': [{'nome': 'Ana Maria Santos'}],
                            'locadores': [{'nome': 'TEST LANDLORD'}]
                        }
                    }
                elif contract_id == "789012":
                    return True, {
                        'contract_details': {
                            'valorRenda': 100.00,
                            'locatarios': [
                                {'nome': 'Carlos João Silva'},
                                {'nome': 'Maria Fernanda Costa'}
                            ],
                            'locadores': [{'nome': 'TEST LANDLORD'}]
                        }
                    }
                return False, {}
                
            web_client.get_receipt_form = mock_get_receipt_form
            
            # Process step-by-step with mixed actions
            def mock_confirmation_callback(receipt_data, form_data):
                if receipt_data.contract_id == "123456":
                    print(f"   👤 Contract {receipt_data.contract_id}: Ana Maria Santos - SKIPPING")
                    return 'skip'
                else:
                    print(f"   👥 Contract {receipt_data.contract_id}: Multiple tenants - CONFIRMING")
                    return 'confirm'
            
            print(f"\n🔄 Processing receipts step-by-step...")
            results = processor.process_receipts_step_by_step(receipts, mock_confirmation_callback)
            
            # Create report data in the format used by the application
            report_data = []
            for result in results:
                report_data.append({
                    'Contract ID': result.contract_id,
                    'Tenant Name': result.tenant_name,
                    'Status': result.status,
                    'Receipt Number': result.receipt_number,
                    'From Date': result.from_date,
                    'To Date': result.to_date,
                    'Payment Date': result.payment_date,
                    'Value': result.value,
                    'Error Message': result.error_message,
                    'Timestamp': result.timestamp
                })
            
            # Export to CSV report
            export_success = csv_handler.export_report(report_data, report_file_path)
            
            if export_success:
                print(f"\n📋 Report exported to: {os.path.basename(report_file_path)}")
                print(f"\n📄 Report Contents:")
                print("=" * 80)
                
                # Read and display the report
                with open(report_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print(content)
                
                print("=" * 80)
                print(f"\n✅ SUCCESS DEMONSTRATION:")
                print(f"   • Skipped receipt (123456) shows tenant name: 'Ana Maria Santos'")
                print(f"   • Confirmed receipt (789012) shows multiple tenants: 'Carlos João Silva, Maria Fernanda Costa (2 tenants)'")
                print(f"   • Both receipts have complete information for reporting")
                print(f"\n🎯 BENEFIT:")
                print(f"   Users can now see who the tenant is even for receipts that were skipped")
                print(f"   during step-by-step processing, making reports much more useful!")
                
            else:
                print(f"❌ Failed to export report")
                
        else:
            print(f"❌ Failed to load CSV: {errors}")
    
    finally:
        # Clean up
        try:
            os.unlink(temp_file_path)
            os.unlink(report_file_path)
        except:
            pass

if __name__ == "__main__":
    demonstrate_tenant_names_in_report()
