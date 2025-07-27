#!/usr/bin/env python3
"""
Payload Validation Test for Receipt Issuing
Tests that the correct JSON payload structure is sent to the platform API.
Uses mock platform to capture and validate the exact payload sent.
"""

import sys
import os
import json
from unittest.mock import Mock, patch
from datetime import datetime

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.web_client import WebClient
from src.receipt_processor import ReceiptProcessor
from src.csv_handler import ReceiptData
from src.utils.logger import get_logger

logger = get_logger(__name__)

class PayloadCaptureMockPlatform:
    """Mock platform that captures and validates payloads."""
    
    def __init__(self):
        self.captured_payloads = []
        self.validation_results = []
        
        # Expected payload structure based on Portal das Finanças API
        self.expected_structure = {
            "numContrato": int,
            "versaoContrato": int,
            "nifEmitente": (int, type(None)),
            "nomeEmitente": str,
            "isNifEmitenteColetivo": bool,
            "valor": (int, float),
            "tipoContrato": {
                "codigo": str,
                "label": str
            },
            "locadores": list,
            "locatarios": list,
            "imoveis": list,
            "hasNifHerancaIndivisa": bool,
            "locadoresHerancaIndivisa": list,
            "herdeiros": list,
            "dataInicio": str,
            "dataFim": str,
            "dataRecebimento": str,
            "tipoImportancia": {
                "codigo": str,
                "label": str
            }
        }
        
        # Mock contracts for testing
        self.contracts = {
            "123456": {
                "numContrato": 123456,
                "versaoContrato": 1,
                "nifEmitente": 123456789,
                "nomeEmitente": "TEST LANDLORD NAME",
                "valorRenda": 100.00,
                "nomeLocatario": "Test Tenant Name",
                "imovelAlternateId": "Narnia, 123, 1º Dto",
            }
        }
    
    def validate_payload_structure(self, payload: dict, path: str = "") -> list:
        """Recursively validate payload structure against expected format."""
        errors = []
        
        def validate_field(actual, expected, field_path):
            if isinstance(expected, dict):
                if not isinstance(actual, dict):
                    errors.append(f"{field_path}: Expected dict, got {type(actual)}")
                    return
                for key, expected_type in expected.items():
                    if key not in actual:
                        errors.append(f"{field_path}.{key}: Missing required field")
                    else:
                        validate_field(actual[key], expected_type, f"{field_path}.{key}")
            elif isinstance(expected, tuple):
                # Multiple allowed types
                if not any(isinstance(actual, t) for t in expected):
                    type_names = [t.__name__ for t in expected]
                    errors.append(f"{field_path}: Expected one of {type_names}, got {type(actual)}")
            elif isinstance(expected, type):
                if not isinstance(actual, expected):
                    errors.append(f"{field_path}: Expected {expected.__name__}, got {type(actual)}")
            elif expected == list:
                if not isinstance(actual, list):
                    errors.append(f"{field_path}: Expected list, got {type(actual)}")
        
        validate_field(payload, self.expected_structure, "payload")
        return errors
    
    def validate_payload_content(self, payload: dict) -> list:
        """Validate payload content and business logic."""
        errors = []
        
        # Check required fields have valid values
        if payload.get("numContrato") and payload.get("numContrato") <= 0:
            errors.append("numContrato must be positive")
        
        if payload.get("valor") and payload.get("valor") <= 0:
            errors.append("valor must be positive")
        
        # Check date format (YYYY-MM-DD)
        date_fields = ["dataInicio", "dataFim", "dataRecebimento"]
        for field in date_fields:
            if field in payload:
                try:
                    datetime.strptime(payload[field], "%Y-%m-%d")
                except ValueError:
                    errors.append(f"{field} must be in YYYY-MM-DD format")
        
        # Check date logic
        if "dataInicio" in payload and "dataFim" in payload:
            try:
                start = datetime.strptime(payload["dataInicio"], "%Y-%m-%d")
                end = datetime.strptime(payload["dataFim"], "%Y-%m-%d")
                if start > end:
                    errors.append("dataInicio must be before or equal to dataFim")
            except ValueError:
                pass  # Already caught above
        
        # Check required list structures
        if "locadores" in payload and payload["locadores"]:
            for i, locador in enumerate(payload["locadores"]):
                if not isinstance(locador, dict):
                    errors.append(f"locadores[{i}] must be an object")
                elif "nome" not in locador:
                    errors.append(f"locadores[{i}] missing required 'nome' field")
        
        if "locatarios" in payload and payload["locatarios"]:
            for i, locatario in enumerate(payload["locatarios"]):
                if not isinstance(locatario, dict):
                    errors.append(f"locatarios[{i}] must be an object")
                elif "nome" not in locatario:
                    errors.append(f"locatarios[{i}] missing required 'nome' field")
        
        # Check tipoContrato
        if "tipoContrato" in payload:
            tipo = payload["tipoContrato"]
            if isinstance(tipo, dict):
                if tipo.get("codigo") != "ARREND":
                    errors.append("tipoContrato.codigo should be 'ARREND' for rent receipts")
            
        return errors
    
    def capture_and_validate_payload(self, payload: dict) -> dict:
        """Capture payload and perform validation."""
        self.captured_payloads.append(payload.copy())
        
        # Structure validation
        structure_errors = self.validate_payload_structure(payload)
        
        # Content validation
        content_errors = self.validate_payload_content(payload)
        
        validation_result = {
            "payload": payload,
            "structure_valid": len(structure_errors) == 0,
            "content_valid": len(content_errors) == 0,
            "structure_errors": structure_errors,
            "content_errors": content_errors,
            "timestamp": datetime.now().isoformat()
        }
        
        self.validation_results.append(validation_result)
        
        # Return mock success response
        if validation_result["structure_valid"] and validation_result["content_valid"]:
            return {
                "success": True,
                "numeroRecibo": f"REC{payload.get('numContrato', '000000')}{datetime.now().strftime('%Y%m%d%H%M')}",
                "dataEmissao": datetime.now().isoformat(),
                "valor": payload.get("valor")
            }
        else:
            return {
                "success": False,
                "error": "Validation failed",
                "structure_errors": structure_errors,
                "content_errors": content_errors
            }
    
    def get_receipt_form_html(self, contract_id: str) -> str:
        """Mock receipt form HTML."""
        if contract_id not in self.contracts:
            return None
            
        contract = self.contracts[contract_id]
        
        return f"""
        <html>
        <body>
            <script>
                var $scope = {{}};
                $scope.recibo = {{
                    "numContrato": {contract["numContrato"]},
                    "versaoContrato": {contract["versaoContrato"]},
                    "nifEmitente": {contract["nifEmitente"]},
                    "nomeEmitente": "{contract["nomeEmitente"]}",
                    "valorRenda": {contract["valorRenda"]}
                }};
            </script>
        </body>
        </html>
        """
    
    def get_contracts_list(self) -> list:
        """Mock contracts list."""
        return [
            {
                "numero": str(contract["numContrato"]),
                "referencia": f"CT{contract['numContrato']}",
                "nomeLocador": contract["nomeEmitente"],
                "nomeLocatario": contract["nomeLocatario"],
                "imovelAlternateId": contract["imovelAlternateId"],
                "valorRenda": contract["valorRenda"],
                "estado": {"codigo": "ACTIVO", "label": "Ativo"}
            }
            for contract in self.contracts.values()
        ]

def test_payload_validation():
    """Test that correct payload structure is sent to the platform."""
    print("=" * 80)
    print("PAYLOAD VALIDATION TEST")
    print("=" * 80)
    
    # Initialize mock platform
    mock_platform = PayloadCaptureMockPlatform()
    
    # Test receipt data
    test_receipt = ReceiptData(
        contract_id="123456",
        from_date="2024-07-01",
        to_date="2024-07-31",
        receipt_type="rent",
        value=100.00
    )
    
    print(f"Testing receipt: Contract {test_receipt.contract_id}, Value €{test_receipt.value}")
    
    with patch('requests.Session') as mock_session_class:
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        # Mock GET requests (form retrieval)
        def mock_get(url, **kwargs):
            response = Mock()
            response.status_code = 200
            
            if 'criarRecibo' in url:
                contract_id = url.split('/')[-1]
                response.text = mock_platform.get_receipt_form_html(contract_id)
            elif 'obterElementosContratosEmissaoRecibos' in url:
                response.json.return_value = {"data": mock_platform.get_contracts_list()}
            else:
                response.text = '<html><body>Mock response</body></html>'
            
            return response
        
        # Mock POST requests (receipt submission) - THIS IS WHERE WE CAPTURE THE PAYLOAD
        def mock_post(url, **kwargs):
            response = Mock()
            
            if 'emitirRecibo' in url:
                # CAPTURE AND VALIDATE THE PAYLOAD
                payload = kwargs.get('json', {})
                print(f"\n📨 CAPTURED PAYLOAD:")
                print(json.dumps(payload, indent=2, ensure_ascii=False))
                
                # Validate the payload
                result = mock_platform.capture_and_validate_payload(payload)
                
                response.status_code = 200 if result.get('success') else 400
                response.json.return_value = result
            else:
                response.status_code = 200
                response.text = '<html><body>Mock response</body></html>'
            
            return response
        
        mock_session.get = mock_get
        mock_session.post = mock_post
        mock_session.cookies = Mock()
        mock_session.cookies.keys.return_value = ['JSESSIONID']
        
        # Create and configure web client
        web_client = WebClient(testing_mode=False)
        web_client.session = mock_session
        web_client.authenticated = True
        
        # Set up contracts cache
        web_client._contracts_cache = {
            'contracts': mock_platform.get_contracts_list(),
            'timestamp': datetime.now().timestamp()
        }
        
        print("\n🔍 TESTING WORKFLOW:")
        
        # Step 1: Get receipt form
        print("\n1. Getting receipt form...")
        success, form_data = web_client.get_receipt_form(test_receipt.contract_id)
        
        if not success:
            print("❌ Failed to get receipt form")
            return
        
        print(f"✅ Form data retrieved with contract details")
        
        # Step 2: Prepare submission data
        print("\n2. Preparing submission data...")
        processor = ReceiptProcessor(web_client)
        submission_data = processor._prepare_submission_data(test_receipt, form_data)
        
        print(f"✅ Submission data prepared")
        
        # Step 3: Issue receipt (this triggers payload capture)
        print("\n3. Issuing receipt (payload will be captured)...")
        success, response = web_client.issue_receipt(submission_data)
        
        # Step 4: Analyze validation results
        print("\n" + "=" * 80)
        print("PAYLOAD VALIDATION RESULTS")
        print("=" * 80)
        
        if mock_platform.validation_results:
            result = mock_platform.validation_results[0]
            
            print(f"\n📊 STRUCTURE VALIDATION:")
            if result["structure_valid"]:
                print("✅ Payload structure is CORRECT")
            else:
                print("❌ Payload structure has ERRORS:")
                for error in result["structure_errors"]:
                    print(f"   • {error}")
            
            print(f"\n📋 CONTENT VALIDATION:")
            if result["content_valid"]:
                print("✅ Payload content is VALID")
            else:
                print("❌ Payload content has ERRORS:")
                for error in result["content_errors"]:
                    print(f"   • {error}")
            
            print(f"\n📈 PAYLOAD SUMMARY:")
            payload = result["payload"]
            print(f"   • Contract ID: {payload.get('numContrato')}")
            print(f"   • Value: €{payload.get('valor')}")
            print(f"   • Period: {payload.get('dataInicio')} to {payload.get('dataFim')}")
            print(f"   • Landlord: {payload.get('nomeEmitente')}")
            print(f"   • Landlords count: {len(payload.get('locadores', []))}")
            print(f"   • Tenants count: {len(payload.get('locatarios', []))}")
            print(f"   • Properties count: {len(payload.get('imoveis', []))}")
            
            if success:
                print(f"\n🎉 RECEIPT ISSUED SUCCESSFULLY:")
                print(f"   • Receipt Number: {response.get('receiptNumber')}")
            else:
                print(f"\n❌ RECEIPT ISSUANCE FAILED:")
                print(f"   • Error: {response}")
        
        else:
            print("❌ No payload was captured!")
    
    print("\n" + "=" * 80)
    print("PAYLOAD VALIDATION TEST COMPLETE")
    
    if mock_platform.validation_results:
        result = mock_platform.validation_results[0]
        if result["structure_valid"] and result["content_valid"]:
            print("🎉 ALL VALIDATIONS PASSED - Payload is correct!")
        else:
            print("⚠️  VALIDATION ISSUES FOUND - Review errors above")
    else:
        print("❌ No validation performed - Check test setup")
    
    print("=" * 80)

if __name__ == "__main__":
    test_payload_validation()
