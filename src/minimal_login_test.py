#!/usr/bin/env python3
"""
Minimal login attempt with only essential fields
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from web_client import WebClient
import requests

def minimal_login_test():
    """Try login with minimal essential fields only."""
    
    print("=" * 60)
    print("MINIMAL LOGIN TEST")
    print("=" * 60)
    
    # Use mock credentials for testing
    username = "test"
    password = "test"
    
    print(f"Using credentials: {username} / {'*' * len(password)}")
    
    # Demo client
    client = WebClient()
    
    try:
        # Get the login page first
        print("\n1. Getting login page...")
        response = client.session.get(client.login_page_url, timeout=10)
        response.raise_for_status()
        
        # Extract CSRF token
        import re
        csrf_pattern = r"_csrf:\s*{\s*parameterName:\s*'([^']+)',\s*token:\s*'([^']+)'"
        csrf_match = re.search(csrf_pattern, response.text)
        
        if not csrf_match:
            print("❌ CSRF token not found")
            return
        
        csrf_param_name = csrf_match.group(1)
        csrf_token = csrf_match.group(2)
        print(f"✅ CSRF Token: {csrf_token[:20]}...")
        
        # Prepare MINIMAL form data - only the essentials
        print("\n2. Preparing minimal form data...")
        minimal_form_data = {
            csrf_param_name: csrf_token,  # CSRF token (required)
            'username': username,         # Username field
            'password': password,         # Password field
            'partID': 'PFAP'             # Part ID from URL
        }
        
        print("Minimal form data:")
        for key, value in minimal_form_data.items():
            if 'password' in key.lower():
                print(f"   {key}: [REDACTED]")
            else:
                print(f"   {key}: {value}")
        
        # Set headers
        client._set_login_headers()
        
        print(f"\n3. Making minimal login request to {client.login_url}...")
        
        try:
            response = client.session.post(
                client.login_url,
                data=minimal_form_data,
                timeout=15,
                allow_redirects=False
            )
            
            print(f"\n4. Minimal login response:")
            print(f"   Status: {response.status_code}")
            print(f"   URL: {response.url}")
            
            if response.status_code == 500:
                print("   ❌ Still getting 500 error with minimal fields")
                
                # Save minimal response
                with open('minimal_500_response.html', 'w', encoding='utf-8') as f:
                    f.write(response.text)
                print("   💾 Saved to minimal_500_response.html")
                
            elif response.status_code in [200, 302, 303]:
                print("   ✅ Success! No more 500 error")
                
                if 'location' in response.headers:
                    print(f"   Redirect to: {response.headers['location']}")
                
                # Check response content
                response_lower = response.text.lower()
                if any(success_indicator in response_lower for success_indicator in [
                    'dashboard', 'bem-vindo', 'sucesso', 'authenticated'
                ]):
                    print("   ✅ Login appears successful!")
                elif any(error_indicator in response_lower for error_indicator in [
                    'erro', 'invalid', 'incorreto', 'failed'
                ]):
                    print("   ❌ Login failed - invalid credentials")
                else:
                    print("   ⚠️  Login status unclear")
                    
                # Save successful response for analysis
                with open('minimal_success_response.html', 'w', encoding='utf-8') as f:
                    f.write(response.text)
                print("   💾 Saved to minimal_success_response.html")
                
            else:
                print(f"   ⚠️  Unexpected status: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Request failed: {e}")
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    minimal_login_test()
