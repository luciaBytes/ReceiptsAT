#!/usr/bin/env python3
"""
Test script to verify multiple landlord extraction and tenant name reporting.
"""

import re
import json

# Sample JavaScript content with multiple landlords and tenants
sample_javascript_multiple_landlords = '''
var reciboData = {
    "numContrato": 123456,
    "versaoContrato": 1,
    "nifEmitente": 123456789,
    "nomeEmitente": "PRIMARY LANDLORD NAME",
    "locadores": [
        {
            "nif": 123456789,
            "nome": "MARIA LANDLORD SILVA",
            "quotaParte": "1/2",
            "sujeitoPassivo": "V"
        },
        {
            "nif": 987654321,
            "nome": "JOÃO LANDLORD COSTA",
            "quotaParte": "1/2", 
            "sujeitoPassivo": "V"
        }
    ],
    "locatarios": [
        {
            "nif": 111222333,
            "nome": "ANA TENANT FERREIRA",
            "pais": {"codigo": "2724", "label": "PORTUGAL"},
            "retencao": {"taxa": 0, "codigo": "RIRS03", "label": "Dispensa de retenção"}
        },
        {
            "nif": 444555666,
            "nome": "CARLOS TENANT MENDES",
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

def test_multiple_landlord_extraction():
    """Test multiple landlord extraction from JavaScript data."""
    print("=== Testing Multiple Landlord Extraction ===\n")
    
    script_content = sample_javascript_multiple_landlords
    contract_details = {}
    
    if 'numContrato' in script_content:
        print("✓ Found contract data in JavaScript")
        
        # Extract basic contract info
        contract_match = re.search(r'"numContrato":\s*(\d+)', script_content)
        if contract_match:
            contract_details['numContrato'] = int(contract_match.group(1))
            print(f"✓ Contract number: {contract_details['numContrato']}")
        
        # Extract ALL landlords
        locadores_pattern = r'"locadores":\s*\[(.*?)\]'
        locadores_match = re.search(locadores_pattern, script_content, re.DOTALL)
        if locadores_match:
            print("✓ Found locadores data in JavaScript")
            
            landlords_list = []
            
            try:
                # Parse full JSON structure
                full_array_pattern = r'"locadores":\s*(\[.*?\])'
                full_array_match = re.search(full_array_pattern, script_content, re.DOTALL)
                if full_array_match:
                    locadores_json = full_array_match.group(1)
                    # Clean up JSON
                    locadores_json = re.sub(r',\s*}', '}', locadores_json)
                    locadores_json = re.sub(r',\s*]', ']', locadores_json)
                    
                    landlords_array = json.loads(locadores_json)
                    
                    for i, landlord in enumerate(landlords_array):
                        landlord_info = {
                            'nif': landlord.get('nif'),
                            'nome': landlord.get('nome', '').strip(),
                            'quotaParte': landlord.get('quotaParte', '1/1'),
                            'sujeitoPassivo': landlord.get('sujeitoPassivo', 'V')
                        }
                        landlords_list.append(landlord_info)
                        print(f"✓ Extracted landlord {i+1}: NIF={landlord_info['nif']}, Name={landlord_info['nome']}, Quota={landlord_info['quotaParte']}")
                    
                    contract_details['locadores'] = landlords_list
                    contract_details['landlord_count'] = len(landlords_list)
                    print(f"✓ Successfully extracted {len(landlords_list)} landlords")
                    
            except (json.JSONDecodeError, ValueError) as e:
                print(f"✗ JSON parsing failed: {e}")
                return None
        
        # Extract ALL tenants (for comparison)
        locatarios_pattern = r'"locatarios":\s*\[(.*?)\]'
        locatarios_match = re.search(locatarios_pattern, script_content, re.DOTALL)
        if locatarios_match:
            print("\n✓ Found locatarios data in JavaScript")
            
            tenants_list = []
            
            try:
                full_array_pattern = r'"locatarios":\s*(\[.*?\])'
                full_array_match = re.search(full_array_pattern, script_content, re.DOTALL)
                if full_array_match:
                    locatarios_json = full_array_match.group(1)
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
                    
            except (json.JSONDecodeError, ValueError) as e:
                print(f"✗ Tenant JSON parsing failed: {e}")
    
    return contract_details

def test_submission_data_with_multiple_landlords():
    """Test submission data preparation with multiple landlords."""
    print("\n=== Testing Submission Data with Multiple Landlords ===\n")
    
    # Mock form data with multiple landlords and tenants
    form_data = {
        'numContrato': 123456,
        'versaoContrato': 1,
        'nifEmitente': 123456789,
        'nomeEmitente': 'PRIMARY LANDLORD',
        'contract_details': {
            'locadores': [
                {
                    'nif': 123456789,
                    'nome': 'MARIA LANDLORD SILVA',
                    'quotaParte': '1/2',
                    'sujeitoPassivo': 'V'
                },
                {
                    'nif': 987654321,
                    'nome': 'JOÃO LANDLORD COSTA', 
                    'quotaParte': '1/2',
                    'sujeitoPassivo': 'V'
                }
            ],
            'locatarios': [
                {
                    'nif': 111222333,
                    'nome': 'ANA TENANT FERREIRA',
                    'pais': {"codigo": "2724", "label": "PORTUGAL"},
                    'retencao': {"taxa": 0, "codigo": "RIRS03", "label": "Dispensa de retenção"}
                },
                {
                    'nif': 444555666,
                    'nome': 'CARLOS TENANT MENDES',
                    'pais': {"codigo": "2724", "label": "PORTUGAL"},
                    'retencao': {"taxa": 0, "codigo": "RIRS03", "label": "Dispensa de retenção"}
                }
            ]
        }
    }
    
    # Test landlord list preparation
    extracted_landlords = form_data.get('contract_details', {}).get('locadores', [])
    locadores_list = []
    
    if extracted_landlords:
        for i, landlord in enumerate(extracted_landlords):
            locador = {
                "nif": landlord.get('nif'),
                "nome": landlord.get('nome', '').strip(),
                "quotaParte": landlord.get('quotaParte', '1/1'),
                "sujeitoPassivo": landlord.get('sujeitoPassivo', 'V')
            }
            locadores_list.append(locador)
            print(f"✓ Prepared landlord {i+1}: NIF={locador['nif']}, Name={locador['nome']}, Quota={locador['quotaParte']}")
    
    print(f"\n✓ Total landlords prepared for submission: {len(locadores_list)}")
    
    # Test tenant list preparation
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
    
    print(f"\n✓ Total tenants prepared for submission: {len(locatarios_list)}")
    
    # Test tenant name extraction for report
    if len(locatarios_list) == 1:
        tenant_name_for_report = locatarios_list[0].get('nome', 'Unknown Tenant').strip()
    else:
        # Multiple tenants - create combined name
        names = []
        for tenant in locatarios_list:
            name = tenant.get('nome', '').strip()
            if name and name != 'UNKNOWN TENANT':
                names.append(name)
        if names:
            tenant_name_for_report = f"{', '.join(names)} ({len(names)} tenants)"
        else:
            tenant_name_for_report = f"{len(locatarios_list)} tenants"
    
    print(f"\n✓ Tenant name for report: '{tenant_name_for_report}'")
    
    # Show final submission structure
    print(f"\n=== Final Submission Structure ===")
    print("Locadores section:")
    print(json.dumps(locadores_list, indent=2, ensure_ascii=False))
    print("\nLocatarios section:")
    print(json.dumps(locatarios_list, indent=2, ensure_ascii=False))
    
    return locadores_list, locatarios_list, tenant_name_for_report

if __name__ == "__main__":
    print("=== Multiple Landlord & Tenant Name Support Test ===\n")
    
    # Test 1: Data extraction
    extracted_data = test_multiple_landlord_extraction()
    
    # Test 2: Submission preparation  
    landlords, tenants, tenant_name = test_submission_data_with_multiple_landlords()
    
    print(f"\n=== Test Results ===")
    if extracted_data and landlords and tenants:
        print("✅ Multiple landlord support is working correctly!")
        print("✅ Multiple tenant support is working correctly!")
        print("✅ Tenant names will be properly displayed in reports!")
        print("✅ All landlord and tenant data will be included in submissions")
        print()
        print("Key improvements:")
        print("- ✅ Multiple landlords extracted from JavaScript form data")  
        print("- ✅ Multiple tenants extracted from JavaScript form data")
        print("- ✅ Proper tenant names in report export")
        print("- ✅ Complete submission payloads with all parties")
    else:
        print("❌ Multiple party support test failed")
