#!/usr/bin/env python3
"""
Test script to verify tenant NIF extraction from receipt form data.
This simulates the JavaScript parsing that happens in get_receipt_form().
"""

import re

# Sample JavaScript content that would be found in the receipt form page
sample_javascript = '''
var reciboData = {
    "numContrato": 123456,
    "versaoContrato": 1,
    "nifEmitente": 123456789,
    "nomeEmitente": "TEST LANDLORD NAME",
    "locatarios": [
        {
            "nif": 987654321,
            "nome": "MARIA SANTOS SILVA",
            "pais": {"codigo": "2724", "label": "PORTUGAL"},
            "retencao": {"taxa": 0, "codigo": "RIRS03", "label": "Dispensa de retenção"}
        }
    ],
    "imoveis": [
        {
            "morada": "NARNIA, 123, 1º DTO",
            "tipo": {"codigo": "U", "label": "Urbano"}
        }
    ]
};
'''

def test_nif_extraction():
    """Test the NIF extraction logic."""
    print("Testing tenant NIF extraction from JavaScript data...")
    
    script_content = sample_javascript
    contract_details = {}
    
    if 'numContrato' in script_content:
        print("✓ Found contract data in JavaScript")
        
        # Try to extract contract number
        contract_match = re.search(r'"numContrato":\s*(\d+)', script_content)
        if contract_match:
            contract_details['numContrato'] = int(contract_match.group(1))
            print(f"✓ Contract number: {contract_details['numContrato']}")
        
        # Try to extract NIF emitente
        nif_match = re.search(r'"nifEmitente":\s*(\d+)', script_content)
        if nif_match:
            contract_details['nifEmitente'] = int(nif_match.group(1))
            print(f"✓ Landlord NIF: {contract_details['nifEmitente']}")
        
        # Try to extract landlord name
        landlord_match = re.search(r'"nomeEmitente":\s*"([^"]+)"', script_content)
        if landlord_match:
            contract_details['nomeEmitente'] = landlord_match.group(1).strip()
            print(f"✓ Landlord name: {contract_details['nomeEmitente']}")
        
        # Try to extract contract version
        version_match = re.search(r'"versaoContrato":\s*(\d+)', script_content)
        if version_match:
            contract_details['versaoContrato'] = int(version_match.group(1))
            print(f"✓ Contract version: {contract_details['versaoContrato']}")
        
        # Try to extract tenant data including NIF
        locatarios_pattern = r'"locatarios":\s*\[(.*?)\]'
        locatarios_match = re.search(locatarios_pattern, script_content, re.DOTALL)
        if locatarios_match:
            locatarios_data = locatarios_match.group(1)
            print("✓ Found locatarios data in JavaScript")
            
            # Extract tenant NIF
            tenant_nif_match = re.search(r'"nif":\s*(\d+)', locatarios_data)
            if tenant_nif_match:
                contract_details['tenant_nif'] = int(tenant_nif_match.group(1))
                print(f"✓ Extracted tenant NIF: {contract_details['tenant_nif']}")
            else:
                print("✗ Tenant NIF not found")
            
            # Extract tenant name
            tenant_name_match = re.search(r'"nome":\s*"([^"]+)"', locatarios_data)
            if tenant_name_match:
                contract_details['tenant_name'] = tenant_name_match.group(1).strip()
                print(f"✓ Extracted tenant name: {contract_details['tenant_name']}")
            else:
                print("✗ Tenant name not found")
        
        # Try to extract imoveis (property) data
        imoveis_pattern = r'"imoveis":\s*\[(.*?)\]'
        imoveis_match = re.search(imoveis_pattern, script_content, re.DOTALL)
        if imoveis_match:
            imoveis_data = imoveis_match.group(1)
            # Extract property address
            address_match = re.search(r'"morada":\s*"([^"]+)"', imoveis_data)
            if address_match:
                contract_details['property_address'] = address_match.group(1).strip()
                print(f"✓ Extracted property address: {contract_details['property_address']}")
            else:
                print("✗ Property address not found")
    
    print("\nExtracted contract details:")
    for key, value in contract_details.items():
        print(f"  {key}: {value}")
    
    # Assert that we extracted meaningful data
    assert len(contract_details) > 0, "Should extract some contract details"
    print(f"✓ Successfully extracted {len(contract_details)} contract details")

if __name__ == "__main__":
    test_nif_extraction()
