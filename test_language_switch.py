"""
Test script for language switching functionality
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.multilingual_localization import (
    get_text, 
    switch_language, 
    get_current_language,
    get_language_button_text
)

def test_language_switching():
    """Test the language switching functionality."""
    
    print("=== Language Switching Test ===")
    
    # Test initial state
    print(f"Initial language: {get_current_language()}")
    print(f"Language button shows: {get_language_button_text()}")
    print(f"Main window title: {get_text('MAIN_WINDOW_TITLE')}")
    print(f"Generate template button: {get_text('GENERATE_TEMPLATE_BUTTON')}")
    print(f"Login button: {get_text('LOGIN_BUTTON')}")
    print()
    
    # Switch language
    new_lang = switch_language()
    print(f"Switched to: {new_lang}")
    print(f"Language button shows: {get_language_button_text()}")
    print(f"Main window title: {get_text('MAIN_WINDOW_TITLE')}")
    print(f"Generate template button: {get_text('GENERATE_TEMPLATE_BUTTON')}")
    print(f"Login button: {get_text('LOGIN_BUTTON')}")
    print()
    
    # Switch back
    new_lang = switch_language()
    print(f"Switched back to: {new_lang}")
    print(f"Language button shows: {get_language_button_text()}")
    print(f"Main window title: {get_text('MAIN_WINDOW_TITLE')}")
    print(f"Generate template button: {get_text('GENERATE_TEMPLATE_BUTTON')}")
    print(f"Login button: {get_text('LOGIN_BUTTON')}")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_language_switching()
