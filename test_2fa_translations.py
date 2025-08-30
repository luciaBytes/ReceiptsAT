#!/usr/bin/env python3
"""
Test script to verify 2FA button translations are working correctly.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.multilingual_localization import get_text, set_language

def test_2fa_translations():
    """Test that all 2FA-related translations are working."""
    print("Testing 2FA Translations...")
    print("=" * 40)
    
    # Test both languages
    for lang in ['pt', 'en']:
        set_language(lang)
        print(f"\n{lang.upper()} Language:")
        print("-" * 20)
        
        # Test all 2FA-related keys
        test_keys = [
            'VERIFY_BUTTON',
            'TWO_FACTOR_TITLE', 
            'TWO_FACTOR_MESSAGE',
            'SMS_CODE_LABEL',
            'TWO_FACTOR_HELP',
            'ENTER_SMS_CODE_MESSAGE',
            'SMS_CODE_SIX_DIGITS_MESSAGE',
            'CANCEL_BUTTON'
        ]
        
        for key in test_keys:
            try:
                text = get_text(key)
                # Check if we're getting the key back (indicates missing translation)
                if text == key:
                    print(f"❌ {key}: MISSING - showing key instead of text")
                else:
                    print(f"✅ {key}: '{text}'")
            except Exception as e:
                print(f"❌ {key}: ERROR - {e}")
    
    print("\n" + "=" * 40)
    print("Test completed!")

if __name__ == "__main__":
    test_2fa_translations()
