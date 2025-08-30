"""
Test suite for the receipts application.
"""

import unittest
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import API monitor tests
from test_api_monitor import (
    TestPageSnapshot,
    TestChangeDetection, 
    TestMonitoringConfig,
    TestPortalAPIMonitor
)
from test_api_monitor_dialog import (
    TestAPIMonitorDialog,
    TestAPIMonitorDialogMocked
)

from csv_handler import CSVHandler, ReceiptData
from web_client import WebClient
from receipt_processor import ReceiptProcessor, ProcessingResult

class TestCSVHandler(unittest.TestCase):
    """Test cases for CSV handler."""
    
    def setUp(self):
        self.csv_handler = CSVHandler()
    
    def test_load_valid_csv(self):
        """Test loading a valid CSV file."""
        # Create a temporary CSV file
        csv_content = """contractId,fromDate,toDate,receiptType,value,paymentDate
123456,2024-01-01,2024-01-31,rent,100.00,2024-01-28
789012,2024-02-01,2024-02-29,rent,900.50,2024-02-28"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_file = f.name
        
        try:
            success, errors = self.csv_handler.load_csv(temp_file)
            self.assertTrue(success)
            self.assertEqual(len(errors), 0)
            
            receipts = self.csv_handler.get_receipts()
            self.assertEqual(len(receipts), 2)
            
            # Check first receipt
            receipt1 = receipts[0]
            self.assertEqual(receipt1.contract_id, "123456")
            self.assertEqual(receipt1.from_date, "2024-01-01")
            self.assertEqual(receipt1.to_date, "2024-01-31")
            self.assertEqual(receipt1.value, 100.00)
            
        finally:
            os.unlink(temp_file)
    
    def test_load_invalid_csv_missing_columns(self):
        """Test loading CSV with missing required columns."""
        csv_content = """contractId,fromDate
123456,2024-01-01"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_file = f.name
        
        try:
            success, errors = self.csv_handler.load_csv(temp_file)
            self.assertFalse(success)
            self.assertIn("Missing required column", str(errors))
            
        finally:
            os.unlink(temp_file)
    
    def test_validate_date_range(self):
        """Test date validation."""
        csv_content = """contractId,fromDate,toDate,receiptType,value,paymentDate
123456,2024-01-31,2024-01-01,rent,100.00,2024-01-28"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_file = f.name
        
        try:
            success, errors = self.csv_handler.load_csv(temp_file)
            self.assertFalse(success)
            self.assertTrue(any("cannot be later than" in error for error in errors))
            
        finally:
            os.unlink(temp_file)
    
    def test_validate_payment_date_future(self):
        """Test payment date cannot be in the future."""
        from datetime import datetime, timedelta
        future_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        csv_content = f"""contractId,fromDate,toDate,receiptType,value,paymentDate
123456,2024-01-01,2024-01-31,rent,100.00,{future_date}"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_file = f.name
        
        try:
            success, errors = self.csv_handler.load_csv(temp_file)
            self.assertFalse(success)
            self.assertTrue(any("cannot be in the future" in error for error in errors))
            
        finally:
            os.unlink(temp_file)
    
    def test_payment_date_flexibility(self):
        """Test that payment date can be before or after receipt period."""
        csv_content = """contractId,fromDate,toDate,receiptType,value,paymentDate
123456,2024-02-01,2024-02-29,rent,100.00,2024-01-15
789012,2024-02-01,2024-02-29,rent,900.50,2024-03-15"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_file = f.name
        
        try:
            success, errors = self.csv_handler.load_csv(temp_file)
            self.assertTrue(success, f"Should allow payment dates before/after receipt period. Errors: {errors}")
            receipts = self.csv_handler.get_receipts()
            self.assertEqual(len(receipts), 2)
            
        finally:
            os.unlink(temp_file)
    
    def test_export_report(self):
        """Test report export functionality."""
        report_data = [
            {'Contract ID': '123456', 'Status': 'Success', 'Value': 100.00},
            {'Contract ID': '789012', 'Status': 'Failed', 'Value': 900.50}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_file = f.name
        
        try:
            success = self.csv_handler.export_report(report_data, temp_file)
            self.assertTrue(success)
            
            # Verify file content
            with open(temp_file, 'r') as f:
                content = f.read()
                self.assertIn('Contract ID', content)
                self.assertIn('123456', content)
                self.assertIn('Success', content)
                
        finally:
            os.unlink(temp_file)

class TestWebClient(unittest.TestCase):
    """Test cases for web client."""
    
    def setUp(self):
        self.web_client = WebClient(testing_mode=True)
    
    def test_login_success(self):
        """Test successful login."""
        success, message = self.web_client.login("test", "test")
        self.assertTrue(success)
        self.assertEqual(message, "Mock login successful")
        self.assertTrue(self.web_client.is_authenticated())
    
    def test_login_failure(self):
        """Test failed login with invalid credentials."""
        success, message = self.web_client.login("invalid", "invalid")
        self.assertFalse(success)
        self.assertIn("Invalid mock credentials", message)
        self.assertFalse(self.web_client.is_authenticated())
    
    def test_testing_mode_connection(self):
        """Test that testing mode provides mock connection."""
        success, message = self.web_client.test_connection()
        self.assertTrue(success)
        self.assertEqual(message, "Mock connection successful")
    
    def test_login_max_attempts(self):
        """Test maximum login attempts."""
        # Simulate failed logins
        self.web_client.authenticated = False
        self.web_client.login_attempts = 3
        
        success, message = self.web_client.login("testuser", "testpass")
        self.assertFalse(success)
        self.assertIn("Maximum login attempts", message)
    
    def test_logout(self):
        """Test logout functionality."""
        self.web_client.authenticated = True
        self.web_client.logout()
        self.assertFalse(self.web_client.is_authenticated())
    
    def test_test_connection_mock(self):
        """Test connection testing in mock mode."""
        success, message = self.web_client.test_connection()
        self.assertTrue(success)
        self.assertEqual(message, "Mock connection successful")
    
    def test_get_contracts_list_mock(self):
        """Test getting contracts list in mock mode."""
        # First login to authenticate
        self.web_client.login("test", "test")
        
        success, contracts = self.web_client.get_contracts_list()
        self.assertTrue(success)
        self.assertIsInstance(contracts, list)
        self.assertGreater(len(contracts), 0)
        # Check that contracts have expected structure
        if contracts:
            self.assertIn('contractId', contracts[0])
            self.assertIn('property', contracts[0])
    
    def test_submit_receipt_mock(self):
        """Test receipt submission in mock mode."""
        # First login to authenticate
        self.web_client.login("test", "test")
        
        mock_receipt = {
            "contractId": "123456",
            "fromDate": "2024-01-01",
            "toDate": "2024-01-31",
            "value": "100.00"
        }
        
        success, message = self.web_client.submit_receipt(mock_receipt)
        self.assertTrue(success)
        self.assertIn("Mock receipt submitted", message)
    
class TestReceiptProcessor(unittest.TestCase):
    """Test cases for receipt processor."""
    
    def setUp(self):
        self.mock_web_client = Mock(spec=WebClient)
        # Mock the validate_csv_contracts method to return a proper dict
        self.mock_web_client.validate_csv_contracts.return_value = {
            'success': True,
            'message': 'Mock validation successful',
            'portal_contracts_count': 2,
            'csv_contracts_count': 2,
            'portal_contracts': ['123456', '789012'],
            'portal_contracts_data': [],
            'csv_contracts': ['123456', '789012'],
            'valid_contracts': ['123456', '789012'],
            'valid_contracts_data': [],
            'invalid_contracts': [],
            'missing_from_csv': [],
            'missing_from_csv_data': [],
            'missing_from_portal': [],
            'validation_errors': []
        }
        self.processor = ReceiptProcessor(self.mock_web_client)
    
    def test_dry_run_mode(self):
        """Test dry run mode."""
        self.processor.set_dry_run(True)
        
        receipt = ReceiptData(
            contract_id="123456",
            from_date="2024-01-01",
            to_date="2024-01-31",
            receipt_type="rent",
            value=100.00,
            payment_date="2024-01-28"
        )
        
        result = self.processor._process_single_receipt(receipt)
        self.assertTrue(result.success)
        self.assertEqual(result.receipt_number, "DRY-RUN-001")
        self.assertEqual(result.contract_id, "123456")
    
    def test_process_receipts_bulk(self):
        """Test bulk processing."""
        self.processor.set_dry_run(True)
        
        receipts = [
            ReceiptData("123456", "2024-01-01", "2024-01-31", "rent", 100.00, "2024-01-28"),
            ReceiptData("789012", "2024-02-01", "2024-02-29", "rent", 900.50, "2024-02-28")
        ]
        
        results = self.processor.process_receipts_bulk(receipts)
        self.assertEqual(len(results), 2)
        self.assertTrue(all(r.success for r in results))
    
    def test_generate_report_data(self):
        """Test report data generation."""
        self.processor.results = [
            ProcessingResult(
                contract_id="123456",
                tenant_name="Test Tenant",
                success=True,
                receipt_number="R001",
                from_date="2024-01-01",
                to_date="2024-01-31",
                value=100.00
            )
        ]
        
        report_data = self.processor.generate_report_data()
        self.assertEqual(len(report_data), 1)
        
        report_item = report_data[0]
        self.assertEqual(report_item['Contract ID'], "123456")
        self.assertEqual(report_item['Status'], "Success")
        self.assertEqual(report_item['Receipt Number'], "R001")

class TestIntegration(unittest.TestCase):
    """Integration tests (with mocked web requests)."""
    
    def test_end_to_end_dry_run(self):
        """Test complete end-to-end flow in dry run mode."""
        # Create CSV data
        csv_content = """contractId,fromDate,toDate,receiptType,value,paymentDate
123456,2024-01-01,2024-01-31,rent,100.00,2024-01-28
789012,2024-02-01,2024-02-29,rent,900.50,2024-02-28"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            csv_file = f.name
        
        try:
            # Load CSV
            csv_handler = CSVHandler()
            success, errors = csv_handler.load_csv(csv_file)
            self.assertTrue(success)
            
            receipts = csv_handler.get_receipts()
            self.assertEqual(len(receipts), 2)
            
            # Process in dry run mode with testing mode WebClient
            web_client = WebClient(testing_mode=True)
            
            # Mock the contract validation to avoid authentication issues
            mock_validation_report = {
                'success': True,
                'message': 'Mock validation successful',
                'portal_contracts_count': 2,
                'csv_contracts_count': 2,
                'portal_contracts': ['123456', '789012'],
                'portal_contracts_data': [],
                'csv_contracts': ['123456', '789012'],
                'valid_contracts': ['123456', '789012'],
                'valid_contracts_data': [],
                'invalid_contracts': [],
                'missing_from_csv': [],
                'missing_from_csv_data': [],
                'missing_from_portal': [],
                'validation_errors': []
            }
            web_client.validate_csv_contracts = Mock(return_value=mock_validation_report)
            
            processor = ReceiptProcessor(web_client)
            processor.set_dry_run(True)
            
            results = processor.process_receipts_bulk(receipts)
            self.assertEqual(len(results), 2)
            self.assertTrue(all(r.success for r in results))
            
            # Generate and export report
            report_data = processor.generate_report_data()
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                report_file = f.name
            
            success = csv_handler.export_report(report_data, report_file)
            self.assertTrue(success)
            
            # Verify report content
            with open(report_file, 'r') as f:
                content = f.read()
                self.assertIn('Contract ID', content)
                self.assertIn('123456', content)
                self.assertIn('Success', content)
            
            os.unlink(report_file)
            
        finally:
            os.unlink(csv_file)

if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes including API Monitor tests
    test_classes = [
        TestCSVHandler, 
        TestWebClient, 
        TestReceiptProcessor, 
        TestIntegration,
        # API Monitor test classes
        TestPageSnapshot,
        TestChangeDetection,
        TestMonitoringConfig,
        TestPortalAPIMonitor,
        TestAPIMonitorDialog,
        TestAPIMonitorDialogMocked
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)
