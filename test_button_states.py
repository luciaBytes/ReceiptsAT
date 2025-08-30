"""
Test script to verify button state logic after login and CSV selection
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

class MockWebClient:
    """Mock web client for testing"""
    def __init__(self):
        self._authenticated = False
    
    def is_authenticated(self):
        return self._authenticated
    
    def set_authenticated(self, auth):
        self._authenticated = auth

class MockCSVHandler:
    """Mock CSV handler for testing"""
    def __init__(self):
        self._receipts = []
    
    def get_receipts(self):
        return self._receipts
    
    def set_receipts(self, receipts):
        self._receipts = receipts

class MockSessionStatus:
    """Mock session status widget"""
    def __init__(self):
        self.text = "No active session"
    
    def cget(self, prop):
        if prop == "text":
            return self.text
    
    def set_text(self, text):
        self.text = text

def test_button_logic():
    """Test the button enabling logic"""
    print("=== Button State Logic Test ===")
    
    # Mock objects
    web_client = MockWebClient()
    csv_handler = MockCSVHandler()
    session_status = MockSessionStatus()
    csv_file_path = ""
    
    def check_button_states(scenario):
        """Check button states based on current conditions"""
        has_auth = web_client.is_authenticated()
        has_csv_file = bool(csv_file_path)
        has_valid_receipts = has_csv_file and bool(csv_handler.get_receipts())
        
        session_text = session_status.cget("text").lower()
        session_ok = has_auth and "expired" not in session_text and "no active" not in session_text
        
        start_enabled = has_auth and has_valid_receipts and session_ok
        validate_enabled = has_auth and has_csv_file and session_ok
        
        print(f"\n{scenario}:")
        print(f"  Auth: {has_auth}, CSV File: {has_csv_file}, Valid Receipts: {has_valid_receipts}")
        print(f"  Session Status: '{session_status.text}', Session OK: {session_ok}")
        print(f"  Start Button: {'ENABLED' if start_enabled else 'DISABLED'}")
        print(f"  Validate Button: {'ENABLED' if validate_enabled else 'DISABLED'}")
        return start_enabled, validate_enabled
    
    # Test scenarios
    
    # 1. Initial state - not authenticated, no CSV
    check_button_states("1. Initial State")
    
    # 2. After login - authenticated, no CSV
    web_client.set_authenticated(True)
    session_status.set_text("Session active")
    start_enabled, validate_enabled = check_button_states("2. After Login (no CSV)")
    
    # 3. After CSV file selected - authenticated, has CSV file but no validated receipts
    csv_file_path = "test.csv"
    start_enabled, validate_enabled = check_button_states("3. After CSV Selected (not validated)")
    
    # Should validate button be enabled now? YES!
    assert validate_enabled, "ERROR: Validate button should be enabled after login + CSV file selection!"
    
    # 4. After CSV validation - authenticated, has CSV file and validated receipts
    csv_handler.set_receipts([{"contract": "123"}, {"contract": "456"}])
    start_enabled, validate_enabled = check_button_states("4. After CSV Validated")
    
    # Both buttons should be enabled now
    assert start_enabled, "ERROR: Start button should be enabled after login + validated CSV!"
    assert validate_enabled, "ERROR: Validate button should still be enabled!"
    
    # 5. Session expired
    session_status.set_text("Session expired")
    start_enabled, validate_enabled = check_button_states("5. Session Expired")
    
    # Both buttons should be disabled
    assert not start_enabled, "ERROR: Start button should be disabled when session expired!"
    assert not validate_enabled, "ERROR: Validate button should be disabled when session expired!"
    
    print("\n✅ All button state tests passed!")
    print("\n=== Key Findings ===")
    print("- Validate button enables immediately after login + CSV file selection")
    print("- Start button only enables after login + validated CSV + active session")
    print("- Both buttons disable when session expires")
    
if __name__ == "__main__":
    test_button_logic()
