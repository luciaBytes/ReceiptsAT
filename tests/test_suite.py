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
        csv_content = """contractId,fromDate,toDate,receiptType,value
123456,2024-01-01,2024-01-31,rent,850.00
789012,2024-02-01,2024-02-29,rent,900.50"""
        
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
            self.assertEqual(receipt1.value, 850.00)
            
        finally:
            os.unlink(temp_file)
    
    def test_load_invalid_csv_missing_columns(self):
        """Test loading CSV with missing required columns."""
        csv_content = """contractId,fromDate,toDate
123456,2024-01-01,2024-01-31"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_file = f.name
        
        try:
            success, errors = self.csv_handler.load_csv(temp_file)
            self.assertFalse(success)
            self.assertIn("Missing required columns", str(errors))
            
        finally:
            os.unlink(temp_file)
    
    def test_validate_date_range(self):
        """Test date validation."""
        csv_content = """contractId,fromDate,toDate,receiptType,value
123456,2024-01-31,2024-01-01,rent,850.00"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_file = f.name
        
        try:
            success, errors = self.csv_handler.load_csv(temp_file)
            self.assertFalse(success)
            self.assertTrue(any("cannot be later than" in error for error in errors))
            
        finally:
            os.unlink(temp_file)
    
    def test_export_report(self):
        """Test report export functionality."""
        report_data = [
            {'Contract ID': '123456', 'Status': 'Success', 'Value': 850.00},
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
        self.web_client = WebClient()
    
    def test_login_success(self):
        """Test successful login."""
        success, message = self.web_client.login("testuser", "testpass")
        # In our mock implementation, this should succeed
        self.assertTrue(success)
        self.assertEqual(message, "Login successful")
        self.assertTrue(self.web_client.is_authenticated())
    
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
        success = self.web_client.logout()
        self.assertTrue(success)
        self.assertFalse(self.web_client.is_authenticated())
    
    @patch('requests.Session.get')
    def test_test_connection(self, mock_get):
        """Test connection testing."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        success, message = self.web_client.test_connection()
        self.assertTrue(success)
        self.assertIn("successful", message)
    
    def test_extract_recibo_data(self):
        """Test recibo data extraction from HTML."""
        html_content = '''
        <html>
        <script>
        $scope.recibo = {"numContrato": 123456, "valor": 850.00};
        </script>
        </html>
        '''
        
        result = self.web_client._extract_recibo_data(html_content)
        self.assertIsNotNone(result)
        self.assertEqual(result.get('numContrato'), 123456)
        self.assertEqual(result.get('valor'), 850.00)

class TestReceiptProcessor(unittest.TestCase):
    """Test cases for receipt processor."""
    
    def setUp(self):
        self.mock_web_client = Mock(spec=WebClient)
        self.processor = ReceiptProcessor(self.mock_web_client)
    
    def test_dry_run_mode(self):
        """Test dry run mode."""
        self.processor.set_dry_run(True)
        
        receipt = ReceiptData(
            contract_id="123456",
            from_date="2024-01-01",
            to_date="2024-01-31",
            receipt_type="rent",
            value=850.00
        )
        
        result = self.processor._process_single_receipt(receipt)
        self.assertTrue(result.success)
        self.assertEqual(result.receipt_number, "DRY-RUN-001")
        self.assertEqual(result.contract_id, "123456")
    
    def test_process_receipts_bulk(self):
        """Test bulk processing."""
        self.processor.set_dry_run(True)
        
        receipts = [
            ReceiptData("123456", "2024-01-01", "2024-01-31", "rent", 850.00),
            ReceiptData("789012", "2024-02-01", "2024-02-29", "rent", 900.50)
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
                value=850.00
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
        csv_content = """contractId,fromDate,toDate,receiptType,value
123456,2024-01-01,2024-01-31,rent,850.00
789012,2024-02-01,2024-02-29,rent,900.50"""
        
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
            
            # Process in dry run mode
            web_client = WebClient()
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
    
    # Add test classes
    test_classes = [TestCSVHandler, TestWebClient, TestReceiptProcessor, TestIntegration]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)
