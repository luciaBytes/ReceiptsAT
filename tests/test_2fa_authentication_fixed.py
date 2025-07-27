#!/usr/bin/env python3
"""
Test script to demonstrate 2FA SMS authentication functionality.
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from web_client import WebClient

def test_2fa_authentication():
    """Test 2FA SMS authentication functionality with timeout protection."""
    print("Testing 2FA authentication functionality...")
    
    # Initialize web client in testing mode (this should use mocks)
    web_client = WebClient(testing_mode=True)
    
    # Test 1: Normal login (no 2FA)
    print("1. Testing normal login...")
    success, message = web_client.login("demo", "demo")
    assert success, f"Normal login should succeed: {message}"
    print(f"   ✅ Normal login successful: {message}")
    
    # Reset for next test
    web_client.logout()
    
    # Test 2: 2FA-enabled login
    print("2. Testing 2FA trigger...")
    success, message = web_client.login("2fa", "demo")  # Should trigger 2FA
    assert not success, "2FA login should not succeed initially"
    assert message == "2FA_REQUIRED", f"Should require 2FA, got: {message}"
    assert web_client.pending_2fa, "pending_2fa flag should be set"
    print(f"   ✅ 2FA requirement detected: {message}")
    
    # Test 3: Invalid SMS code
    print("3. Testing invalid SMS code...")
    success, message = web_client.login("", "", "999999")
    assert not success, "Invalid SMS code should fail"
    print(f"   ✅ Invalid code rejected: {message}")
    
    # Test 4: Valid SMS code
    print("4. Testing valid SMS code...")
    success, message = web_client.login("", "", "123456")
    assert success, f"Valid SMS code should succeed: {message}"
    assert web_client.authenticated, "Should be authenticated after valid 2FA"
    assert not web_client.pending_2fa, "pending_2fa flag should be cleared"
    print(f"   ✅ Valid code accepted: {message}")
    
    print("✅ All 2FA tests passed!")

def test_2fa_workflow_simulation():
    """Test complete 2FA workflow simulation."""
    print("Testing 2FA workflow simulation...")
    
    web_client = WebClient(testing_mode=True)
    
    # Simulate complete workflow
    print("1. Initial login with 2FA user...")
    success, message = web_client.login("2fa", "demo")
    assert message == "2FA_REQUIRED"
    print("   ✅ 2FA required as expected")
    
    print("2. Complete 2FA verification...")
    success, message = web_client.login("", "", "123456")
    assert success
    print("   ✅ 2FA verification successful")
    
    print("3. Verify authenticated state...")
    assert web_client.authenticated
    assert not web_client.pending_2fa
    print("   ✅ Authentication state correct")
    
    print("✅ 2FA workflow simulation completed!")

if __name__ == "__main__":
    test_2fa_authentication()
    test_2fa_workflow_simulation()
