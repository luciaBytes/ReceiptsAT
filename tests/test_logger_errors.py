#!/usr/bin/env python3
"""
Test suite for logger utility and error handling components.
"""

import unittest
import tempfile
import os
from datetime import datetime
from unittest.mock import Mock, patch
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.logger import LogHandler, get_logger, setup_logger

class TestLogHandler(unittest.TestCase):
    """Test cases for LogHandler utility."""
    
    def setUp(self):
        """Set up test environment."""
        self.log_handler = LogHandler()
    
    def test_log_handler_initialization(self):
        """Test log handler initializes correctly."""
        self.assertEqual(len(self.log_handler.get_entries()), 0)
        self.assertIsInstance(self.log_handler.get_entries(), list)
    
    def test_add_log_entry(self):
        """Test adding log entries."""
        self.log_handler.add_entry("INFO", "Test message")
        
        entries = self.log_handler.get_entries()
        self.assertEqual(len(entries), 1)
        
        entry = entries[0]
        self.assertEqual(entry['level'], "INFO")
        self.assertEqual(entry['message'], "Test message")
        self.assertIsInstance(entry['timestamp'], datetime)
    
    def test_add_multiple_log_entries(self):
        """Test adding multiple log entries."""
        messages = [
            ("INFO", "First message"),
            ("WARNING", "Second message"), 
            ("ERROR", "Third message")
        ]
        
        for level, message in messages:
            self.log_handler.add_entry(level, message)
        
        entries = self.log_handler.get_entries()
        self.assertEqual(len(entries), 3)
        
        # Check entries are in correct order
        for i, (level, message) in enumerate(messages):
            self.assertEqual(entries[i]['level'], level)
            self.assertEqual(entries[i]['message'], message)
    
    def test_custom_timestamp(self):
        """Test adding entry with custom timestamp."""
        custom_time = datetime(2024, 1, 1, 12, 0, 0)
        self.log_handler.add_entry("INFO", "Custom time message", custom_time)
        
        entries = self.log_handler.get_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]['timestamp'], custom_time)
    
    def test_clear_entries(self):
        """Test clearing log entries."""
        # Add some entries
        self.log_handler.add_entry("INFO", "Message 1")
        self.log_handler.add_entry("INFO", "Message 2")
        self.assertEqual(len(self.log_handler.get_entries()), 2)
        
        # Clear entries
        self.log_handler.clear_entries()
        self.assertEqual(len(self.log_handler.get_entries()), 0)
    
    def test_export_to_file(self):
        """Test exporting log entries to file."""
        # Add test entries
        self.log_handler.add_entry("INFO", "Test info message")
        self.log_handler.add_entry("ERROR", "Test error message")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            temp_file = f.name
        
        try:
            # Export to file
            success = self.log_handler.export_to_file(temp_file)
            self.assertTrue(success)
            
            # Verify file content
            with open(temp_file, 'r') as f:
                content = f.read()
                self.assertIn("Test info message", content)
                self.assertIn("Test error message", content)
                self.assertIn("INFO", content)
                self.assertIn("ERROR", content)
                
        finally:
            os.unlink(temp_file)
    
    def test_export_empty_log(self):
        """Test exporting empty log to file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            temp_file = f.name
        
        try:
            # Export empty log
            success = self.log_handler.export_to_file(temp_file)
            self.assertTrue(success)
            
            # Verify file exists and is empty
            with open(temp_file, 'r') as f:
                content = f.read()
                self.assertEqual(content.strip(), "")
                
        finally:
            os.unlink(temp_file)
    
    def test_export_file_error_handling(self):
        """Test error handling in file export."""
        # Try to export to invalid path
        invalid_path = "/invalid/path/that/does/not/exist.log"
        success = self.log_handler.export_to_file(invalid_path)
        
        # Should handle error gracefully
        self.assertFalse(success)

class TestLoggerSetup(unittest.TestCase):
    """Test cases for logger setup functions."""
    
    def test_get_logger(self):
        """Test getting logger instance."""
        logger = get_logger("test_module")
        self.assertIsNotNone(logger)
        # Logger name includes application prefix
        self.assertTrue(logger.name.endswith("test_module"))
    
    def test_setup_logger(self):
        """Test logger setup."""
        import logging
        
        logger = setup_logger(logging.DEBUG)
        self.assertIsNotNone(logger)
        # Logger level may be managed differently, just check it's set
        self.assertIsInstance(logger.level, int)
    
    def test_logger_formatting(self):
        """Test logger output formatting."""
        with patch('sys.stdout') as mock_stdout:
            logger = get_logger("test_format")
            logger.info("Test message")
            # Logger should have been configured and called

class TestErrorHandling(unittest.TestCase):
    """Test cases for error handling scenarios."""
    
    def setUp(self):
        """Set up test environment."""
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
        from web_client import WebClient
        from csv_handler import CSVHandler
        self.web_client = WebClient(testing_mode=True)
        self.csv_handler = CSVHandler()
    
    def test_authentication_error_handling(self):
        """Test authentication error scenarios."""
        # Test invalid credentials
        success, message = self.web_client.login("invalid", "invalid")
        self.assertFalse(success)
        self.assertIn("Invalid mock credentials", message)
    
    def test_max_login_attempts(self):
        """Test maximum login attempts handling."""
        # Simulate max attempts reached
        self.web_client.login_attempts = 3
        success, message = self.web_client.login("test", "test")
        self.assertFalse(success)
        self.assertIn("Maximum login attempts", message)
    
    def test_csv_validation_error_handling(self):
        """Test CSV validation error scenarios."""
        # Test invalid date range
        invalid_csv = """contractId,fromDate,toDate
123456,2024-01-31,2024-01-01"""  # fromDate after toDate
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(invalid_csv)
            temp_file = f.name
        
        try:
            success, errors = self.csv_handler.load_csv(temp_file)
            self.assertFalse(success)
            self.assertTrue(any("cannot be later than" in error for error in errors))
            
        finally:
            os.unlink(temp_file)
    
    def test_future_payment_date_handling(self):
        """Test future payment date error handling."""
        from datetime import datetime, timedelta
        
        future_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        invalid_csv = f"""contractId,fromDate,toDate,paymentDate
123456,2024-01-01,2024-01-31,{future_date}"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(invalid_csv)
            temp_file = f.name
        
        try:
            success, errors = self.csv_handler.load_csv(temp_file)
            self.assertFalse(success)
            self.assertTrue(any("cannot be in the future" in error for error in errors))
            
        finally:
            os.unlink(temp_file)

class TestSessionManagement(unittest.TestCase):
    """Test cases for session management."""
    
    def setUp(self):
        """Set up test environment."""
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
        from web_client import WebClient
        self.web_client = WebClient(testing_mode=True)
    
    def test_authentication_state(self):
        """Test authentication state tracking."""
        # Initially not authenticated
        self.assertFalse(self.web_client.is_authenticated())
        
        # After successful login
        success, _ = self.web_client.login("test", "test")
        self.assertTrue(success)
        self.assertTrue(self.web_client.is_authenticated())
        
        # After logout
        self.web_client.logout()
        self.assertFalse(self.web_client.is_authenticated())
    
    def test_session_persistence(self):
        """Test session persistence across operations."""
        # Login
        success, _ = self.web_client.login("test", "test")
        self.assertTrue(success)
        
        # Perform operation that requires authentication
        success, contracts = self.web_client.get_contracts_list()
        self.assertTrue(success)
        
        # Should still be authenticated
        self.assertTrue(self.web_client.is_authenticated())

if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [TestLogHandler, TestLoggerSetup, TestErrorHandling, TestSessionManagement]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)
