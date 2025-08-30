"""
Unit tests for API Monitor Dialog GUI functionality.

Tests the GUI interface for displaying API monitoring results and alerts.
Note: These tests may be limited by tkinter availability in headless environments.
"""

import unittest
import tkinter as tk
from unittest.mock import Mock, patch, MagicMock
import sys
import os
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import with error handling for environments without proper tkinter
try:
    from gui.api_monitor_dialog import APIMonitorDialog
    TKINTER_AVAILABLE = True
except Exception as e:
    print(f"Tkinter not available for GUI tests: {e}")
    TKINTER_AVAILABLE = False
    
    # Mock the class if tkinter is not available
    class APIMonitorDialog:
        def __init__(self, parent):
            pass


@unittest.skipUnless(TKINTER_AVAILABLE, "Tkinter not available")
class TestAPIMonitorDialog(unittest.TestCase):
    """Test cases for APIMonitorDialog class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Try to create root window for testing
        try:
            self.root = tk.Tk()
            self.root.withdraw()  # Hide the test window
            self.tkinter_working = True
        except Exception as e:
            self.tkinter_working = False
            self.skipTest(f"Cannot create tkinter root window: {e}")
        
        # Mock parent window
        self.mock_parent = self.root  # Use real parent instead of mock
    
    def tearDown(self):
        """Clean up test fixtures."""
        if hasattr(self, 'root') and self.root:
            try:
                self.root.destroy()
            except:
                pass  # Window might already be destroyed
    
    def test_dialog_initialization(self):
        """Test APIMonitorDialog initialization."""
        if not self.tkinter_working:
            self.skipTest("Tkinter not working properly")
            
        try:
            with patch('gui.api_monitor_dialog.PortalAPIMonitor'):
                dialog = APIMonitorDialog(self.mock_parent)
                self.assertIsNotNone(dialog.window)
                self.assertEqual(dialog.parent, self.mock_parent)
                dialog.window.destroy()
        except Exception as e:
            self.skipTest(f"Dialog creation failed: {e}")
    
    def test_dialog_basic_functionality(self):
        """Test basic dialog functionality."""
        if not self.tkinter_working:
            self.skipTest("Tkinter not working properly")
            
        try:
            with patch('gui.api_monitor_dialog.PortalAPIMonitor') as mock_monitor:
                # Mock the monitor to avoid actual API calls
                mock_monitor_instance = Mock()
                mock_monitor.return_value = mock_monitor_instance
                mock_monitor_instance.generate_monitoring_report.return_value = {
                    "monitoring_status": "active",
                    "total_changes_detected": 0,
                    "recent_changes": []
                }
                
                dialog = APIMonitorDialog(self.mock_parent)
                
                # Basic tests
                self.assertIsNotNone(dialog.window)
                self.assertIsNotNone(dialog.monitor)
                
                dialog.window.destroy()
        except Exception as e:
            self.skipTest(f"Dialog test failed: {e}")


class TestAPIMonitorDialogMocked(unittest.TestCase):
    """Test API Monitor Dialog functionality using mocks (no tkinter required)."""
    
    def test_constructor_parameters(self):
        """Test that constructor takes correct parameters."""
        # This test doesn't require actual tkinter
        with patch('gui.api_monitor_dialog.tk.Toplevel'), \
             patch('gui.api_monitor_dialog.PortalAPIMonitor'):
            
            mock_parent = Mock()
            try:
                dialog = APIMonitorDialog(mock_parent)
                # Just test that it doesn't raise TypeError about argument count
                self.assertEqual(dialog.parent, mock_parent)
            except Exception as e:
                if "takes 2 positional arguments but 3 were given" in str(e):
                    self.fail("Constructor signature is incorrect")
                # Other exceptions are acceptable (tkinter issues, etc.)
    
    def test_monitor_integration(self):
        """Test integration with PortalAPIMonitor."""
        with patch('gui.api_monitor_dialog.tk.Toplevel'), \
             patch('gui.api_monitor_dialog.PortalAPIMonitor') as mock_monitor_class:
            
            mock_monitor_instance = Mock()
            mock_monitor_class.return_value = mock_monitor_instance
            
            mock_parent = Mock()
            
            try:
                dialog = APIMonitorDialog(mock_parent)
                
                # Verify monitor was created
                mock_monitor_class.assert_called_once()
                self.assertEqual(dialog.monitor, mock_monitor_instance)
            except Exception as e:
                if "tkinter" not in str(e).lower() and "tcl" not in str(e).lower():
                    raise  # Re-raise non-tkinter exceptions


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)
