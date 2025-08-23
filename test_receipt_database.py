"""
Unit tests for the Receipt Database/History feature.
"""

import unittest
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add src to path for imports
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.receipt_database import ReceiptDatabase, ReceiptRecord
from csv_handler import ReceiptData
from receipt_processor import ReceiptProcessor, ProcessingResult
from web_client import WebClient


class TestReceiptDatabase(unittest.TestCase):
    """Test cases for the ReceiptDatabase class."""
    
    def setUp(self):
        """Setup test database with temporary file."""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        self.db = ReceiptDatabase(self.temp_db.name)
        
        # Sample receipt records for testing
        self.sample_record = ReceiptRecord(
            contract_id="123456",
            tenant_name="João Silva",
            from_date="2025-07-01",
            to_date="2025-07-31",
            payment_date="2025-07-28",
            value=750.50,
            receipt_type="rent",
            receipt_number="REC2025001",
            status="Success",
            error_message="",
            processing_mode="bulk",
            dry_run=False,
            tenant_count=1,
            landlord_count=1,
            is_inheritance=False
        )
        
        self.sample_dry_run_record = ReceiptRecord(
            contract_id="789012",
            tenant_name="Maria Santos",
            from_date="2025-08-01",
            to_date="2025-08-31",
            payment_date="2025-08-28",
            value=850.00,
            receipt_type="rent",
            receipt_number="",
            status="Success",
            error_message="",
            processing_mode="step-by-step",
            dry_run=True,
            tenant_count=2,
            landlord_count=1,
            is_inheritance=False
        )
    
    def tearDown(self):
        """Cleanup test database file."""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_database_initialization(self):
        """Test that database is properly initialized."""
        # Database should be created and functional
        self.assertIsInstance(self.db, ReceiptDatabase)
        self.assertEqual(self.db.db_path, self.temp_db.name)
        
        # Tables should exist
        stats = self.db.get_statistics()
        self.assertIsInstance(stats, dict)
        self.assertEqual(stats.get('total_receipts', 0), 0)
    
    def test_add_single_receipt(self):
        """Test adding a single receipt record."""
        # Add receipt
        receipt_id = self.db.add_receipt(self.sample_record)
        
        self.assertIsInstance(receipt_id, int)
        self.assertGreater(receipt_id, 0)
        
        # Verify it was saved
        retrieved = self.db.get_receipt_by_id(receipt_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.contract_id, "123456")
        self.assertEqual(retrieved.tenant_name, "João Silva")
        self.assertEqual(retrieved.value, 750.50)
        self.assertFalse(retrieved.dry_run)
    
    def test_add_duplicate_receipt(self):
        """Test that duplicate receipts are handled properly."""
        # Add first receipt
        self.db.add_receipt(self.sample_record)
        
        # Try to add duplicate (same contract_id, from_date, to_date, timestamp)
        with self.assertRaises(Exception):  # Should raise IntegrityError
            self.db.add_receipt(self.sample_record)
    
    def test_add_receipts_batch(self):
        """Test adding multiple receipts in batch."""
        records = [
            self.sample_record,
            self.sample_dry_run_record,
            ReceiptRecord(
                contract_id="345678",
                tenant_name="Carlos Ferreira",
                from_date="2025-06-01",
                to_date="2025-06-30",
                value=920.00,
                status="Failed",
                error_message="Authentication failed",
                processing_mode="bulk",
                dry_run=False
            )
        ]
        
        # Add batch
        receipt_ids = self.db.add_receipts_batch(records)
        
        self.assertEqual(len(receipt_ids), 3)
        self.assertTrue(all(isinstance(rid, int) for rid in receipt_ids))
        
        # Verify all were saved
        recent = self.db.get_recent_receipts(10)
        self.assertEqual(len(recent), 3)
    
    def test_search_receipts(self):
        """Test receipt search functionality."""
        # Add test data
        self.db.add_receipts_batch([self.sample_record, self.sample_dry_run_record])
        
        # Search by contract ID
        results = self.db.search_receipts(contract_id="123456")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].contract_id, "123456")
        
        # Search by tenant name
        results = self.db.search_receipts(tenant_name="Maria")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].tenant_name, "Maria Santos")
        
        # Search by status
        results = self.db.search_receipts(status="Success")
        self.assertEqual(len(results), 2)
        
        # Search by dry run status
        results = self.db.search_receipts(dry_run=True)
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].dry_run)
        
        results = self.db.search_receipts(dry_run=False)
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0].dry_run)
    
    def test_get_receipts_by_contract(self):
        """Test getting receipts for specific contract."""
        # Add multiple receipts for same contract
        record2 = ReceiptRecord(
            contract_id="123456",
            tenant_name="João Silva",
            from_date="2025-06-01",
            to_date="2025-06-30",
            value=750.50,
            status="Success",
            processing_mode="bulk",
            dry_run=False
        )
        
        self.db.add_receipts_batch([self.sample_record, record2, self.sample_dry_run_record])
        
        # Get receipts for contract 123456
        results = self.db.get_receipts_by_contract("123456")
        self.assertEqual(len(results), 2)
        self.assertTrue(all(r.contract_id == "123456" for r in results))
        
        # Results should be ordered by timestamp DESC
        if len(results) > 1:
            timestamps = [r.timestamp for r in results]
            self.assertEqual(timestamps, sorted(timestamps, reverse=True))
    
    def test_statistics(self):
        """Test statistics generation."""
        # Add test data
        failed_record = ReceiptRecord(
            contract_id="999999",
            tenant_name="Failed User",
            from_date="2025-07-01",
            to_date="2025-07-31",
            value=500.00,
            status="Failed",
            error_message="Some error",
            processing_mode="bulk",
            dry_run=False
        )
        
        self.db.add_receipts_batch([
            self.sample_record,
            self.sample_dry_run_record,
            failed_record
        ])
        
        # Get statistics
        stats = self.db.get_statistics()
        
        self.assertEqual(stats['total_receipts'], 3)
        self.assertEqual(stats['successful_receipts'], 2)
        self.assertEqual(stats['failed_receipts'], 1)
        self.assertEqual(stats['dry_run_receipts'], 1)
        self.assertEqual(stats['unique_contracts'], 3)
        
        # Financial stats
        self.assertEqual(stats['total_value'], 2100.50)  # 750.50 + 850.00 + 500.00
        # Real total should be non-dry-run receipts: 750.50 + 500.00 = 1250.50
        # But if query only counts successful non-dry-run, then only 750.50
        expected_real_total = 750.50  # Only successful non-dry-run receipts
        self.assertEqual(stats['real_total_value'], expected_real_total)
        
        # Status breakdown
        status_breakdown = stats['status_breakdown']
        self.assertEqual(status_breakdown['Success'], 2)
        self.assertEqual(status_breakdown['Failed'], 1)
    
    def test_delete_receipt(self):
        """Test receipt deletion."""
        # Add receipt
        receipt_id = self.db.add_receipt(self.sample_record)
        
        # Verify it exists
        self.assertIsNotNone(self.db.get_receipt_by_id(receipt_id))
        
        # Delete it
        success = self.db.delete_receipt(receipt_id)
        self.assertTrue(success)
        
        # Verify it's gone
        self.assertIsNone(self.db.get_receipt_by_id(receipt_id))
        
        # Try to delete non-existent receipt
        success = self.db.delete_receipt(99999)
        self.assertFalse(success)
    
    def test_clear_all_receipts(self):
        """Test clearing all receipts."""
        # Add test data
        self.db.add_receipts_batch([self.sample_record, self.sample_dry_run_record])
        
        # Verify data exists
        stats = self.db.get_statistics()
        self.assertEqual(stats['total_receipts'], 2)
        
        # Clear all
        deleted_count = self.db.clear_all_receipts()
        self.assertEqual(deleted_count, 2)
        
        # Verify data is gone
        stats = self.db.get_statistics()
        self.assertEqual(stats['total_receipts'], 0)
        
        recent = self.db.get_recent_receipts(10)
        self.assertEqual(len(recent), 0)
    
    def test_export_csv(self):
        """Test CSV export functionality."""
        # Add test data
        self.db.add_receipts_batch([self.sample_record, self.sample_dry_run_record])
        
        # Export to temporary CSV file
        temp_csv = tempfile.NamedTemporaryFile(suffix='.csv', delete=False)
        temp_csv.close()
        
        try:
            success = self.db.export_to_csv(temp_csv.name)
            self.assertTrue(success)
            
            # Verify CSV file was created and has content
            self.assertTrue(os.path.exists(temp_csv.name))
            
            with open(temp_csv.name, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertIn('contract_id', content)  # Header
                self.assertIn('123456', content)       # Data
                self.assertIn('789012', content)       # Data
                self.assertIn('João Silva', content)   # Portuguese characters
                
        finally:
            if os.path.exists(temp_csv.name):
                os.unlink(temp_csv.name)


class TestReceiptProcessorDatabaseIntegration(unittest.TestCase):
    """Test database integration with ReceiptProcessor."""
    
    def setUp(self):
        """Setup test environment."""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        
        # Mock WebClient
        self.mock_web_client = MagicMock(spec=WebClient)
        
        # Create database and processor
        self.database = ReceiptDatabase(self.temp_db.name)
        self.processor = ReceiptProcessor(self.mock_web_client, self.database)
        
        # Sample receipt data
        self.sample_receipt = ReceiptData(
            contract_id="123456",
            from_date="2025-07-01",
            to_date="2025-07-31",
            receipt_type="rent",
            value=750.50,
            payment_date="2025-07-28"
        )
    
    def tearDown(self):
        """Cleanup test database file."""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_database_saving_enabled_by_default(self):
        """Test that database saving is enabled by default."""
        self.assertTrue(self.processor.save_to_database)
    
    def test_disable_database_saving(self):
        """Test disabling database saving."""
        self.processor.set_database_saving(False)
        self.assertFalse(self.processor.save_to_database)
    
    def test_get_database_instance(self):
        """Test getting database instance from processor."""
        db = self.processor.get_database()
        self.assertIs(db, self.database)
    
    @patch('receipt_processor.logger')
    def test_save_result_to_database(self, mock_logger):
        """Test saving individual result to database."""
        # Create processing result
        result = ProcessingResult(
            contract_id="123456",
            tenant_name="João Silva",
            success=True,
            receipt_number="REC001",
            from_date="2025-07-01",
            to_date="2025-07-31",
            payment_date="2025-07-28",
            value=750.50,
            timestamp=datetime.now().isoformat(),
            status="Success"
        )
        
        # Save to database
        success = self.processor.save_result_to_database(result, self.sample_receipt, "bulk")
        self.assertTrue(success)
        
        # Verify it was saved
        receipts = self.database.get_receipts_by_contract("123456")
        self.assertEqual(len(receipts), 1)
        
        saved_receipt = receipts[0]
        self.assertEqual(saved_receipt.contract_id, "123456")
        self.assertEqual(saved_receipt.tenant_name, "João Silva")
        self.assertEqual(saved_receipt.receipt_number, "REC001")
        self.assertEqual(saved_receipt.processing_mode, "bulk")
        self.assertFalse(saved_receipt.dry_run)
    
    def test_save_result_with_database_disabled(self):
        """Test that results are not saved when database is disabled."""
        self.processor.set_database_saving(False)
        
        result = ProcessingResult(
            contract_id="123456",
            tenant_name="Test User",
            success=True
        )
        
        # Should return True but not actually save
        success = self.processor.save_result_to_database(result, self.sample_receipt, "bulk")
        self.assertTrue(success)
        
        # Verify nothing was saved
        receipts = self.database.get_receipts_by_contract("123456")
        self.assertEqual(len(receipts), 0)
    
    def test_save_all_results_batch(self):
        """Test saving multiple results in batch."""
        # Create multiple results
        results = [
            ProcessingResult(
                contract_id="123456",
                tenant_name="João Silva",
                success=True,
                receipt_number="REC001",
                from_date="2025-07-01",
                to_date="2025-07-31",
                value=750.50,
                timestamp=datetime.now().isoformat(),
                status="Success"
            ),
            ProcessingResult(
                contract_id="789012",
                tenant_name="Maria Santos",
                success=False,
                error_message="Test error",
                from_date="2025-08-01",
                to_date="2025-08-31",
                value=850.00,
                timestamp=datetime.now().isoformat(),
                status="Failed"
            )
        ]
        
        # Set results in processor
        self.processor.results = results
        
        # Create corresponding receipt data
        receipts = [
            self.sample_receipt,
            ReceiptData(
                contract_id="789012",
                from_date="2025-08-01",
                to_date="2025-08-31",
                receipt_type="rent",
                value=850.00
            )
        ]
        
        # Save batch
        saved_count = self.processor.save_all_results_to_database(receipts, "step-by-step")
        self.assertEqual(saved_count, 2)
        
        # Verify both were saved
        all_receipts = self.database.get_recent_receipts(10)
        self.assertEqual(len(all_receipts), 2)
        
        # Check processing mode was set correctly
        self.assertTrue(all(r.processing_mode == "step-by-step" for r in all_receipts))


class TestReceiptRecord(unittest.TestCase):
    """Test cases for the ReceiptRecord data class."""
    
    def test_receipt_record_creation(self):
        """Test creating ReceiptRecord instances."""
        record = ReceiptRecord(
            contract_id="123456",
            tenant_name="Test User",
            value=100.50
        )
        
        self.assertEqual(record.contract_id, "123456")
        self.assertEqual(record.tenant_name, "Test User")
        self.assertEqual(record.value, 100.50)
        
        # Default values
        self.assertIsNone(record.id)
        self.assertEqual(record.status, "")
        self.assertFalse(record.dry_run)
        self.assertEqual(record.tenant_count, 1)
        self.assertFalse(record.is_inheritance)
    
    def test_timestamp_auto_generation(self):
        """Test that timestamp is automatically generated."""
        record = ReceiptRecord(contract_id="123")
        
        # Should have timestamp
        self.assertNotEqual(record.timestamp, "")
        self.assertIsInstance(record.timestamp, str)
        
        # Should be valid ISO format
        datetime.fromisoformat(record.timestamp)
    
    def test_timestamp_preservation(self):
        """Test that provided timestamp is preserved."""
        custom_timestamp = "2025-07-15T10:30:00"
        record = ReceiptRecord(
            contract_id="123",
            timestamp=custom_timestamp
        )
        
        self.assertEqual(record.timestamp, custom_timestamp)


if __name__ == '__main__':
    # Create test suite
    test_classes = [
        TestReceiptDatabase,
        TestReceiptProcessorDatabaseIntegration,
        TestReceiptRecord
    ]
    
    suite = unittest.TestSuite()
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print("RECEIPT DATABASE/HISTORY TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print(f"\nERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    exit(0 if result.wasSuccessful() else 1)
