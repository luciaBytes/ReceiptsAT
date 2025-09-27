#!/usr/bin/env python3
"""
Test the updated WebClient with correct authentication
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from web_client import WebClient

def test_updated_client():
    """Test the updated WebClient with correct authentication."""
    
    print("=" * 60)
    print("TESTING UPDATED WEB CLIENT")
    print("=" * 60)
    
    # Use mock credentials for testing
    username = "test"
    password = "test"
    
    print(f"Using credentials: {username} / {'*' * len(password)}")

    # Demo client
    print(f"\n1. Testing authentication...")
    client = WebClient()

    success, message = client.login(username, password)
    
    if success:
        print(f"   ✅ Authentication successful!")
        print(f"   Message: {message}")
        
        # Test that we can get the receipt creation page
        print(f"\n2. Testing receipt page access...")
        try:
            receipt_url = f"{client.auth_base_url}/pfap/criarRecibo"
            response = client.session.get(receipt_url, timeout=10)
            
            if response.status_code == 200:
                print(f"   ✅ Can access receipt page (status: {response.status_code})")
                
                # Check if we're still logged in (look for logout link or user info)
                if 'logout' in response.text.lower() or 'sair' in response.text.lower():
                    print(f"   ✅ Still logged in (found logout link)")
                else:
                    print(f"   ⚠️  May not be fully logged in (no logout link found)")
                    
                # Save a sample of the page
                with open('logged_in_receipt_page.html', 'w', encoding='utf-8') as f:
                    f.write(response.text[:5000] + "..." if len(response.text) > 5000 else response.text)
                print(f"   💾 Saved sample to logged_in_receipt_page.html")
                
            else:
                print(f"   ❌ Cannot access receipt page (status: {response.status_code})")
                
                if response.status_code == 302:
                    location = response.headers.get('location', 'No location header')
                    print(f"   Redirect to: {location}")
                    
        except Exception as e:
            print(f"   ❌ Error accessing receipt page: {str(e)}")
        
    else:
        print(f"   ❌ Authentication failed!")
        print(f"   Message: {message}")
        return False
    
    print(f"\n3. Testing session persistence...")
    # Make another request to see if session is maintained
    try:
        test_url = f"{client.auth_base_url}/"
        response = client.session.get(test_url, timeout=10)
        print(f"   Status for authenticated request: {response.status_code}")
        
        if response.status_code == 200:
            print(f"   ✅ Session maintained")
        else:
            print(f"   ⚠️  Session may have issues")
            
    except Exception as e:
        print(f"   ❌ Error testing session: {str(e)}")
    
    return success

if __name__ == "__main__":
    success = test_updated_client()
    if success:
        print("\n🎉 WEB CLIENT WORKING CORRECTLY!")
    else:
        print("\n❌ WEB CLIENT NEEDS FIXES")
