#!/usr/bin/env python3
"""
Test script to verify API monitor functionality is working.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_api_monitor_imports():
    """Test that API monitor imports work correctly."""
    print("Testing API Monitor imports...")
    
    try:
        from gui.api_monitor_dialog import show_api_monitor_dialog
        print("✅ Successfully imported show_api_monitor_dialog")
    except ImportError as e:
        print(f"❌ Failed to import show_api_monitor_dialog: {e}")
        assert False, f"Failed to import show_api_monitor_dialog: {e}"
    
    try:
        from utils.api_monitor import PortalAPIMonitor, ChangeDetection
        print("✅ Successfully imported PortalAPIMonitor and ChangeDetection")
    except ImportError as e:
        print(f"❌ Failed to import API monitor utilities: {e}")
        assert False, f"Failed to import API monitor utilities: {e}"
    
    try:
        # Test basic instantiation
        monitor = PortalAPIMonitor()
        print("✅ Successfully created PortalAPIMonitor instance")
    except Exception as e:
        print(f"❌ Failed to create PortalAPIMonitor instance: {e}")
        assert False, f"Failed to create PortalAPIMonitor instance: {e}"
    
    print("✅ All API monitor imports and basic functionality working!")

if __name__ == "__main__":
    success = test_api_monitor_imports()
    sys.exit(0 if success else 1)
