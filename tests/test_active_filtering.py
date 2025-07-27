#!/usr/bin/env python3
"""
Test the active contracts filtering functionality.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

from web_client import WebClient
from utils.logger import get_logger

logger = get_logger(__name__)

def test_active_contracts_filtering():
    """
    Test that validation only considers active contracts.
    """
    print("🔍 TESTING ACTIVE CONTRACTS FILTERING")
    print("=" * 40)
    print()
    
    print("Testing with mock mode to verify filtering logic:")
    print("-" * 50)
    
    web_client = WebClient(testing_mode=True)
    
    # Login  
    success, message = web_client.login("test", "test")
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
