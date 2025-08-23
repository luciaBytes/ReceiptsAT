"""
Demo of the user-friendly error handling system.
Shows how technical errors are converted to user-friendly messages.
"""

from src.utils.error_handler import UserFriendlyErrorHandler

def demo_error_handling():
    """Demonstrate the error handling system with various error types."""
    handler = UserFriendlyErrorHandler()
    
    # Demo various error scenarios
    error_scenarios = [
        (Exception("Invalid credentials provided"), "login"),
        (Exception("2FA verification required"), "authentication"),
        (Exception("Connection failed to server"), "network"),
        (Exception("CSV format is invalid - missing columns"), "csv_processing"),
        (Exception("Contract not found in portal system"), "receipt_generation"),
        (Exception("Session expired, please login again"), "portal_access"),
        (Exception("Some completely unknown error"), "unknown_operation")
    ]
    
    print("=== User-Friendly Error Handler Demo ===\n")
    
    for error, context in error_scenarios:
        print(f"🔥 Original Error: {error}")
        print(f"📍 Context: {context}")
        print("─" * 50)
        
        friendly_error = handler.handle_error(error, context)
        formatted_message = handler.format_error_message(friendly_error, include_technical=True)
        
        print(formatted_message)
        print("=" * 80)
        print()

if __name__ == "__main__":
    demo_error_handling()
