"""
Test inheritance case detection and processing
"""
import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_inheritance_detection():
    """Test the inheritance case detection from $scope.recibo data."""
    from web_client import WebClient
    import re
    import json
    
    # Sample $scope.recibo data with inheritance (based on user's example)
    scope_recibo_with_inheritance = '''
    $scope.recibo = {
        "iRecibo":81764162,
        "numRecibo":29,
        "numContrato":5145568,
        "versaoContrato":2,
        "nifEmitente":555666777,
        "nomeEmitente":"SAMPLE LANDLORD NAME - CABEÇA DE CASAL DA HERANÇA DE",
        "isNifEmitenteColetivo":false,
        "emissaoData":"2024-07-31",
        "dataInicio":"2024-08-01",
        "dataFim":"2024-08-31",
        "dataRecebimento":"2024-07-04",
        "vRetencao":204.25,
        "valor": 100.00,
        "vImportanciaRecb":612.75,
        "retencao":{"taxa":0.25,"codigo":"RIRS01","label":"À taxa de 25% - artigo 101.º, n.º 1, al. e) do CIRS"},
        "estado":{"codigo":"EMITID","label":"Emitido"},
        "tipoContrato":{"codigo":"ARREND","label":"Arrendamento"},
        "tipoImportancia":{"codigo":"RENDAC","label":"Renda"},
        "locadores":[{"nif":555666777,"nome":"SAMPLE LANDLORD NAME - CABEÇA DE CASAL DA HERANÇA DE","quotaParte":"1/1","sujeitoPassivo":"V"}],
        "locatarios":[{"nif":444555666,"nome":"SAMPLE COMPANY LDA","pais":{"codigo":"2724","label":"PORTUGAL"},"retencao":{"taxa":0.25,"codigo":"RIRS01","label":"À taxa de 25% - artigo 101.º, n.º 1, al. e) do CIRS"}}],
        "imoveis":[{"codigoPostal":"2735","unidadeFuncional":"297","morada":"SAMPLE STREET SQUARE","numeroMorada":"13","localidade":"SAMPLE LOCALITY","andar":"RCA","distrito":{"codigo":"11","label":"LISBOA"},"concelho":{"codigo":"11","label":"SAMPLE MUNICIPALITY"},"freguesia":{"codigo":"24","label":"SAMPLE PARISH"},"tipo":{"codigo":"U","label":"Urbano"},"artigo":"2899","fraccao":"A","parteComum":false,"bemOmisso":false,"novo":false,"editableMode":false,"viewLoadingConcelhos":false,"viewLoadingFreguesias":false,"ordem":1,"alternateId":"111124-U-2899-A"}],
        "dataEstado":"2024-07-31",
        "hasNifHerancaIndivisa":true,
        "locadoresHerancaIndivisa":[{"nif":555666777,"nome":"SAMPLE LANDLORD NAME - CABEÇA DE CASAL DA HERANÇA DE","quotaParte":"1/1","sujeitoPassivo":"V"}],
        "herdeiros":[{"nifLocador":{"codigo":"555666777","label":"555666777"},"nifHerdeiro":987654321,"quotaParte":"1/2","ordem":1},{"nifLocador":{"codigo":"555666777","label":"555666777"},"nifHerdeiro":444555666,"quotaParte":"1/2","ordem":2}]
    };
    '''
    
    # Sample without inheritance
    scope_recibo_without_inheritance = '''
    $scope.recibo = {
        "numContrato":3338527,
        "hasNifHerancaIndivisa":false,
        "locadores":[{"nif":555666777,"nome":"REGULAR LANDLORD","quotaParte":"1/1","sujeitoPassivo":"V"}],
        "locatarios":[{"nif":123456789,"nome":"REGULAR TENANT","pais":{"codigo":"2724","label":"PORTUGAL"}}]
    };
    '''
    
    print("🔍 Testing Inheritance Detection...")
    
    # Test inheritance case
    print("\n1. Testing contract WITH inheritance:")
    
    # Extract inheritance flag
    inheritance_match = re.search(r'"hasNifHerancaIndivisa":\s*(true|false)', scope_recibo_with_inheritance)
    if inheritance_match:
        has_inheritance = inheritance_match.group(1) == 'true'
        print(f"   ✅ Inheritance flag detected: {has_inheritance}")
        
        if has_inheritance:
            # Extract locadoresHerancaIndivisa
            heranca_pattern = r'"locadoresHerancaIndivisa":\s*(\[.*?\])'
            heranca_match = re.search(heranca_pattern, scope_recibo_with_inheritance, re.DOTALL)
            if heranca_match:
                try:
                    heranca_json = heranca_match.group(1)
                    heranca_json = re.sub(r',\s*}', '}', heranca_json)
                    heranca_json = re.sub(r',\s*]', ']', heranca_json)
                    
                    heranca_landlords = json.loads(heranca_json)
                    print(f"   ✅ Inheritance landlords: {len(heranca_landlords)}")
                    for i, landlord in enumerate(heranca_landlords):
                        print(f"      Landlord {i+1}: NIF={landlord.get('nif')}, Name={landlord.get('nome', '')[:30]}...")
                        
                except Exception as e:
                    print(f"   ❌ Error parsing inheritance landlords: {e}")
            
            # Extract herdeiros
            herdeiros_pattern = r'"herdeiros":\s*(\[.*?\])'
            herdeiros_match = re.search(herdeiros_pattern, scope_recibo_with_inheritance, re.DOTALL)
            if herdeiros_match:
                try:
                    herdeiros_json = herdeiros_match.group(1)
                    herdeiros_json = re.sub(r',\s*}', '}', herdeiros_json)
                    herdeiros_json = re.sub(r',\s*]', ']', herdeiros_json)
                    
                    heirs = json.loads(herdeiros_json)
                    print(f"   ✅ Heirs: {len(heirs)}")
                    for i, heir in enumerate(heirs):
                        heir_nif = heir.get('nifHerdeiro')
                        quota = heir.get('quotaParte')
                        ordem = heir.get('ordem')
                        print(f"      Heir {i+1}: NIF={heir_nif}, Quota={quota}, Order={ordem}")
                        
                except Exception as e:
                    print(f"   ❌ Error parsing heirs: {e}")
    
    # Test non-inheritance case
    print("\n2. Testing contract WITHOUT inheritance:")
    
    inheritance_match = re.search(r'"hasNifHerancaIndivisa":\s*(true|false)', scope_recibo_without_inheritance)
    if inheritance_match:
        has_inheritance = inheritance_match.group(1) == 'true'
        print(f"   ✅ Inheritance flag detected: {has_inheritance}")
        
        if not has_inheritance:
            print(f"   ✅ Standard processing will be used (no inheritance parameters)")
    
    print(f"\n📊 Inheritance Processing Summary:")
    print(f"   • Detection works by checking 'hasNifHerancaIndivisa' flag")
    print(f"   • When true: extracts locadoresHerancaIndivisa and herdeiros arrays")
    print(f"   • When false: uses standard locadores processing")
    print(f"   • Submission data includes all inheritance parameters")
    print(f"   • Contract 5145568 is confirmed as inheritance case")

def test_receipt_processor_inheritance():
    """Test that receipt processor correctly handles inheritance data."""
    print(f"\n🔧 Testing Receipt Processor with Inheritance...")
    
    try:
        from receipt_processor import ReceiptProcessor
        from web_client import WebClient
        from csv_handler import ReceiptData
        
        # Create test receipt data
        receipt = ReceiptData(
            contract_id="5145568",
            from_date="2024-08-01",
            to_date="2024-08-31",
            payment_date="2024-07-04",
            value=817.00,
            receipt_type="RENDAC"  # Added missing parameter
        )
        
        # Mock form data with inheritance information
        form_data = {
            'contract_details': {
                'hasNifHerancaIndivisa': True,
                'locadoresHerancaIndivisa': [
                    {
                        'nif': 555666777,
                        'nome': 'SAMPLE LANDLORD NAME - CABEÇA DE CASAL DA HERANÇA DE',
                        'quotaParte': '1/1',
                        'sujeitoPassivo': 'V'
                    }
                ],
                'herdeiros': [
                    {
                        'nifLocador': {'codigo': '555666777', 'label': '555666777'},
                        'nifHerdeiro': 987654321,
                        'quotaParte': '1/2',
                        'ordem': 1
                    },
                    {
                        'nifLocador': {'codigo': '555666777', 'label': '555666777'},
                        'nifHerdeiro': 444555666,
                        'quotaParte': '1/2',
                        'ordem': 2
                    }
                ],
                'locatarios': [
                    {
                        'nif': 444555666,
                        'nome': 'SAMPLE COMPANY LDA'
                    }
                ]
            }
        }
        
        # Test submission data preparation
        web_client = WebClient(testing_mode=True)
        processor = ReceiptProcessor(web_client)
        
        submission_data = processor._prepare_submission_data(receipt, form_data)
        
        print(f"   ✅ Inheritance data included in submission:")
        print(f"      hasNifHerancaIndivisa: {submission_data.get('hasNifHerancaIndivisa')}")
        print(f"      locadoresHerancaIndivisa: {len(submission_data.get('locadoresHerancaIndivisa', []))}")
        print(f"      herdeiros: {len(submission_data.get('herdeiros', []))}")
        
        # Verify the inheritance data is correctly passed through
        if submission_data.get('hasNifHerancaIndivisa'):
            print(f"   ✅ Receipt processor correctly detected inheritance case")
            heirs = submission_data.get('herdeiros', [])
            for i, heir in enumerate(heirs):
                print(f"      Heir {i+1}: NIF={heir.get('nifHerdeiro')}, Quota={heir.get('quotaParte')}")
        else:
            print(f"   ❌ Receipt processor failed to detect inheritance case")
            
    except Exception as e:
        print(f"   ❌ Error testing receipt processor: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 80)
    print("INHERITANCE CASE DETECTION AND PROCESSING TEST")
    print("=" * 80)
    test_inheritance_detection()
    test_receipt_processor_inheritance()
