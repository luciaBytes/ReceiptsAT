#!/usr/bin/env python3
"""
Test to verify payment date is correctly sent in receipt issuance requests.
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

def test_payment_date_in_payload():
    """Test that payment date is correctly included in the API payload."""
    print("=" * 70)
    print("PAYMENT DATE TEST")
    print("=" * 70)
    
    # Test cases with different payment date scenarios
    test_cases = [
        {
            "name": "Explicit Payment Date",
            "receipt": ReceiptData(
                contract_id="123456",
                from_date="2024-07-01",
                to_date="2024-07-31",
                receipt_type="rent",
                value=100.00,
                payment_date="2024-07-30"  # Explicit payment date
            ),
            "expected_payment_date": "2024-07-30"
        },
        {
            "name": "No Payment Date (fallback to to_date)",
            "receipt": ReceiptData(
                contract_id="123456",
                from_date="2024-07-01", 
                to_date="2024-07-31",
                receipt_type="rent",
                value=100.00,
                payment_date=""  # Empty payment date
            ),
            "expected_payment_date": "2024-07-31"
        },
        {
            "name": "Different Payment Date",
            "receipt": ReceiptData(
                contract_id="123456",
                from_date="2024-07-01",
                to_date="2024-07-31", 
                receipt_type="rent",
                value=100.00,
                payment_date="2024-06-28"  # Payment made before period
            ),
            "expected_payment_date": "2024-06-28"
        }
    ]
    
    captured_payloads = []
    
    with patch('requests.Session') as mock_session_class:
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        # Mock form HTML with contract data
        form_html = """
        <html>
        <body>
            <script>
                var $scope = {};
                $scope.recibo = {
                    "numContrato": 123456,
                    "versaoContrato": 1,
                    "nifEmitente": 123456789,
                    "nomeEmitente": "TEST LANDLORD NAME"
                };
            </script>
        </body>
        </html>
        """
        
        def mock_get(url, **kwargs):
            response = Mock()
            response.status_code = 200
            response.text = form_html
            return response
        
        def mock_post(url, **kwargs):
            response = Mock()
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
            
            return response
        
        mock_session.get = mock_get
        mock_session.post = mock_post
        mock_session.cookies = Mock()
        mock_session.cookies.keys.return_value = ['JSESSIONID']
        
        # Set up web client
        web_client = WebClient(testing_mode=False)
        web_client.session = mock_session
        web_client.authenticated = True
        
        # Mock contracts cache
        web_client._contracts_cache = {
            'contracts': [
                {
                    "numero": "123456",
                    "referencia": "CT123456",
                    "nomeLocador": "TEST LANDLORD NAME",
                    "nomeLocatario": "Test Tenant Name",
                    "imovelAlternateId": "Narnia, 123",
                    "valorRenda": 100.00,
                    "estado": {"codigo": "ACTIVO", "label": "Ativo"}
                }
            ],
            'timestamp': datetime.now().timestamp()
        }
        
        processor = ReceiptProcessor(web_client)
        
        # Test each case
        for i, test_case in enumerate(test_cases):
            print(f"\n{i+1}. Testing: {test_case['name']}")
            
            receipt = test_case['receipt']
            expected_date = test_case['expected_payment_date']
            
            print(f"   Receipt data:")
            print(f"   - Period: {receipt.from_date} to {receipt.to_date}")
            print(f"   - Payment date: '{receipt.payment_date}'")
            print(f"   - Expected in payload: {expected_date}")
            
            # Get form data
            success, form_data = web_client.get_receipt_form(receipt.contract_id)
            if not success:
                print(f"   ❌ Failed to get form data")
                continue
            
            # Prepare submission data
            submission_data = processor._prepare_submission_data(receipt, form_data)
            
            # Issue receipt (this captures the payload)
            success, response = web_client.issue_receipt(submission_data)
            
            if success and captured_payloads:
                payload = captured_payloads[-1]  # Get the last captured payload
                actual_payment_date = payload.get('dataRecebimento')
                
                if actual_payment_date == expected_date:
                    print(f"   ✅ Payment date correctly sent: {actual_payment_date}")
                else:
                    print(f"   ❌ Payment date mismatch:")
                    print(f"      Expected: {expected_date}")
                    print(f"      Actual: {actual_payment_date}")
            else:
                print(f"   ❌ Failed to issue receipt or capture payload")
    
    # Summary
    print("\n" + "=" * 70)
    print("PAYMENT DATE ANALYSIS")
    print("=" * 70)
    
    if captured_payloads:
        print(f"\nCaptured {len(captured_payloads)} payloads:")
        
        for i, payload in enumerate(captured_payloads):
            test_name = test_cases[i]['name']
            expected = test_cases[i]['expected_payment_date']
            actual = payload.get('dataRecebimento')
            status = "✅" if actual == expected else "❌"
            
            print(f"\n{i+1}. {test_name}:")
            print(f"   - dataRecebimento: {actual}")
            print(f"   - Expected: {expected}")
            print(f"   - Status: {status}")
        
        # Show sample payload structure
        print(f"\nSample payload structure:")
        sample = captured_payloads[0]
        print(f"{{")
        print(f'  "numContrato": {sample.get("numContrato")},')
        print(f'  "dataInicio": "{sample.get("dataInicio")}",')
        print(f'  "dataFim": "{sample.get("dataFim")}",')
        print(f'  "dataRecebimento": "{sample.get("dataRecebimento")}",')
        print(f'  "valor": {sample.get("valor")}')
        print(f"  ... (other fields)")
        print(f"}}")
        
    else:
        print("❌ No payloads were captured during testing")
    
    print("\n" + "=" * 70)
    print("PAYMENT DATE TEST COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    test_payment_date_in_payload()
