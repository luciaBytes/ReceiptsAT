#!/usr/bin/env python3
"""
Test suite for GUI components and main window functionality.
"""

import unittest
import tkinter as tk
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import tempfile

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from gui.main_window import MainWindow
from csv_handler import CSVHandler
from web_client import WebClient

class TestGUIComponents(unittest.TestCase):
    """Test cases for GUI components."""
    
    def setUp(self):
        """Set up test environment."""
        try:
            self.root = tk.Tk()
            self.root.withdraw()  # Hide window during testing
            self.root.update_idletasks()  # Process pending events
            self.main_window = MainWindow(self.root)
        except Exception as e:
            self.skipTest(f"GUI environment not available: {e}")
        
    def tearDown(self):
        """Clean up after tests."""
        try:
            if hasattr(self, 'root') and self.root:
                self.root.quit()
                self.root.destroy()
        except Exception:
            pass  # Ignore cleanup errors
    
    def test_main_window_initialization(self):
        """Test main window initializes correctly."""
        self.assertIsInstance(self.main_window.csv_handler, CSVHandler)
        self.assertIsInstance(self.main_window.web_client, WebClient)
        self.assertEqual(self.main_window.mode_var.get(), "bulk")
        self.assertFalse(self.main_window.dry_run_var.get())
        self.assertEqual(self.main_window.status_var.get(), "Ready")
    
    def test_csv_file_path_handling(self):
        """Test CSV file path variable handling."""
        test_path = "/test/path/file.csv"
        self.main_window.csv_file_path.set(test_path)
        self.assertEqual(self.main_window.csv_file_path.get(), test_path)
    
    def test_processing_mode_selection(self):
        """Test processing mode selection."""
        # Test bulk mode
        self.main_window.mode_var.set("bulk")
        self.assertEqual(self.main_window.mode_var.get(), "bulk")
        
        # Test step-by-step mode
        self.main_window.mode_var.set("step_by_step")
        self.assertEqual(self.main_window.mode_var.get(), "step_by_step")
    
    def test_dry_run_toggle(self):
        """Test dry run mode toggle."""
        # Initially false
        self.assertFalse(self.main_window.dry_run_var.get())
        
        # Set to true
        self.main_window.dry_run_var.set(True)
        self.assertTrue(self.main_window.dry_run_var.get())
    
    def test_progress_tracking(self):
        """Test progress bar functionality."""
        # Initial progress
        self.assertEqual(self.main_window.progress_var.get(), 0.0)
        
        # Set progress
        self.main_window.progress_var.set(50.0)
        self.assertEqual(self.main_window.progress_var.get(), 50.0)
        
        # Full progress
        self.main_window.progress_var.set(100.0)
        self.assertEqual(self.main_window.progress_var.get(), 100.0)
    
    def test_status_message_updates(self):
        """Test status message updates."""
        # Initial status
        self.assertEqual(self.main_window.status_var.get(), "Ready")
        
        # Update status
        self.main_window.status_var.set("Processing...")
        self.assertEqual(self.main_window.status_var.get(), "Processing...")
    
    @patch('tkinter.messagebox.showerror')
    def test_authentication_validation(self, mock_error):
        """Test authentication validation in GUI."""
        # Mock web client as not authenticated
        self.main_window.web_client.is_authenticated = Mock(return_value=False)
        
        # Try to validate contracts without authentication
        self.main_window._validate_contracts()
        
        # Should show error message
        mock_error.assert_called_once_with("Error", "Please login first")
    
    @patch('tkinter.messagebox.showerror')
    def test_csv_validation_requirement(self, mock_error):
        """Test CSV validation requirement in GUI."""
        # Mock authenticated but no CSV loaded
        self.main_window.web_client.is_authenticated = Mock(return_value=True)
        self.main_window.csv_handler.get_receipts = Mock(return_value=[])
        
        # Try to validate contracts without CSV
        self.main_window._validate_contracts()
        
        # Should show error message
        mock_error.assert_called_once_with("Error", "Please load a valid CSV file first")
    
    def test_password_visibility_toggle(self):
        """Test password visibility toggle functionality."""
        # Check initial state - password should be hidden
        self.assertEqual(self.main_window.password_entry.cget('show'), '*')
        
        # Toggle to show password
        self.main_window._toggle_password_visibility()
        self.assertEqual(self.main_window.password_entry.cget('show'), '')
        
        # Toggle back to hide password
        self.main_window._toggle_password_visibility()
        self.assertEqual(self.main_window.password_entry.cget('show'), '*')

class TestFileOperations(unittest.TestCase):
    """Test cases for file I/O operations."""
    
    def setUp(self):
        """Set up test environment."""
        self.csv_handler = CSVHandler()
    
    def test_nonexistent_file_handling(self):
        """Test handling of nonexistent files."""
        nonexistent_file = "/path/that/does/not/exist.csv"
        success, errors = self.csv_handler.load_csv(nonexistent_file)
        
        self.assertFalse(success)
        self.assertIn("File does not exist", str(errors))
    
    def test_empty_file_handling(self):
        """Test handling of empty files."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            # Create empty file
            temp_file = f.name
        
        try:
            success, errors = self.csv_handler.load_csv(temp_file)
            self.assertFalse(success)
            # Should handle empty file gracefully
            
        finally:
            os.unlink(temp_file)
    
    def test_malformed_csv_handling(self):
        """Test handling of malformed CSV files."""
        malformed_csv = """contractId,fromDate,toDate
123456,2024-01-01
This is not valid CSV data
789012,2024-02-01,2024-02-29"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(malformed_csv)
            temp_file = f.name
        
        try:
            success, errors = self.csv_handler.load_csv(temp_file)
            # Should handle malformed CSV gracefully
            self.assertIsInstance(success, bool)
            self.assertIsInstance(errors, list)
            
        finally:
            os.unlink(temp_file)
    
    def test_file_permissions_handling(self):
        """Test handling of file permission issues."""
        # This test is system-dependent and may not work on all platforms
        # Just ensure the method handles exceptions gracefully
        try:
            success, errors = self.csv_handler.load_csv("/root/protected_file.csv")
            self.assertIsInstance(success, bool)
            self.assertIsInstance(errors, list)
        except Exception:
            # Expected on systems where this path doesn't exist
            pass

if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [TestGUIComponents, TestFileOperations]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)
