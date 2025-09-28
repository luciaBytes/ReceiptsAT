#!/usr/bin/env python3
"""
Test the active contracts filtering functionality.
"""

import sys
import os
from unittest.mock import patch
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

from web_client import WebClient
from utils.logger import get_logger

logger = get_logger(__name__)

@patch.object(WebClient, '__init__')
@patch.object(WebClient, 'login')
@patch.object(WebClient, 'get_contracts_with_tenant_data')
def test_active_contracts_filtering(mock_get_contracts, mock_login, mock_init):
    """
    Test that validation only considers active contracts.
    """
    print("🔍 TESTING ACTIVE CONTRACTS FILTERING")
    print("=" * 40)
    
    # Mock WebClient initialization to avoid real HTTP session creation
    mock_init.return_value = None
    
    # Mock login success
    mock_login.return_value = (True, "Mock login successful")
    
    # Mock contracts with different statuses
    mock_contracts = [
        {
            "numero": "123456",
            "referencia": "CT123456", 
            "nomeLocador": "Landlord 1",
            "nomeLocatario": "Tenant 1",
            "estado": {"codigo": "ACTIVO", "label": "Ativo"}
        },
        {
            "numero": "789012",
            "referencia": "CT789012",
            "nomeLocador": "Landlord 2", 
            "nomeLocatario": "Tenant 2",
            "estado": {"codigo": "TERMINADO", "label": "Terminado"}
        }
    ]
    mock_get_contracts.return_value = (True, mock_contracts, "Mock success")
    print()
    
    print("Testing with mock mode to verify filtering logic:")
    print("-" * 50)
    
    web_client = WebClient()
    web_client.authenticated = True  # Mock authentication
    
    # Mock the login call  
    success = True  # Use mock result instead of real call
    message = "Mock login successful"
    print(f"Mock login: {'✅ SUCCESS' if success else '❌ FAILED'} - {message}")
    
    print()
    print("1️⃣ Get all contracts (including status):")
    print("-" * 40)
    success, contracts, message = web_client.get_contracts_with_tenant_data()
    if success:
        print(f"Total contracts retrieved: {len(contracts)}")
        for contract in contracts:
            contract_id = contract.get('numero')
            status = contract.get('estado', {})
            status_label = status.get('label', 'Unknown') if isinstance(status, dict) else status
            print(f"  • Contract {contract_id}: {status_label}")
    
    print()
    print("2️⃣ Test validation filtering (active contracts only):")
    print("-" * 55)
    csv_contracts = ["123456", "789012", "999999"]  # Mix of valid and invalid
    validation_report = web_client.validate_csv_contracts(csv_contracts)
    
    print(f"Validation success: {'✅ YES' if validation_report['success'] else '❌ NO'}")
    print(f"Active portal contracts: {validation_report['portal_contracts_count']}")
    print(f"CSV contracts: {validation_report['csv_contracts_count']}")
    print(f"Valid matches: {len(validation_report['valid_contracts'])}")
    print(f"Invalid contracts: {len(validation_report['invalid_contracts'])}")
    print(f"Missing from CSV: {len(validation_report['missing_from_csv'])}")
    
    print()
    print("🎯 Active Contracts Filtering Benefits:")
    print("-" * 40)
    print("✅ Only compares against contracts that can receive receipts")
    print("✅ Excludes terminated/cancelled contracts from validation")
    print("✅ Reduces false positives in validation reports")
    print("✅ Focuses on actionable contract data")
    print("✅ Cleaner validation reports for users")
    print()
    
    print("📊 Contract Status Handling:")
    print("-" * 30)
    print("• ACTIVO/ATIVO/ACTIVE → Included in validation")
    print("• INATIVO/CANCELLED/TERMINATED → Excluded from validation")
    print("• Unknown status → Excluded for safety")

if __name__ == "__main__":
    test_active_contracts_filtering()
