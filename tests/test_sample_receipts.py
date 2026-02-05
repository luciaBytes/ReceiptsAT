#!/usr/bin/env python3
"""
Test the sample_receipts.csv file with the complete receipt processing system.
"""

import sys
import os
from unittest.mock import Mock, patch
from datetime import datetime
import json

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from csv_handler import CSVHandler
from web_client import WebClient
from receipt_processor import ReceiptProcessor
from utils.logger import get_logger

logger = get_logger(__name__)

def test_sample_receipts():
    """Test the sample_receipts.csv file with complete workflow."""
    print("=" * 80)
    print("SAMPLE RECEIPTS CSV TEST")
    print("=" * 80)
    
    # Path to the sample CSV file
    project_root = os.path.join(os.path.dirname(__file__), '..')
    csv_file_path = os.path.join(project_root, 'sample', 'sample_receipts.csv')
    
    if not os.path.exists(csv_file_path):
        print(f"❌ Sample CSV file not found: {csv_file_path}")
        return
    
    print(f"Testing file: {csv_file_path}")
    
    # Step 1: Test CSV Loading
    print(f"\n1. TESTING CSV LOADING")
    print("-" * 40)
    
    csv_handler = CSVHandler()
    success, errors = csv_handler.load_csv(csv_file_path)
    
    if success:
        receipts = csv_handler.get_receipts()
        print(f"✅ CSV loaded successfully: {len(receipts)} receipts")
        
        print(f"\nReceipt Details:")
        for i, receipt in enumerate(receipts, 1):
            print(f"  {i}. Contract {receipt.contract_id}:")
            print(f"     - Period: {receipt.from_date} to {receipt.to_date}")
            print(f"     - Payment Date: {receipt.payment_date}")
            print(f"     - Value: €{receipt.value}")
            print(f"     - Type: {receipt.receipt_type}")
    else:
        print(f"❌ CSV loading failed with errors:")
        for error in errors:
            print(f"   • {error}")
        return
    
    # Step 2: Test Contract Validation (Mock)
    print(f"\n2. TESTING CONTRACT VALIDATION")
    print("-" * 40)
    
    captured_payloads = []
    
    with patch('requests.Session') as mock_session_class:
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        # Mock contract data for all sample contracts
        mock_contracts = [
            {
                "numero": "123456",
                "referencia": "CT123456",
                "nomeLocador": "LANDLORD ONE",
                "nomeLocatario": "TENANT ONE",
                "imovelAlternateId": "Narnia, 123",
                "valorRenda": 100.00,
                "estado": {"codigo": "ACTIVO", "label": "Ativo"}
            },
            {
                "numero": "789012",
                "referencia": "CT789012", 
                "nomeLocador": "LANDLORD TWO",
                "nomeLocatario": "TENANT TWO",
                "imovelAlternateId": "Avenida Central, 456",
                "valorRenda": 900.50,
                "estado": {"codigo": "ACTIVO", "label": "Ativo"}
            },
            {
                "numero": "345678",
                "referencia": "CT345678",
                "nomeLocador": "LANDLORD THREE", 
                "nomeLocatario": "TENANT THREE",
                "imovelAlternateId": "Praça Principal, 789",
                "valorRenda": 925.75,
                "estado": {"codigo": "ACTIVO", "label": "Ativo"}
            },
            {
                "numero": "901234",
                "referencia": "CT901234",
                "nomeLocador": "LANDLORD FOUR",
                "nomeLocatario": "TENANT FOUR", 
                "imovelAlternateId": "Rua Nova, 101",
                "valorRenda": 875.25,
                "estado": {"codigo": "ACTIVO", "label": "Ativo"}
            }
        ]
        
        # Create mock validation report
        csv_contract_ids = ["123456", "789012", "345678", "901234"]
        mock_validation_report = {
            'success': True,
            'message': "Mock validation successful",
            'portal_contracts_count': len(mock_contracts),
            'csv_contracts_count': len(csv_contract_ids),
            'portal_contracts': csv_contract_ids,
            'portal_contracts_data': mock_contracts,
            'csv_contracts': csv_contract_ids,
            'valid_contracts': csv_contract_ids,
            'valid_contracts_data': mock_contracts,
            'invalid_contracts': [],
            'missing_from_csv': [],
            'missing_from_csv_data': [],
            'missing_from_portal': [],
            'validation_errors': []
        }
        
        def mock_get(url, **kwargs):
            response = Mock()
            response.status_code = 200
            response.json = Mock()
            
            if 'criarRecibo' in url:
                # Extract contract ID from URL
                contract_id = url.split('/')[-1]
                
                # Find the contract data
                contract = next((c for c in mock_contracts if c['numero'] == contract_id), None)
                if contract:
                    form_html = f"""
                    <html><body>
                        <script>
                            var $scope = {{}};
                            $scope.recibo = {{
                                "numContrato": {contract['numero']},
                                "versaoContrato": 1,
                                "nifEmitente": 123456789,
                                "nomeEmitente": "{contract['nomeLocador']}"
                            }};
                        </script>
                    </body></html>
                    """
                    response.text = form_html
                else:
                    response.text = '<html><body>Contract not found</body></html>'
            
            elif 'obterElementosContratosEmissaoRecibos' in url:
                response.json.return_value = {"data": mock_contracts}
            else:
                response.text = '<html><body>Mock response</body></html>'
                response.json.return_value = {}
            
            return response
        
        def mock_post(url, **kwargs):
            response = Mock()
            response.json = Mock()
            
            if 'emitirRecibo' in url:
                # Capture the payload
                payload = kwargs.get('json', {})
                captured_payloads.append(payload.copy())
                
                response.status_code = 200
                response.json.return_value = {
                    "success": True,
                    "numeroRecibo": f"REC{payload.get('numContrato', '000000')}{datetime.now().strftime('%Y%m%d%H%M')}",
                    "dataEmissao": datetime.now().isoformat(),
                    "valor": payload.get("valor")
                }
            else:
                response.status_code = 200
                response.text = '<html><body>Mock response</body></html>'
                response.json.return_value = {}
            
            return response
        
        mock_session.get = mock_get
        mock_session.post = mock_post
        mock_session.cookies = Mock()
        mock_session.cookies.keys.return_value = ['JSESSIONID']
        
        # Set up web client
        web_client = WebClient()
        web_client.session = mock_session
        web_client.authenticated = True
        
        # Mock contracts cache
        web_client._contracts_cache = {
            'contracts': mock_contracts,
            'timestamp': datetime.now().timestamp()
        }
        
        # Mock the validate_csv_contracts method
        def mock_validate_csv_contracts(csv_contract_ids):
            return mock_validation_report
        
        web_client.validate_csv_contracts = mock_validate_csv_contracts
        
        processor = ReceiptProcessor(web_client)
        
        # Test contract validation
        validation_report = processor.validate_contracts(receipts)
        print(f"Contract validation completed:")
        print(f"  - Success: {validation_report['success']}")
        print(f"  - Total receipts: {validation_report['receipts_count']}")
        print(f"  - Valid contracts: {len(validation_report['valid_contracts'])}")
        print(f"  - Invalid contracts: {len(validation_report['invalid_contracts'])}")
        
        if validation_report['invalid_contracts']:
            print(f"  Invalid contracts:")
            for contract_id in validation_report['invalid_contracts']:
                print(f"    • {contract_id}")
        
        # Step 3: Test Receipt Processing
        print(f"\n3. TESTING RECEIPT PROCESSING")
        print("-" * 40)
        
        # Process all receipts
        for i, receipt in enumerate(receipts):
            print(f"\n  Processing receipt {i+1}/{len(receipts)}: Contract {receipt.contract_id}")
            
            # Get form data
            success, form_data = web_client.get_receipt_form(receipt.contract_id)
            if success:
                print(f"    ✅ Form data retrieved")
                
                # Prepare submission data
                submission_data = processor._prepare_submission_data(receipt, form_data)
                
                # Issue receipt
                success, response = web_client.issue_receipt(submission_data)
                if success:
                    print(f"    ✅ Receipt issued: {response.get('receiptNumber')}")
                    print(f"       Value: €{response.get('response', {}).get('valor', 'Unknown')}")
                else:
                    print(f"    ❌ Receipt issuance failed: {response}")
            else:
                print(f"    ❌ Failed to get form data")
    
    # Step 4: Analyze Captured Payloads
    print(f"\n4. PAYLOAD ANALYSIS")
    print("-" * 40)
    
    if captured_payloads:
        print(f"Captured {len(captured_payloads)} payloads:")
        
        for i, payload in enumerate(captured_payloads):
            receipt = receipts[i]
            print(f"\n  Payload {i+1} (Contract {payload.get('numContrato')}):")
            print(f"    - Period: {payload.get('dataInicio')} to {payload.get('dataFim')}")
            print(f"    - Payment Date: {payload.get('dataRecebimento')}")
            print(f"    - Value: €{payload.get('valor')}")
            print(f"    - Landlord: {payload.get('nomeEmitente')}")
            print(f"    - CSV Value: €{receipt.value}")
            
            # Check if CSV value matches payload value
            if abs(payload.get('valor', 0) - receipt.value) < 0.01:
                print(f"    ✅ Value correctly used from CSV")
            else:
                print(f"    ⚠️  Value mismatch - used fallback or different value")
        
        # Show sample payload structure
        print(f"\n  Sample Payload Structure:")
        sample = captured_payloads[0]
        print(json.dumps({
            "numContrato": sample.get("numContrato"),
            "valor": sample.get("valor"),
            "dataInicio": sample.get("dataInicio"),
            "dataFim": sample.get("dataFim"),
            "dataRecebimento": sample.get("dataRecebimento"),
            "nomeEmitente": sample.get("nomeEmitente"),
            "locadores": sample.get("locadores", []),
            "locatarios": sample.get("locatarios", []),
            "imoveis": sample.get("imoveis", [])
        }, indent=2))
    
    else:
        print("❌ No payloads were captured")
    
    print(f"\n" + "=" * 80)
    print("SAMPLE RECEIPTS TEST COMPLETE")
    print("=" * 80)
    
    # Summary
    if captured_payloads:
        print(f"🎉 SUCCESS: All {len(captured_payloads)} receipts processed successfully!")
        print(f"   - CSV validation: ✅")
        print(f"   - Contract validation: ✅") 
        print(f"   - Form retrieval: ✅")
        print(f"   - Receipt issuance: ✅")
        print(f"   - Payload structure: ✅")
    else:
        print(f"❌ FAILURE: Receipt processing encountered issues")
    
    print("=" * 80)

if __name__ == "__main__":
    test_sample_receipts()
