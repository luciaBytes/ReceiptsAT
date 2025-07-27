#!/usr/bin/env python3
"""
Test validation export with the actual sample_report_heranca.csv file.
"""

import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.csv_handler import CSVHandler
from src.web_client import WebClient
from src.receipt_processor import ReceiptProcessor
from src.utils.logger import get_logger

logger = get_logger(__name__)

def test_validation_export_with_sample():
    """Test validation export with the actual sample file."""
    print("=" * 80)
    print("VALIDATION EXPORT WITH RECIBOS_JULHO.CSV")
    print("=" * 80)
    
    # Use the actual sample file
    sample_file = os.path.join(project_root, 'sample', 'recibos_julho.csv')
    export_file = os.path.join(project_root, 'sample', 'validation_report_julho.csv')
    
    if not os.path.exists(sample_file):
        print(f"❌ Sample file not found: {sample_file}")
        return
    
    print(f"Using sample file: {os.path.basename(sample_file)}")
    
    try:
        print("\n1. Setting up components...")
        csv_handler = CSVHandler()
        web_client = WebClient(testing_mode=True)
        processor = ReceiptProcessor(web_client)
        
        print("2. Loading sample CSV...")
        success, errors = csv_handler.load_csv(sample_file)
        
        if not success:
            print(f"❌ Failed to load CSV: {errors}")
            return
        
        receipts = csv_handler.get_receipts()
        print(f"✅ Loaded {len(receipts)} receipts from sample file")
        
        # Show first few contracts
        print(f"\nSample contracts:")
        for i, receipt in enumerate(receipts[:5], 1):
            print(f"  {i}. Contract {receipt.contract_id} - {receipt.from_date} to {receipt.to_date}")
        if len(receipts) > 5:
            print(f"  ... and {len(receipts) - 5} more")
        
        print("\n3. Authenticating...")
        login_success, message = web_client.login("demo", "demo")
        print(f"✅ {message}")
        
        print("4. Running validation...")
        validation_report = processor.validate_contracts(receipts)
        
        print(f"\n📊 VALIDATION SUMMARY:")
        print(f"   Portal contracts (active): {validation_report['portal_contracts_count']}")
        print(f"   CSV contracts: {validation_report['csv_contracts_count']}")
        print(f"   Valid matches: {len(validation_report['valid_contracts'])}")
        print(f"   Invalid contracts: {len(validation_report['invalid_contracts'])}")
        print(f"   Missing from CSV: {len(validation_report['missing_from_csv'])}")
        
        if validation_report.get('invalid_contracts'):
            print(f"\n❌ Invalid contracts (in CSV but not in active portal):")
            for contract_id in validation_report['invalid_contracts']:
                print(f"     • {contract_id}")
        
        if validation_report.get('missing_from_csv'):
            print(f"\n⚠️ Active portal contracts not in CSV:")
            for contract_id in validation_report['missing_from_csv']:
                print(f"     • {contract_id}")
        
        print("\n5. Preparing export data...")
        
        # Prepare report data
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
        
        # Add invalid contracts
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
        
        # Add missing from CSV
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
        
        print(f"✅ Prepared {len(report_data)} validation entries")
        
        print("\n6. Exporting validation report...")
        export_success = csv_handler.export_report(report_data, export_file)
        
        if export_success:
            print(f"✅ Validation report exported to: {os.path.basename(export_file)}")
            
            # Show file size and sample content
            file_size = os.path.getsize(export_file)
            print(f"   File size: {file_size} bytes")
            
            print(f"\n📄 Sample export content (first 10 lines):")
            print("-" * 80)
            with open(export_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for i, line in enumerate(lines[:10], 1):
                    print(f"{i:2}: {line.rstrip()}")
                if len(lines) > 10:
                    print(f"... and {len(lines) - 10} more lines")
            print("-" * 80)
            
            print(f"\n🎯 VALIDATION EXPORT COMPLETE!")
            print(f"📁 Export file: {export_file}")
            print(f"📊 Total validation entries: {len(report_data)}")
            print(f"✅ Users can now export validation results to CSV for:")
            print(f"   • Record keeping and audit trails")
            print(f"   • Sharing with landlords or tenants")
            print(f"   • Further analysis in Excel or other tools")
            print(f"   • Troubleshooting contract validation issues")
            
        else:
            print("❌ Failed to export validation report")
    
    except Exception as e:
        print(f"❌ Error during test: {e}")

if __name__ == "__main__":
    test_validation_export_with_sample()
