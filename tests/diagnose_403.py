#!/usr/bin/env python3
"""
Diagnostic script for 403 Forbidden login error
"""
import sys
import os
sys.path.append('src')

from web_client import WebClient
import requests
import json

def diagnose_403_error():
    """Diagnose the 403 Forbidden error in login."""
    
    print("=== DIAGNOSING 403 FORBIDDEN ERROR ===")
    print()
    
    client = WebClient()
    
    # Step 1: Test basic connectivity
    print("1. Testing basic connectivity...")
    try:
        response = client.session.get(client.login_page_url, timeout=10)
        print(f"   ✅ Login page accessible: {response.status_code}")
        print(f"   URL: {response.url}")
    except Exception as e:
        print(f"   ❌ Cannot access login page: {e}")
        return
    
    # Step 2: Check form data extraction
    print("\n2. Testing form data extraction...")
    form_data = client._get_login_form_data()
    if form_data:
        print(f"   ✅ Form data extracted: {len(form_data)} fields")
        for key, value in form_data.items():
            print(f"      {key}: {value}")
    else:
        print("   ❌ Failed to extract form data")
        return
    
    # Step 3: Test login with dummy credentials to see exact error
    print("\n3. Testing login submission (with dummy credentials)...")
    
    # Add dummy credentials to form data
    test_form_data = form_data.copy()
    test_form_data.update({
        'username': '000000000',  # Dummy NIF
        'password': 'testpass123',
        'envioDadosPessoais': 'false',
        'selectedAuthMethod': 'N'
    })
    
    print("   Form data to be submitted:")
    for key, value in test_form_data.items():
        if 'password' in key.lower():
            print(f"      {key}: [HIDDEN]")
        else:
            print(f"      {key}: {value}")
    
    # Set headers
    client._set_login_headers()
    
    print(f"\n   Headers being sent:")
    for key, value in client.session.headers.items():
        print(f"      {key}: {value}")
    
    # Attempt the POST request
    print(f"\n   Submitting POST to: {client.login_url}")
    try:
        response = client.session.post(
            client.login_url,
            data=test_form_data,
            timeout=15,
            allow_redirects=False  # Don't follow redirects to see exact response
        )
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response URL: {response.url}")
        print(f"   Response Headers:")
        for key, value in response.headers.items():
            print(f"      {key}: {value}")
        
        if response.status_code == 403:
            print(f"\n   ❌ 403 FORBIDDEN ERROR DETAILS:")
            print(f"   Response Length: {len(response.text)} chars")
            
            # Check if response contains error information
            response_lower = response.text.lower()
            error_indicators = [
                'forbidden', 'access denied', 'erro', 'error',
                'csrf', 'token', 'security', 'blocked', 'rate limit'
            ]
            
            found_indicators = []
            for indicator in error_indicators:
                if indicator in response_lower:
                    found_indicators.append(indicator)
            
            if found_indicators:
                print(f"   Potential error indicators found: {found_indicators}")
            
            # Save response for manual inspection
            with open('403_error_response.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print(f"   💾 Full response saved to: 403_error_response.html")
            
            # Show first 500 characters of response
            print(f"\n   First 500 characters of response:")
            print(f"   {'-'*50}")
            print(response.text[:500])
            print(f"   {'-'*50}")
            
        elif response.status_code in [200, 302, 303]:
            print(f"   ✅ Request accepted! Status: {response.status_code}")
            if 'location' in response.headers:
                print(f"   Redirect to: {response.headers['location']}")
        
    except requests.exceptions.HTTPError as e:
        print(f"   ❌ HTTP Error: {e}")
        print(f"   Response status: {e.response.status_code}")
        print(f"   Response text (first 200 chars): {e.response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
    
    # Step 4: Try alternative approaches
    print("\n4. Testing alternative approaches...")
    
    # Try with different Content-Type
    print("\n   4a. Trying with application/json content-type...")
    try:
        headers = client.session.headers.copy()
        headers['Content-Type'] = 'application/json'
        
        json_data = json.dumps(test_form_data)
        
        response = client.session.post(
            client.login_url,
            data=json_data,
            headers=headers,
            timeout=15,
            allow_redirects=False
        )
        print(f"      Status with JSON: {response.status_code}")
        
    except Exception as e:
        print(f"      JSON approach failed: {e}")
    
    # Try without some headers
    print("\n   4b. Trying with minimal headers...")
    try:
        minimal_session = requests.Session()
        minimal_session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Content-Type': 'application/x-www-form-urlencoded',
        })
        
        response = minimal_session.post(
            client.login_url,
            data=test_form_data,
            timeout=15,
            allow_redirects=False
        )
        print(f"      Status with minimal headers: {response.status_code}")
        
    except Exception as e:
        print(f"      Minimal headers approach failed: {e}")
    
    print("\n=== DIAGNOSIS COMPLETE ===")
    print("\nNext steps:")
    print("1. Check 403_error_response.html for detailed error message")
    print("2. Look for CSRF token requirements")
    print("3. Check if login endpoint has changed")
    print("4. Verify if additional authentication steps are needed")

if __name__ == "__main__":
    diagnose_403_error()
