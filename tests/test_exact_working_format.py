#!/usr/bin/env python3
"""
Test authentication with the exact format from the working request
"""
import sys
import os
sys.path.append('src')

from web_client import WebClient

def load_test_credentials():
    """Load test credentials from credentials file."""
    try:
        with open('credentials', 'r') as f:
            lines = f.read().strip().split('\n')
            if len(lines) >= 2:
                nif = lines[0].strip()
                password = lines[1].strip()
                return nif, password
    except FileNotFoundError:
        print("❌ Error: 'credentials' file not found.")
        print("   Create a 'credentials' file with:")
        print("   Line 1: Your NIF")
        print("   Line 2: Your password")
        return None, None
    except Exception as e:
        print(f"❌ Error reading credentials: {e}")
        return None, None
    
    print("❌ Error: Insufficient credentials in file")
    return None, None

def test_exact_working_format():
    """Test authentication using the exact format from the working request."""
    
    print("=== TESTING EXACT WORKING FORMAT ===")
    
    # Load credentials from file
    nif, password = load_test_credentials()
    if not nif or not password:
        return False
    
    client = WebClient()
    
    # Test 1: Check form data preparation matches working format
    print("1. Testing form data preparation...")
    form_data = client._get_login_form_data()
    csrf_data = client._get_csrf_token_data()
    
    if form_data and csrf_data:
        # Add CSRF token
        form_data[csrf_data['parameterName']] = csrf_data['token']
        
        # Add credentials in correct format
        form_data.update({
            'username': nif,
            'password': password
        })
        
        print("   Expected working format:")
        print("     username=34234235&password=??????&partID=PFAP&selectedAuthMethod=N&_csrf=xxxxx&authVersion=2")
        
        print("\n   Our format:")
        form_parts = []
        for key, value in form_data.items():
            if key == 'password':
                form_parts.append(f"{key}=??????")
            elif key == csrf_data['parameterName']:
                form_parts.append(f"{key}={value[:8]}...")
            else:
                form_parts.append(f"{key}={value}")
        print(f"     {'&'.join(form_parts)}")
        
        # Check if our format matches the working format
        expected_keys = {'username', 'password', 'partID', 'selectedAuthMethod', '_csrf', 'authVersion'}
        our_keys = set(form_data.keys())
        
        missing_keys = expected_keys - our_keys
        extra_keys = our_keys - expected_keys
        
        print(f"\n   Format comparison:")
        print(f"     Missing keys: {missing_keys if missing_keys else 'None ✅'}")
        print(f"     Extra keys: {extra_keys if extra_keys else 'None ✅'}")
        
        if not missing_keys and not extra_keys:
            print("     🎉 Format matches perfectly!")
        
    # Test 2: Test with exact headers from working request
    print("\n2. Testing with exact working headers...")
    
    import requests
    
    # Headers from the working request
    working_headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'pt-PT,pt;q=0.9,pt-BR;q=0.8,en;q=0.7,en-US;q=0.6,en-GB;q=0.5',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'https://www.acesso.gov.pt',
        'Referer': 'https://www.acesso.gov.pt/v2/loginForm?partID=PFAP',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0',
        'sec-ch-ua': '"Not;A=Brand";v="99", "Microsoft Edge";v="139", "Chromium";v="139"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"'
    }
    
    try:
        # Test with fake but properly formatted NIF
        test_response = client.session.post(
            'https://www.acesso.gov.pt/v2/login',
            data=form_data,
            headers=working_headers,
            timeout=10,
            allow_redirects=False
        )
        
        print(f"   Response status: {test_response.status_code}")
        
        if test_response.status_code == 200:
            print("   🎉 SUCCESS! Got 200 OK (same as working request)")
            
            # Check if response indicates authentication attempt was processed
            response_text = test_response.text.lower()
            if 'erro' in response_text or 'error' in response_text:
                print("     -> Response contains error (likely invalid credentials)")
                print("     -> This is expected with fake credentials - format is working!")
            elif 'success' in response_text or 'sucesso' in response_text:
                print("     -> Response contains success indicators")
            else:
                print("     -> Response processed (no obvious success/error indicators)")
                
        elif test_response.status_code in [302, 303, 307, 308]:
            redirect_location = test_response.headers.get('Location', '')
            print(f"   🎉 SUCCESS! Got redirect to: {redirect_location}")
            print("     -> This indicates the request format is working!")
            
        else:
            print(f"   Status: {test_response.status_code}")
            print(f"   Response: {test_response.text[:200]}")
            
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 3: Test the updated login method
    print("\n3. Testing updated login method...")
    try:
        # Use a properly formatted Portuguese NIF for testing
        success, message = client.login('123456789', 'testpassword')  # Format like NIF
        print(f"   Login result: {'SUCCESS' if success else 'FAILED'}")
        print(f"   Message: {message}")
        
        if not success:
            if '200' in message or 'redirect' in message.lower():
                print("   -> Request format is working! (Error likely due to fake credentials)")
            elif '500' in message or '400' in message:
                print("   -> Still getting server errors - need more investigation")
            else:
                print("   -> Different type of error")
    
    except Exception as e:
        print(f"   Login method error: {e}")

if __name__ == "__main__":
    test_exact_working_format()
