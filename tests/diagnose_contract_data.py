#!/usr/bin/env python3
"""
Diagnostic script to check tenant NIF extraction from actual contract forms.
Run this after authenticating to see what data is available for your contracts.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from web_client import WebClient

def diagnose_contract_data():
    """Check what data is available for contract forms."""
    
    print("=== Contract Data Diagnostic ===\n")
    
    # Create web client in production mode
    web_client = WebClient(testing_mode=False)
    print("✓ Web client created (production mode)")
    
    # Check if authenticated (you need to login first)
    if not web_client.is_authenticated():
        print("✗ Not authenticated. Please login through the main application first.")
        print("Then run this diagnostic to check your contract data.")
        return
    
    print("✓ Authentication status verified")
    
    # Get contracts list
    print("\n--- Getting Contracts List ---")
    success, contracts_data, message = web_client.get_contracts_with_tenant_data()
    
    if not success:
        print(f"✗ Failed to get contracts: {message}")
        return
    
    print(f"✓ Retrieved {len(contracts_data)} contracts")
    
    # Show sample contract data
    if contracts_data:
        sample_contract = contracts_data[0]
        print("\nSample contract data available:")
        for key, value in sample_contract.items():
            print(f"  {key}: {value}")
        
        contract_id = str(sample_contract.get('numero', ''))
        print(f"\n--- Testing Form Data for Contract {contract_id} ---")
        
        # Get receipt form data
        success, form_data = web_client.get_receipt_form(contract_id)
        
        if success and form_data:
            print("✓ Form data retrieved successfully")
            print("\nForm data keys:")
            for key in form_data.keys():
                print(f"  {key}")
            
            # Check for extracted tenant data
            extracted_tenants = form_data.get('contract_details', {}).get('locatarios', [])
            tenant_count = form_data.get('contract_details', {}).get('tenant_count', 0)
            
            # Check for extracted landlord data
            extracted_landlords = form_data.get('contract_details', {}).get('locadores', [])
            landlord_count = form_data.get('contract_details', {}).get('landlord_count', 0)
            
            print(f"\nExtracted data:")
            print(f"  Landlord count: {landlord_count}")
            print(f"  Tenant count: {tenant_count}")
            
            if extracted_landlords:
                print("  All landlords:")
                for i, landlord in enumerate(extracted_landlords):
                    nif = landlord.get('nif')
                    name = landlord.get('nome', '').strip()
                    quota = landlord.get('quotaParte', '1/1')
                    print(f"    Landlord {i+1}: {name} (NIF: {nif}, Quota: {quota})")
                    
                if all(landlord.get('nif') for landlord in extracted_landlords):
                    print("✓ All landlord NIFs found")
                else:
                    print("✗ Some landlord NIFs missing")
                    for i, landlord in enumerate(extracted_landlords):
                        if not landlord.get('nif'):
                            print(f"    Missing NIF for landlord {i+1}: {landlord.get('nome', 'Unknown')}")
            
            if extracted_tenants:
                print("  All tenants:")
                for i, tenant in enumerate(extracted_tenants):
                    nif = tenant.get('nif')
                    name = tenant.get('nome', '').strip()
                    print(f"    Tenant {i+1}: {name} (NIF: {nif})")
                    
                if all(tenant.get('nif') for tenant in extracted_tenants):
                    print("✓ All tenant NIFs found - receipts should work correctly")
                else:
                    print("✗ Some tenant NIFs missing - receipts may fail")
                    for i, tenant in enumerate(extracted_tenants):
                        if not tenant.get('nif'):
                            print(f"    Missing NIF for tenant {i+1}: {tenant.get('nome', 'Unknown')}")
            else:
                # Fallback to single tenant extraction
                tenant_nif = form_data.get('tenant_nif') or form_data.get('contract_details', {}).get('tenant_nif')
                tenant_name = form_data.get('tenant_name') or form_data.get('contract_details', {}).get('tenant_name')
                
                print(f"  Single tenant extraction:")
                print(f"    Tenant NIF: {tenant_nif}")
                print(f"    Tenant Name: {tenant_name}")
                
                if tenant_nif:
                    print("✓ Tenant NIF found - receipts should work correctly")
                else:
                    print("✗ Tenant NIF not found - receipts will fail")
                    print("  The platform requires tenant NIF for receipt submission")
        else:
            print("✗ Failed to get form data")
    else:
        print("No contracts available")

if __name__ == "__main__":
    diagnose_contract_data()
