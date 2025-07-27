"""
Test 2FA detection with real portal response data
"""
import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_2fa_detection():
    """Test 2FA detection with actual portal response."""
    from web_client import WebClient
    import requests
    
    # Create a mock response with the actual 2FA indicators
    class MockResponse:
        def __init__(self, text, url="https://www.acesso.gov.pt/v2/login", status_code=200):
            self.text = text
            self.url = url
            self.status_code = status_code
    
    # Actual response content that indicates 2FA is required
    response_with_2fa = '''
    <script type="text/javascript">
      var model = {
        is2FA: parseBoolean('true'),
        phone: stringOrNull('*******35'),
        nifIn2FA: stringOrNull('987654321'),
        smsFailed: parseBoolean(''),
        codeExpired2Fa: parseBoolean('true'),
        sendsRemaining: parseInt('2') || null,
        fieldError: JSON.parse('{"field":"codigoSms2Fa","errorMsg":"Código incorreto. Por favor, solicite o envio de um novo código."}' || null),
      }
    </script>
    '''
    
    # Response without 2FA
    response_without_2fa = '''
    <script type="text/javascript">
      var model = {
        is2FA: parseBoolean('false'),
        loginSuccess: parseBoolean('true'),
        showAlert: parseBoolean('false'),
      }
    </script>
    '''
    
    # Test with 2FA required response
    print("🔍 Testing 2FA Detection...")
    
    web_client = WebClient(testing_mode=True)
    
    # Test Case 1: Response with 2FA required
    print("\n1. Testing response with 2FA required:")
    mock_response_2fa = MockResponse(response_with_2fa)
    success, message = web_client._analyze_login_response(mock_response_2fa)
    
    if message == "2FA_REQUIRED":
        print("   ✅ 2FA correctly detected")
        print(f"   📱 Portal indicates 2FA is required")
        print(f"   🔧 Response: {message}")
    else:
        print("   ❌ 2FA not detected when it should be")
        print(f"   🔧 Response: {message}")
    
    # Test Case 2: Response without 2FA
    print("\n2. Testing response without 2FA:")
    mock_response_no_2fa = MockResponse(response_without_2fa)
    success, message = web_client._analyze_login_response(mock_response_no_2fa)
    
    if message != "2FA_REQUIRED":
        print("   ✅ No 2FA correctly detected (normal login flow)")
        print(f"   🔧 Response: {message}")
    else:
        print("   ❌ 2FA incorrectly detected when not required")
        print(f"   🔧 Response: {message}")
    
    # Test Case 3: Check specific indicators
    print("\n3. Testing specific 2FA indicators:")
    
    indicators_to_test = [
        ("is2FA: parseBoolean('true')", True),
        ("is2FA: parseBoolean('false')", False),
        ('fieldError: JSON.parse(\'{"field":"codigoSms2Fa"', True),
        ("loginSuccess: parseBoolean('true')", False),
    ]
    
    for indicator, should_detect_2fa in indicators_to_test:
        test_response = f"<script>{indicator}</script>"
        mock_resp = MockResponse(test_response)
        success, message = web_client._analyze_login_response(mock_resp)
        
        is_2fa_detected = (message == "2FA_REQUIRED")
        
        if is_2fa_detected == should_detect_2fa:
            status = "✅"
        else:
            status = "❌"
        
        print(f"   {status} '{indicator[:30]}...' → 2FA: {is_2fa_detected} (expected: {should_detect_2fa})")
    
    print(f"\n📊 2FA Detection Summary:")
    print(f"   • Only triggers when portal indicates is2FA: true")
    print(f"   • Detects SMS code field errors")
    print(f"   • Transparent for accounts without 2FA")
    print(f"   • Follows exact portal response indicators")

if __name__ == "__main__":
    print("=" * 80)
    print("2FA DETECTION TEST WITH PORTAL RESPONSE DATA")
    print("=" * 80)
    test_2fa_detection()
