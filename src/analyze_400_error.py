#!/usr/bin/env python3
"""
Analyze 400 error response in detail
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from web_client import WebClient
import requests
import re
import json

def analyze_400_error():
    """Analyze the 400 error response in detail."""
    
    print("=" * 60)
    print("400 ERROR ANALYSIS")
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
        csrf_pattern = r"_csrf:\s*{\s*parameterName:\s*'([^']+)',\s*token:\s*'([^']+)'"
        csrf_match = re.search(csrf_pattern, response.text)
        
        if not csrf_match:
            print("❌ CSRF token not found")
            return
        
        csrf_param_name = csrf_match.group(1)
        csrf_token = csrf_match.group(2)
        print(f"✅ CSRF Token: {csrf_token[:20]}...")
        
        # Look for more configuration data in the JavaScript
        print("\n2. Analyzing JavaScript configuration...")
        
        # Look for form field requirements
        form_config_patterns = [
            r"requiredFields:\s*\[([^\]]+)\]",
            r"fieldNames:\s*\{([^}]+)\}",
            r"validation:\s*\{([^}]+)\}",
            r"authConfig:\s*\{([^}]+)\}",
        ]
        
        for pattern in form_config_patterns:
            matches = re.findall(pattern, response.text)
            if matches:
                print(f"Found config pattern: {pattern}")
                for match in matches[:2]:  # Show first 2 matches
                    print(f"   {match[:100]}...")
        
        # Try to find any mentions of NIF validation
        nif_patterns = [
            r"nif[^{]*{[^}]+}",
            r"NIF[^{]*{[^}]+}",
            r"validateNIF[^{]*{[^}]+}",
        ]
        
        for pattern in nif_patterns:
            matches = re.findall(pattern, response.text, re.IGNORECASE)
            if matches:
                print(f"Found NIF pattern: {pattern}")
                for match in matches[:2]:
                    print(f"   {match}")
        
        # Set up the form data with different attempts
        test_scenarios = [
            {
                'name': 'NIF with authMethod N',
                'data': {
                    csrf_param_name: csrf_token,
                    'nif': username,
                    'password': password,
                    'partID': 'PFAP',
                    'authMethod': 'N',
                    'authVersion': '2'
                }
            },
            {
                'name': 'username instead of nif',
                'data': {
                    csrf_param_name: csrf_token,
                    'username': username,
                    'password': password,
                    'partID': 'PFAP',
                    'authMethod': 'N',
                    'authVersion': '2'
                }
            },
            {
                'name': 'NIF without authMethod',
                'data': {
                    csrf_param_name: csrf_token,
                    'nif': username,
                    'password': password,
                    'partID': 'PFAP'
                }
            },
            {
                'name': 'Original format with N authMethod',
                'data': {
                    csrf_param_name: csrf_token,
                    'username': username,
                    'password': password,
                    'partID': 'PFAP',
                    'authMethod': 'N'
                }
            }
        ]
        
        # Set headers
        client._set_login_headers()
        
        print(f"\n3. Testing different scenarios...")
        
        for scenario in test_scenarios:
            print(f"\n   Testing: {scenario['name']}")
            
            try:
                response = client.session.post(
                    client.login_url,
                    data=scenario['data'],
                    timeout=10,
                    allow_redirects=False
                )
                
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 400:
                    print(f"   Headers: {dict(response.headers)}")
                    
                    # Check for error details in response
                    if response.text:
                        print(f"   Response length: {len(response.text)} chars")
                        
                        # Look for JSON error messages
                        try:
                            if response.headers.get('content-type', '').startswith('application/json'):
                                error_data = response.json()
                                print(f"   JSON Error: {error_data}")
                            else:
                                # Look for HTML error messages
                                error_patterns = [
                                    r'<div[^>]*class="[^"]*error[^"]*"[^>]*>([^<]+)</div>',
                                    r'<span[^>]*class="[^"]*error[^"]*"[^>]*>([^<]+)</span>',
                                    r'<p[^>]*class="[^"]*error[^"]*"[^>]*>([^<]+)</p>',
                                    r'"error":\s*"([^"]+)"',
                                    r'"message":\s*"([^"]+)"'
                                ]
                                
                                for pattern in error_patterns:
                                    matches = re.findall(pattern, response.text, re.IGNORECASE)
                                    if matches:
                                        print(f"   Error messages found: {matches}")
                                        break
                                else:
                                    # Show first part of response if no specific error found
                                    print(f"   Response preview: {response.text[:200]}...")
                                    
                        except json.JSONDecodeError:
                            print(f"   Non-JSON response")
                            
                        # Save the 400 response for analysis
                        filename = f"400_response_{scenario['name'].replace(' ', '_')}.html"
                        with open(filename, 'w', encoding='utf-8') as f:
                            f.write(response.text)
                        print(f"   💾 Saved to {filename}")
                        
                elif response.status_code in [200, 302, 303]:
                    print(f"   ✅ Success! Status {response.status_code}")
                    if 'location' in response.headers:
                        print(f"   Redirect: {response.headers['location']}")
                    break
                else:
                    print(f"   Other status: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                print(f"   ❌ Request failed: {e}")
                
        print(f"\n4. Summary:")
        print(f"   • All scenarios returned 400 suggests field validation issue")
        print(f"   • Check saved response files for specific error messages")
        print(f"   • May need to analyze the exact field names/formats expected")
        
    except Exception as e:
        print(f"❌ Analysis failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_400_error()
