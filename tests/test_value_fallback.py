#!/usr/bin/env python3
"""
Test CSV value fallback functionality.
"""

import sys
import os
import tempfile
from unittest.mock import Mock, patch
from datetime import datetime

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from csv_handler import CSVHandler
from web_client import WebClient
from receipt_processor import ReceiptProcessor
from utils.logger import get_logger

logger = get_logger(__name__)

def test_value_fallback():
    """Test that value fallback works when CSV value column is missing or empty."""
    print("=" * 70)
    print("CSV VALUE FALLBACK TEST")
    print("=" * 70)
    
    test_cases = [
        {
            "name": "CSV with explicit values",
            "csv_content": """contractId,fromDate,toDate,receiptType,value,paymentDate
123456,2024-07-01,2024-07-31,rent,100.00,2024-07-28""",
            "should_pass": True,
            "expected_value": 100.00,
            "fallback_expected": False
        },
        {
            "name": "CSV without value column (fallback)",
            "csv_content": """contractId,fromDate,toDate,receiptType,paymentDate
123456,2024-07-01,2024-07-31,rent,2024-07-28""",
            "should_pass": True,
            "expected_value": 100.00,  # From contract data
            "fallback_expected": True
        },
        {
            "name": "CSV with empty value (fallback)",
            "csv_content": """contractId,fromDate,toDate,receiptType,value,paymentDate
123456,2024-07-01,2024-07-31,rent,,2024-07-28""",
            "should_pass": True,
            "expected_value": 100.00,  # From contract data
            "fallback_expected": True
        },
        {
            "name": "CSV with zero value (fallback)",
            "csv_content": """contractId,fromDate,toDate,receiptType,value,paymentDate
123456,2024-07-01,2024-07-31,rent,0,2024-07-28""",
            "should_pass": True,
            "expected_value": 100.00,  # From contract data
            "fallback_expected": True
        }
    ]
    
    csv_handler = CSVHandler()
    
    for i, test_case in enumerate(test_cases):
        print(f"\n{i+1}. Testing: {test_case['name']}")
        
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as temp_file:
            temp_file.write(test_case['csv_content'])
            temp_file_path = temp_file.name
        
        try:
            # Test CSV loading
            success, errors = csv_handler.load_csv(temp_file_path)
            
            if test_case['should_pass']:
                if success:
                    receipts = csv_handler.get_receipts()
                    print(f"   ✅ CSV loaded successfully: {len(receipts)} receipts")
                    
                    receipt = receipts[0]
                    print(f"      - CSV value: {receipt.value}")
                    
                    # Test with mock web client and processor
                    with patch('requests.Session') as mock_session_class:
                        mock_session = Mock()
                        mock_session_class.return_value = mock_session
                        
                        # Mock form HTML
                        form_html = """
                        <html><body>
                            <script>
                                var $scope = {};
                                $scope.recibo = {
                                    "numContrato": 123456,
                                    "versaoContrato": 1,
                                    "nifEmitente": 123456789,
                                    "nomeEmitente": "TEST LANDLORD NAME"
                                };
                            </script>
                        </body></html>
                        """
                        
                        captured_payload = None
                        
                        def mock_get(url, **kwargs):
                            response = Mock()
                            response.status_code = 200
                            response.text = form_html
                            return response
                        
                        def mock_post(url, **kwargs):
                            nonlocal captured_payload
                            response = Mock()
                            if 'emitirRecibo' in url:
                                captured_payload = kwargs.get('json', {})
                                response.status_code = 200
                                response.json.return_value = {
                                    "success": True,
                                    "numeroRecibo": "REC123456202407281800",
                                    "valor": captured_payload.get("valor")
                                }
                            else:
                                response.status_code = 200
                                response.text = '<html><body>Mock response</body></html>'
                            return response
                        
                        mock_session.get = mock_get
                        mock_session.post = mock_post
                        mock_session.cookies = Mock()
                        mock_session.cookies.keys.return_value = ['JSESSIONID']
                        
                        # Set up web client
                        web_client = WebClient()
                        web_client.session = mock_session
                        web_client.authenticated = True
                        
                        # Mock contracts cache with contract value
                        web_client._contracts_cache = {
                            'contracts': [
                                {
                                    "numero": "123456",
                                    "referencia": "CT123456",
                                    "nomeLocador": "TEST LANDLORD NAME",
                                    "nomeLocatario": "Test Tenant Name",
                                    "imovelAlternateId": "Narnia, 123",
                                    "valorRenda": 100.00,  # Contract fallback value
                                    "estado": {"codigo": "ACTIVO", "label": "Ativo"}
                                }
                            ],
                            'timestamp': datetime.now().timestamp()
                        }
                        
                        processor = ReceiptProcessor(web_client)
                        
                        # Get form data and prepare submission
                        success, form_data = web_client.get_receipt_form(receipt.contract_id)
                        if success:
                            submission_data = processor._prepare_submission_data(receipt, form_data)
                            
                            # Issue receipt to capture payload
                            success, response = web_client.issue_receipt(submission_data)
                            
                            if success and captured_payload:
                                actual_value = captured_payload.get('valor')
                                expected_value = test_case['expected_value']
                                
                                if abs(actual_value - expected_value) < 0.01:  # Float comparison
                                    print(f"      ✅ Value correctly set: €{actual_value}")
                                    if test_case['fallback_expected']:
                                        print(f"         (Used fallback from contract)")
                                else:
                                    print(f"      ❌ Value mismatch:")
                                    print(f"         Expected: €{expected_value}")
                                    print(f"         Actual: €{actual_value}")
                            else:
                                print(f"      ❌ Failed to process receipt")
                        else:
                            print(f"      ❌ Failed to get form data")
                
                else:
                    print(f"   ❌ CSV loading failed:")
                    for error in errors:
                        print(f"      • {error}")
            else:
                if not success:
                    print(f"   ✅ Correctly rejected")
                else:
                    print(f"   ❌ Should have been rejected")
        
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_file_path)
            except:
                pass
    
    # Test required/optional columns
    print(f"\n" + "=" * 70)
    print("COLUMN CONFIGURATION")
    print("=" * 70)
    
    print(f"Required columns: {csv_handler.REQUIRED_COLUMNS}")
    print(f"Optional columns: {csv_handler.OPTIONAL_COLUMNS}")
    
    if 'value' in csv_handler.OPTIONAL_COLUMNS:
        print("✅ value is correctly marked as OPTIONAL")
    else:
        print("❌ value should be marked as OPTIONAL")
    
    if 'paymentDate' in csv_handler.REQUIRED_COLUMNS:
        print("✅ paymentDate is correctly marked as REQUIRED")
    else:
        print("❌ paymentDate should be marked as REQUIRED")
    
    print(f"\n" + "=" * 70)
    print("CSV VALUE FALLBACK TEST COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    test_value_fallback()
