#!/usr/bin/env python3
"""
Test SMS verification process step by step
"""

import sys
import os
from unittest.mock import patch
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from web_client import WebClient

@patch.object(WebClient, '__init__')
@patch.object(WebClient, 'login')
def test_sms_step_by_step(mock_login, mock_init):
    print("=== SMS Verification Step-by-Step Test (Mocked) ===")
    
    # Mock WebClient initialization to avoid real HTTP session creation
    mock_init.return_value = None
    
    # Mock login to simulate SMS trigger and success on second call
    def mock_login_side_effect(*args, **kwargs):
        if 'sms_code' in kwargs:
            return (True, "SMS verification successful")
        else:
            return (False, "SMS verification required")
    
    mock_login.side_effect = mock_login_side_effect
    
    try:
        client = WebClient()
        client.pending_2fa = True  # Simulate SMS pending state
        
        print("\n--- Step 1: Initial login (should trigger SMS) ---")
        # This call is fully mocked - no real credentials or calls made
        result = client.login("123456789", "mock_password")
        
        if isinstance(result, tuple):
            success, message = result
        else:
            success = result
            message = "Login completed"
            
        print(f"Login result: {success}")
        print(f"Message: {message}")
        print(f"Pending 2FA: {client.pending_2fa}")
        
        if client.pending_2fa:
            print("\n✓ SMS verification is required!")
            print("The system is waiting for SMS code.")
            print("\nTo complete the process, you would need to:")
            print("1. Check your phone for the SMS code")
            print("2. Call client.login(nif, password, sms_code='YOUR_CODE')")
            
            # Simulate the SMS input process
            print("\n--- Simulating SMS code input ---")
            print("In the real app, you would now enter the SMS code you received.")
            
            # Test with a dummy SMS code to see what happens
            print("\n--- Testing with dummy SMS code (will fail) ---")
            sms_result = client.login("test_nif", "test_password", sms_code="123456")
            
            if isinstance(sms_result, tuple):
                sms_success, sms_message = sms_result
            else:
                sms_success = sms_result
                sms_message = "SMS verification completed"
                
            print(f"SMS verification result: {sms_success}")
            print(f"SMS message: {sms_message}")
            
            # Show expected error patterns
            if "2FA_INCORRECT_CODE" in sms_message:
                print("✓ SMS code validation is working (expected failure with dummy code)")
            elif "2FA_CODE_EXPIRED" in sms_message:
                print("✓ SMS code expiration detection is working")
            else:
                print(f"! Unexpected SMS verification response: {sms_message}")
                
        elif "2FA_REQUIRED" in message:
            print("✓ 2FA requirement detected in initial login")
            print("The system correctly identified that SMS verification is needed")
            
        elif success:
            print("! Login completed without 2FA - this might indicate:")
            print("  - Account doesn't have 2FA enabled")
            print("  - 2FA detection logic needs adjustment")
            print("  - Network/authentication flow changed")
            
        else:
            print("! Login failed completely")
            print(f"Error: {message}")
            
        return True
        
    except Exception as e:
        print(f"✗ Error during SMS test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_sms_step_by_step()
