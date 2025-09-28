#!/usr/bin/env python3
"""
Test that prefilled CSV generation only includes active contracts.
"""

import sys
import os
import tempfile
from unittest.mock import patch
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

from web_client import WebClient
from utils.logger import get_logger

logger = get_logger(__name__)

@patch.object(WebClient, '__init__')
@patch.object(WebClient, 'get_contracts_with_tenant_data')
def test_prefilled_csv_active_filtering(mock_get_contracts, mock_init):
    """
    Test that prefilled CSV generation only includes active contracts.
    """
    print("🔍 TESTING PREFILLED CSV ACTIVE FILTERING")
    print("=" * 45)
    
    # Mock WebClient initialization to avoid real HTTP session creation
    mock_init.return_value = None
    
    # Mock contracts with different statuses
    mock_contracts = [
        {
            "numero": "123456",
            "referencia": "CT123456", 
            "nomeLocador": "Landlord 1",
            "nomeLocatario": "Active Tenant",
            "valorRenda": 500.00,
            "estado": {"codigo": "ACTIVO", "label": "Ativo"}
        },
        {
            "numero": "789012",
            "referencia": "CT789012",
            "nomeLocador": "Landlord 2", 
            "nomeLocatario": "Inactive Tenant",
            "valorRenda": 750.00,
            "estado": {"codigo": "TERMINADO", "label": "Terminado"}
        },
        {
            "numero": "111222",
            "referencia": "CT111222",
            "nomeLocador": "Landlord 3", 
            "nomeLocatario": "Another Active Tenant",
            "valorRenda": 600.00,
            "estado": {"codigo": "ACTIVO", "label": "Ativo"}
        }
    ]
    mock_get_contracts.return_value = (True, mock_contracts, "Mock success")
    
    print("Testing with mock contracts:")
    print("-" * 30)
    for contract in mock_contracts:
        contract_id = contract.get('numero')
        tenant = contract.get('nomeLocatario')
        rent = contract.get('valorRenda')
        status = contract.get('estado', {})
        status_label = status.get('label', 'Unknown') if isinstance(status, dict) else status
        print(f"  • Contract {contract_id}: {tenant} - €{rent} ({status_label})")
    
    web_client = WebClient()
    web_client.authenticated = True  # Mock authentication
    
    print()
    print("1️⃣ Generate prefilled CSV:")
    print("-" * 30)
    
    # Create a temporary directory for the CSV file
    with tempfile.TemporaryDirectory() as temp_dir:
        success, result = web_client.generate_prefilled_csv(save_directory=temp_dir)
        
        if success:
            print(f"✅ CSV generation successful: {os.path.basename(result)}")
            
            # Read and analyze the CSV content
            with open(result, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.strip().split('\n')
                
                print(f"📄 CSV contains {len(lines)} lines (including header)")
                print("\n📋 CSV Content:")
                for i, line in enumerate(lines):
                    if i == 0:
                        print(f"  Header: {line}")
                    else:
                        print(f"  Row {i}: {line}")
                
                # Verify only active contracts are included
                print("\n🔍 Active Contract Filtering Verification:")
                print("-" * 45)
                
                # Check for active contracts
                if '123456' in content:
                    print("✅ Active contract 123456 (Active Tenant) included")
                else:
                    print("❌ Active contract 123456 missing!")
                
                if '111222' in content:
                    print("✅ Active contract 111222 (Another Active Tenant) included")
                else:
                    print("❌ Active contract 111222 missing!")
                
                # Check that inactive contract is excluded
                if '789012' not in content:
                    print("✅ Inactive contract 789012 (Inactive Tenant) correctly excluded")
                else:
                    print("❌ Inactive contract 789012 should be excluded but was found!")
                
                # Count data rows (excluding header)
                data_rows = len(lines) - 1
                expected_active_contracts = 2  # Only contracts with ACTIVO status
                
                print(f"\n📊 Summary:")
                print(f"  • Total contracts in mock data: 3")
                print(f"  • Active contracts (ACTIVO): 2")
                print(f"  • Inactive contracts (TERMINADO): 1")
                print(f"  • CSV data rows: {data_rows}")
                
                if data_rows == expected_active_contracts:
                    print("✅ CSV contains correct number of active contracts only")
                else:
                    print(f"❌ Expected {expected_active_contracts} rows, got {data_rows}")
        else:
            print(f"❌ CSV generation failed: {result}")
    
    print("\n🎯 Active Filtering Benefits for Prefilled CSV:")
    print("-" * 50)
    print("✅ Only generates CSV rows for contracts that can receive receipts")
    print("✅ Excludes terminated/cancelled contracts from CSV")
    print("✅ Reduces clutter in generated CSV files")
    print("✅ Prevents errors when processing inactive contracts")
    print("✅ Focuses on actionable contract data for receipt generation")

if __name__ == "__main__":
    test_prefilled_csv_active_filtering()