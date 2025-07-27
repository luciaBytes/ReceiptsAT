#!/usr/bin/env python3
"""
Authentication method specific login test
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from web_client import WebClient
import requests
import re

def auth_method_login_test():
    """Try login with specific authentication method parameters."""
    
    print("=" * 60)
    print("AUTHENTICATION METHOD LOGIN TEST")
    print("=" * 60)
    
    # Use mock credentials for testing
    username = "test"
    password = "test"
    
    print(f"Using credentials: {username} / {'*' * len(password)}")
    
    client = WebClient(testing_mode=False)
    
    try:
        # Get the login page first
        print("\n1. Getting login page and extracting configuration...")
        response = client.session.get(client.login_page_url, timeout=10)
        response.raise_for_status()
        
        # Extract CSRF token
        csrf_pattern = r"_csrf:\s*{\s*parameterName:\s*'([^']+)',\s*token:\s*'([^']+)'"
        csrf_match = re.search(csrf_pattern, response.text)
        
        if not csrf_match:
            print("❌ CSRF token not found")
            return
        
        csrf_param_name = csrf_match.group(1)
        csrf_token = csrf_match.group(2)
        print(f"✅ CSRF Token: {csrf_token[:20]}...")
        
        # Extract authentication methods
        auth_methods_pattern = r"authMethods:\s*stringOrNull\('([^']+)'\)"
        auth_methods_match = re.search(auth_methods_pattern, response.text)
        
        if auth_methods_match:
            auth_methods = auth_methods_match.group(1)
            print(f"✅ Auth methods: {auth_methods}")
        else:
            print("❌ Auth methods not found")
            auth_methods = "NIF,EORI,CARTAO_DE_CIDADAO"  # Default from previous analysis
        
        # Since username is numeric (NIF), try NIF authentication
        print(f"\n2. Trying NIF authentication method...")
        
        # Check if username looks like NIF (9 digits)
        is_nif = username.isdigit() and len(username) == 9
        print(f"Username appears to be NIF: {is_nif}")
        
        if is_nif:
            # Try NIF-specific login
            nif_form_data = {
                csrf_param_name: csrf_token,
                'nif': username,        # NIF field instead of username
                'password': password,
                'partID': 'PFAP',
                'authMethod': 'N',      # N for NIF (based on authMethods conversion)
                'authVersion': '2'
            }
            
            print("NIF form data:")
            for key, value in nif_form_data.items():
                if 'password' in key.lower():
                    print(f"   {key}: [REDACTED]")
                else:
                    print(f"   {key}: {value}")
        else:
            # Try email authentication
            email_form_data = {
                csrf_param_name: csrf_token,
                'email': username,
                'password': password,
                'partID': 'PFAP',
                'authMethod': 'E',      # E for Email
                'authVersion': '2'
            }
            nif_form_data = email_form_data
            print("Email form data prepared")
        
        # Set headers
        client._set_login_headers()
        
        print(f"\n3. Making authentication method specific request...")
        
        try:
            response = client.session.post(
                client.login_url,
                data=nif_form_data,
                timeout=15,
                allow_redirects=False
            )
            
            print(f"\n4. Auth method response:")
            print(f"   Status: {response.status_code}")
            print(f"   URL: {response.url}")
            
            if response.status_code == 500:
                print("   ❌ Still 500 error with auth method")
                
                # Try alternative: post to different endpoint
                print("\n5. Trying alternative endpoint...")
                
                # Some systems use /loginNIF or /loginForm endpoints
                alternative_urls = [
                    f"{client.auth_base_url}/loginNIF",
                    f"{client.auth_base_url}/v2/loginNIF", 
                    f"{client.auth_base_url}/auth/login",
                    f"{client.auth_base_url}/api/login"
                ]
                
                for alt_url in alternative_urls:
                    print(f"   Trying: {alt_url}")
                    try:
                        alt_response = client.session.post(
                            alt_url,
                            data=nif_form_data,
                            timeout=10,
                            allow_redirects=False
                        )
                        print(f"     Status: {alt_response.status_code}")
                        
                        if alt_response.status_code != 500:
                            print(f"     ✅ Found working endpoint: {alt_url}")
                            response = alt_response
                            break
                    except:
                        print(f"     ❌ Failed")
                        continue
                
            if response.status_code == 500:
                print("\n❌ All attempts resulted in 500 error")
                print("\nThis suggests the server has an internal issue or:")
                print("1. The authentication system is temporarily down")
                print("2. There's a server-side bug with the current configuration")
                print("3. Additional required fields are missing")
                print("4. Rate limiting or IP blocking is in effect")
                print("5. The credentials format is incorrect")
                
            elif response.status_code in [200, 302, 303]:
                print("   ✅ Success! No 500 error")
                
                if 'location' in response.headers:
                    location = response.headers['location']
                    print(f"   Redirect to: {location}")
                    
                    # Check if redirect indicates success or failure
                    if 'error' in location.lower() or 'denied' in location.lower():
                        print("   ❌ Redirect indicates authentication failure")
                    elif 'dashboard' in location.lower() or 'home' in location.lower():
                        print("   ✅ Redirect indicates authentication success")
                    else:
                        print("   ⚠️  Redirect purpose unclear")
                
                # Save response
                with open('auth_method_response.html', 'w', encoding='utf-8') as f:
                    f.write(response.text)
                print("   💾 Saved to auth_method_response.html")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Request failed: {e}")
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    auth_method_login_test()
