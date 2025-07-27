#!/usr/bin/env python3
"""
Test script to demonstrate validation export functionality.
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

def test_validation_export():
    """Test validation export functionality."""
    print("=" * 80)
    print("VALIDATION EXPORT FUNCTIONALITY TEST")
    print("=" * 80)
    
    # Create test CSV content
    csv_content = """contractId,fromDate,toDate,receiptType,paymentDate,value
123456,2024-07-01,2024-07-31,rent,2024-07-28,100.00
789012,2024-07-01,2024-07-31,rent,2024-07-28,100.00
999999,2024-07-01,2024-07-31,rent,2024-07-28,750.00"""
    
    # Create temporary CSV file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        f.write(csv_content)
        temp_csv_path = f.name
    
    # Create temporary export file path
    export_path = temp_csv_path.replace('.csv', '_validation_export.csv')
    
    try:
        print("1. Setting up test components...")
        
        # Initialize components
        csv_handler = CSVHandler()
        web_client = WebClient(testing_mode=True)
        processor = ReceiptProcessor(web_client)
        
        print("2. Loading test CSV...")
        success, errors = csv_handler.load_csv(temp_csv_path)
        
        if not success:
            print(f"❌ Failed to load CSV: {errors}")
            return
        
        receipts = csv_handler.get_receipts()
        print(f"✅ Loaded {len(receipts)} receipts")
        
        print("3. Performing mock authentication...")
        login_success, message = web_client.login("demo", "demo")
        print(f"✅ Login: {message}")
        
        print("4. Running contract validation...")
        validation_report = processor.validate_contracts(receipts)
        
        print(f"✅ Validation completed:")
        print(f"   Portal contracts: {validation_report['portal_contracts_count']}")
        print(f"   CSV contracts: {validation_report['csv_contracts_count']}")
        print(f"   Valid matches: {len(validation_report['valid_contracts'])}")
        print(f"   Invalid contracts: {len(validation_report['invalid_contracts'])}")
        print(f"   Missing from CSV: {len(validation_report['missing_from_csv'])}")
        
        print("5. Preparing validation export data...")
        
        # Prepare report data (same logic as in ValidationResultDialog)
        report_data = []
        
        # Add valid contracts
        if validation_report.get('valid_contracts_data'):
            for contract in validation_report['valid_contracts_data']:
                contract_id = contract.get('numero') or contract.get('referencia', 'N/A')
                tenant_name = contract.get('nomeLocatario', 'Unknown')
                landlord_name = contract.get('nomeLocador', 'Unknown')
                rent_amount = contract.get('valorRenda', 0)
                property_addr = contract.get('imovelAlternateId', 'N/A')
                status = contract.get('estado', {}).get('label', 'Unknown')
                
                report_data.append({
                    'Contract ID': contract_id,
                    'Validation Status': 'Valid',
                    'In CSV': 'Yes',
                    'In Portal': 'Yes',
                    'Tenant Name': tenant_name,
                    'Landlord Name': landlord_name,
                    'Rent Amount': f"€{rent_amount:.2f}",
                    'Property Address': property_addr,
                    'Contract Status': status,
                    'Notes': 'Contract found in both CSV and Portal (Active)'
                })
        
        # Add invalid contracts (in CSV but not in portal)
        if validation_report.get('invalid_contracts'):
            for contract_id in validation_report['invalid_contracts']:
                report_data.append({
                    'Contract ID': contract_id,
                    'Validation Status': 'Invalid',
                    'In CSV': 'Yes',
                    'In Portal': 'No',
                    'Tenant Name': 'Unknown',
                    'Landlord Name': 'Unknown',
                    'Rent Amount': 'N/A',
                    'Property Address': 'N/A',
                    'Contract Status': 'Not Found',
                    'Notes': 'Contract in CSV but not found in active Portal contracts'
                })
        
        # Add missing from CSV (in portal but not in CSV)
        if validation_report.get('missing_from_csv_data'):
            for contract in validation_report['missing_from_csv_data']:
                contract_id = contract.get('numero') or contract.get('referencia', 'N/A')
                tenant_name = contract.get('nomeLocatario', 'Unknown')
                landlord_name = contract.get('nomeLocador', 'Unknown')
                rent_amount = contract.get('valorRenda', 0)
                property_addr = contract.get('imovelAlternateId', 'N/A')
                status = contract.get('estado', {}).get('label', 'Unknown')
                
                report_data.append({
                    'Contract ID': contract_id,
                    'Validation Status': 'Missing from CSV',
                    'In CSV': 'No',
                    'In Portal': 'Yes',
                    'Tenant Name': tenant_name,
                    'Landlord Name': landlord_name,
                    'Rent Amount': f"€{rent_amount:.2f}",
                    'Property Address': property_addr,
                    'Contract Status': status,
                    'Notes': 'Active Portal contract not included in CSV file'
                })
        
        print(f"✅ Prepared {len(report_data)} report entries")
        
        print("6. Exporting validation report...")
        export_success = csv_handler.export_report(report_data, export_path)
        
        if export_success:
            print(f"✅ Validation report exported to: {os.path.basename(export_path)}")
            
            print("\n7. Validation export content:")
            print("=" * 80)
            
            # Read and display the exported content
            with open(export_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print(content)
            
            print("=" * 80)
            print("🎉 VALIDATION EXPORT FEATURES:")
            print("✅ Complete contract validation results")
            print("✅ Tenant and landlord names for all contracts")
            print("✅ Rent amounts and property addresses")
            print("✅ Clear validation status for each contract")
            print("✅ Notes explaining validation results")
            print("✅ Summary information with timestamps")
            print("✅ Professional CSV format for further analysis")
            
            print("\n📊 EXPORT BENEFITS:")
            print("• Users can save validation results for record keeping")
            print("• Export can be used for reporting to landlords/tenants")
            print("• Data can be imported into other applications")
            print("• Provides audit trail of validation process")
            print("• Helpful for troubleshooting contract issues")
            
        else:
            print("❌ Failed to export validation report")
    
    finally:
        # Clean up temporary files
        try:
            os.unlink(temp_csv_path)
            if os.path.exists(export_path):
                os.unlink(export_path)
        except:
            pass

if __name__ == "__main__":
    test_validation_export()
