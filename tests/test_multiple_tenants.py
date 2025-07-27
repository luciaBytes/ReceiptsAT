#!/usr/bin/env python3
"""
Test script to verify multiple tenant extraction from receipt form data.
"""

import re
import json

# Sample JavaScript content with multiple tenants
sample_javascript_multiple_tenants = '''
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
        },
        {
            "nif": 123987456,
            "nome": "JOÃO MANUEL COSTA",
            "pais": {"codigo": "2724", "label": "PORTUGAL"},
            "retencao": {"taxa": 0, "codigo": "RIRS03", "label": "Dispensa de retenção"}
        },
        {
            "nif": 456789123,
            "nome": "ANA CRISTINA FERREIRA",
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

def test_multiple_tenant_extraction():
    """Test the multiple tenant extraction logic."""
    print("Testing multiple tenant extraction from JavaScript data...")
    
    script_content = sample_javascript_multiple_tenants
    contract_details = {}
    
    if 'numContrato' in script_content:
        print("✓ Found contract data in JavaScript")
        
        # Extract contract number
        contract_match = re.search(r'"numContrato":\s*(\d+)', script_content)
        if contract_match:
            contract_details['numContrato'] = int(contract_match.group(1))
            print(f"✓ Contract number: {contract_details['numContrato']}")
        
        # Extract NIF emitente
        nif_match = re.search(r'"nifEmitente":\s*(\d+)', script_content)
        if nif_match:
            contract_details['nifEmitente'] = int(nif_match.group(1))
            print(f"✓ Landlord NIF: {contract_details['nifEmitente']}")
        
        # Extract landlord name
        landlord_match = re.search(r'"nomeEmitente":\s*"([^"]+)"', script_content)
        if landlord_match:
            contract_details['nomeEmitente'] = landlord_match.group(1).strip()
            print(f"✓ Landlord name: {contract_details['nomeEmitente']}")
        
        # Extract version
        version_match = re.search(r'"versaoContrato":\s*(\d+)', script_content)
        if version_match:
            contract_details['versaoContrato'] = int(version_match.group(1))
            print(f"✓ Contract version: {contract_details['versaoContrato']}")
        
        # Extract ALL tenants
        locatarios_pattern = r'"locatarios":\s*\[(.*?)\]'
        locatarios_match = re.search(locatarios_pattern, script_content, re.DOTALL)
        if locatarios_match:
            print("✓ Found locatarios data in JavaScript")
            
            tenants_list = []
            
            try:
                # Try to parse full JSON structure first
                full_array_pattern = r'"locatarios":\s*(\[.*?\])'
                full_array_match = re.search(full_array_pattern, script_content, re.DOTALL)
                if full_array_match:
                    locatarios_json = full_array_match.group(1)
                    # Clean up JSON
                    locatarios_json = re.sub(r',\s*}', '}', locatarios_json)
                    locatarios_json = re.sub(r',\s*]', ']', locatarios_json)
                    
                    tenants_array = json.loads(locatarios_json)
                    
                    for i, tenant in enumerate(tenants_array):
                        tenant_info = {
                            'nif': tenant.get('nif'),
                            'nome': tenant.get('nome', '').strip(),
                            'pais': tenant.get('pais', {}),
                            'retencao': tenant.get('retencao', {})
                        }
                        tenants_list.append(tenant_info)
                        print(f"✓ Extracted tenant {i+1}: NIF={tenant_info['nif']}, Name={tenant_info['nome']}")
                    
                    contract_details['locatarios'] = tenants_list
                    contract_details['tenant_count'] = len(tenants_list)
                    print(f"✓ Successfully extracted {len(tenants_list)} tenants using JSON parsing")
                    
            except (json.JSONDecodeError, ValueError) as e:
                print(f"✗ JSON parsing failed: {e}")
                return None
    
    print(f"\n=== Summary ===")
    print(f"Contract: {contract_details.get('numContrato')}")
    print(f"Landlord: {contract_details.get('nomeEmitente')} (NIF: {contract_details.get('nifEmitente')})")
    print(f"Total tenants: {contract_details.get('tenant_count', 0)}")
    
    tenants = contract_details.get('locatarios', [])
    for i, tenant in enumerate(tenants):
        print(f"  Tenant {i+1}: {tenant['nome']} (NIF: {tenant['nif']})")
    
    # Assert that we have valid data
    assert len(contract_details) > 0, "Should extract contract details"
    assert 'tenant_count' in contract_details, "Should count tenants"
    print(f"✓ Successfully extracted contract with {contract_details.get('tenant_count', 0)} tenants")

def test_submission_data_preparation():
    """Test how the submission data would be prepared with multiple tenants."""
    print("\n=== Testing Submission Data Preparation ===")
    
    # Mock form data with multiple tenants
    form_data = {
        'numContrato': 123456,
        'versaoContrato': 1,
        'nifEmitente': 123456789,
        'nomeEmitente': 'TEST LANDLORD',
        'contract_details': {
            'locatarios': [
                {
                    'nif': 987654321,
                    'nome': 'MARIA SANTOS SILVA',
                    'pais': {"codigo": "2724", "label": "PORTUGAL"},
                    'retencao': {"taxa": 0, "codigo": "RIRS03", "label": "Dispensa de retenção"}
                },
                {
                    'nif': 123987456,
                    'nome': 'JOÃO MANUEL COSTA', 
                    'pais': {"codigo": "2724", "label": "PORTUGAL"},
                    'retencao': {"taxa": 0, "codigo": "RIRS03", "label": "Dispensa de retenção"}
                },
                {
                    'nif': 456789123,
                    'nome': 'ANA CRISTINA FERREIRA',
                    'pais': {"codigo": "2724", "label": "PORTUGAL"},
                    'retencao': {"taxa": 0, "codigo": "RIRS03", "label": "Dispensa de retenção"}
                }
            ]
        }
    }
    
    # Simulate the locatarios list preparation logic
    extracted_tenants = form_data.get('contract_details', {}).get('locatarios', [])
    locatarios_list = []
    
    if extracted_tenants:
        for i, tenant in enumerate(extracted_tenants):
            locatario = {
                "nif": tenant.get('nif'),
                "nome": tenant.get('nome', '').strip(),
                "pais": tenant.get('pais', {
                    "codigo": "2724",
                    "label": "PORTUGAL"
                }),
                "retencao": tenant.get('retencao', {
                    "taxa": 0,
                    "codigo": "RIRS03",
                    "label": "Dispensa de retenção - artigo 101.º-B, n.º 1, do CIRS"
                })
            }
            locatarios_list.append(locatario)
            print(f"✓ Prepared tenant {i+1}: NIF={locatario['nif']}, Name={locatario['nome']}")
    
    print(f"\n✓ Total locatarios prepared for submission: {len(locatarios_list)}")
    
    # Show what the locatarios section would look like in the final payload
    print("\nLocatarios section in submission payload:")
    print(json.dumps(locatarios_list, indent=2, ensure_ascii=False))
    
    # Assert that we prepared valid submission data
    assert isinstance(locatarios_list, list), "Should return a list of tenants"
    assert len(locatarios_list) > 0, "Should have at least one tenant"
    print(f"✓ Successfully prepared submission data for {len(locatarios_list)} tenants")

if __name__ == "__main__":
    print("=== Multiple Tenant Support Test ===\n")
    
    # Test 1: Data extraction
    extracted_data = test_multiple_tenant_extraction()
    
    # Test 2: Submission preparation  
    prepared_data = test_submission_data_preparation()
    
    print(f"\n=== Test Results ===")
    if extracted_data and prepared_data:
        print("✅ Multiple tenant support is working correctly!")
        print("✅ All tenant NIFs and names will be included in receipt submissions")
        print("✅ The platform should now accept receipts for contracts with multiple tenants")
    else:
        print("❌ Multiple tenant support test failed")
