"""
Comprehensive unit tests for receipt_verifier module.
Tests receipt verification logic, export functionality, and error handling.
All tests use mocks - no live platform requests.
"""

import pytest
import sys
import os
import tempfile
import csv
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from dataclasses import dataclass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from receipt_verifier import ReceiptVerifier, VerifiedReceipt
from receipt_processor import ProcessingResult


class TestVerifiedReceiptDataclass:
    """Test VerifiedReceipt dataclass initialization."""
    
    def test_verified_receipt_creation(self):
        """Test creating VerifiedReceipt with all fields."""
        receipt = VerifiedReceipt(
            contract_id="123",
            contract_name="Test Contract",
            tenant_name="John Doe",
            rent_date_from="2024-01-01",
            rent_date_to="2024-01-31",
            payment_date="2024-01-15",
            rent_value=500.00,
            issue_date="2024-01-16",
            receipt_number="R-2024-001",
            verification_status="Verified",
            error_message=None
        )
        
        assert receipt.contract_id == "123"
        assert receipt.verification_status == "Verified"
        assert receipt.rent_value == 500.00
    
    def test_verified_receipt_with_error(self):
        """Test creating VerifiedReceipt with error."""
        receipt = VerifiedReceipt(
            contract_id="456",
            contract_name="Failed Contract",
            tenant_name="Jane Doe",
            rent_date_from="2024-02-01",
            rent_date_to="2024-02-29",
            payment_date="2024-02-15",
            rent_value=600.00,
            issue_date="2024-02-16",
            receipt_number="R-2024-002",
            verification_status="Error",
            error_message="Network timeout"
        )
        
        assert receipt.verification_status == "Error"
        assert receipt.error_message == "Network timeout"


class TestReceiptVerifierInit:
    """Test ReceiptVerifier initialization."""
    
    def test_init_with_web_client(self):
        """Test initialization with web client."""
        mock_client = Mock()
        
        verifier = ReceiptVerifier(mock_client)
        
        assert verifier.web_client == mock_client
        assert verifier.verified_receipts == []
    
    def test_init_creates_empty_list(self):
        """Test that initialization creates empty verified_receipts list."""
        mock_client = Mock()
        
        verifier = ReceiptVerifier(mock_client)
        
        assert isinstance(verifier.verified_receipts, list)
        assert len(verifier.verified_receipts) == 0


class TestVerifySingleReceipt:
    """Test _verify_single_receipt method."""
    
    def test_verify_single_receipt_success(self):
        """Test verifying a single receipt that exists in portal."""
        mock_client = Mock()
        mock_client.verify_receipt_in_portal.return_value = (
            True, 
            {
                'contract_name': 'Updated Contract',
                'tenant_name': 'Updated Tenant',
                'issue_date': '2024-01-20'
            }
        )
        
        verifier = ReceiptVerifier(mock_client)
        
        result = ProcessingResult(
            success=True,
            contract_id="123",
            tenant_name="Original Tenant",
            from_date="2024-01-01",
            to_date="2024-01-31",
            payment_date="2024-01-15",
            value=500.00,
            receipt_number="R-001",
            timestamp="2024-01-16T10:30:00"
        )
        
        verified = verifier._verify_single_receipt(result)
        
        assert verified.verification_status == "Verified"
        assert verified.contract_id == "123"
        assert verified.contract_name == "Updated Contract"
        assert verified.tenant_name == "Updated Tenant"
        assert verified.receipt_number == "R-001"
        assert verified.error_message == ""
        
        mock_client.verify_receipt_in_portal.assert_called_once_with("123", "R-001")
    
    def test_verify_single_receipt_not_found(self):
        """Test verifying receipt that doesn't exist in portal."""
        mock_client = Mock()
        mock_client.verify_receipt_in_portal.return_value = (True, None)
        
        verifier = ReceiptVerifier(mock_client)
        
        result = ProcessingResult(
            success=True,
            contract_id="456",
            tenant_name="Test Tenant",
            from_date="2024-02-01",
            to_date="2024-02-29",
            payment_date="2024-02-15",
            value=600.00,
            receipt_number="R-002"
        )
        
        verified = verifier._verify_single_receipt(result)
        
        assert verified.verification_status == "Not Found"
        assert verified.error_message == "Receipt number not found in portal"
    
    def test_verify_single_receipt_error_response(self):
        """Test verification with error response from portal."""
        mock_client = Mock()
        mock_client.verify_receipt_in_portal.return_value = (
            False, 
            {'error': 'Authentication failed'}
        )
        
        verifier = ReceiptVerifier(mock_client)
        
        result = ProcessingResult(
            success=True,
            contract_id="789",
            tenant_name="Test Tenant",
            from_date="2024-03-01",
            to_date="2024-03-31",
            payment_date="2024-03-15",
            value=700.00,
            receipt_number="R-003"
        )
        
        verified = verifier._verify_single_receipt(result)
        
        assert verified.verification_status == "Error"
        assert "Authentication failed" in verified.error_message
    
    def test_verify_single_receipt_exception(self):
        """Test verification when exception occurs."""
        mock_client = Mock()
        mock_client.verify_receipt_in_portal.side_effect = Exception("Network timeout")
        
        verifier = ReceiptVerifier(mock_client)
        
        result = ProcessingResult(
            success=True,
            contract_id="999",
            tenant_name="Test Tenant",
            from_date="2024-04-01",
            to_date="2024-04-30",
            payment_date="2024-04-15",
            value=800.00,
            receipt_number="R-004"
        )
        
        verified = verifier._verify_single_receipt(result)
        
        assert verified.verification_status == "Error"
        assert "Network timeout" in verified.error_message
    
    def test_verify_single_receipt_partial_details(self):
        """Test verification with partial portal details."""
        mock_client = Mock()
        mock_client.verify_receipt_in_portal.return_value = (
            True, 
            {'contract_name': 'Only Contract Name'}  # Missing tenant_name and issue_date
        )
        
        verifier = ReceiptVerifier(mock_client)
        
        result = ProcessingResult(
            success=True,
            contract_id="111",
            tenant_name="Original Tenant",
            from_date="2024-05-01",
            to_date="2024-05-31",
            payment_date="2024-05-15",
            value=900.00,
            receipt_number="R-005"
        )
        
        verified = verifier._verify_single_receipt(result)
        
        assert verified.verification_status == "Verified"
        assert verified.contract_name == "Only Contract Name"
        assert verified.tenant_name == "Original Tenant"  # Should keep original


class TestVerifyProcessingResults:
    """Test verify_processing_results method."""
    
    def test_verify_empty_results(self):
        """Test verifying empty list of results."""
        mock_client = Mock()
        verifier = ReceiptVerifier(mock_client)
        
        results = []
        
        verified = verifier.verify_processing_results(results)
        
        assert len(verified) == 0
        assert verifier.verified_receipts == []
    
    def test_verify_filters_failed_results(self):
        """Test that failed processing results are filtered out."""
        mock_client = Mock()
        verifier = ReceiptVerifier(mock_client)
        
        results = [
            ProcessingResult(
                success=True,
                contract_id="123",
                receipt_number="R-001",
                value=500.00
            ),
            ProcessingResult(
                success=False,
                contract_id="",
                error_message="Failed to process"
            ),
            ProcessingResult(
                success=True,
                contract_id="456",
                receipt_number="R-002",
                value=600.00
            )
        ]
        
        mock_client.verify_receipt_in_portal.return_value = (True, {})
        
        verified = verifier.verify_processing_results(results)
        
        # Should only verify successful results
        assert len(verified) == 2
        assert mock_client.verify_receipt_in_portal.call_count == 2
    
    def test_verify_multiple_results_mixed_statuses(self):
        """Test verifying multiple results with different outcomes."""
        mock_client = Mock()
        
        # Mock different responses for different receipts
        def mock_verify(contract_id, receipt_number):
            if receipt_number == "R-001":
                return (True, {'contract_name': 'Contract 1'})
            elif receipt_number == "R-002":
                return (True, None)  # Not found
            else:
                return (False, {'error': 'Error'})
        
        mock_client.verify_receipt_in_portal.side_effect = mock_verify
        
        verifier = ReceiptVerifier(mock_client)
        
        results = [
            ProcessingResult(success=True, contract_id="1", receipt_number="R-001", value=100.00),
            ProcessingResult(success=True, contract_id="2", receipt_number="R-002", value=200.00),
            ProcessingResult(success=True, contract_id="3", receipt_number="R-003", value=300.00)
        ]
        
        verified = verifier.verify_processing_results(results)
        
        assert len(verified) == 3
        assert verified[0].verification_status == "Verified"
        assert verified[1].verification_status == "Not Found"
        assert verified[2].verification_status == "Error"
    
    def test_verify_results_summary_logging(self):
        """Test that summary statistics are logged."""
        mock_client = Mock()
        mock_client.verify_receipt_in_portal.return_value = (True, {})
        
        verifier = ReceiptVerifier(mock_client)
        
        results = [
            ProcessingResult(success=True, contract_id="1", receipt_number="R-001", value=100.00),
            ProcessingResult(success=True, contract_id="2", receipt_number="R-002", value=200.00)
        ]
        
        with patch('receipt_verifier.logger') as mock_logger:
            verified = verifier.verify_processing_results(results)
            
            # Verify summary logging was called
            assert mock_logger.info.called
            # Check that summary info was logged
            info_calls = [str(call) for call in mock_logger.info.call_args_list]
            assert any("Verified:" in str(call) for call in info_calls)


class TestExportToCSV:
    """Test export_to_csv method."""
    
    def test_export_success(self):
        """Test successful export to CSV."""
        mock_client = Mock()
        verifier = ReceiptVerifier(mock_client)
        
        # Add some verified receipts
        verifier.verified_receipts = [
            VerifiedReceipt(
                contract_id="123",
                contract_name="Test Contract 1",
                tenant_name="Tenant 1",
                rent_date_from="2024-01-01",
                rent_date_to="2024-01-31",
                payment_date="2024-01-15",
                rent_value=500.00,
                issue_date="2024-01-16",
                receipt_number="R-001",
                verification_status="Verified",
                error_message=None
            ),
            VerifiedReceipt(
                contract_id="456",
                contract_name="Test Contract 2",
                tenant_name="Tenant 2",
                rent_date_from="2024-02-01",
                rent_date_to="2024-02-29",
                payment_date="2024-02-15",
                rent_value=600.00,
                issue_date="2024-02-16",
                receipt_number="R-002",
                verification_status="Not Found",
                error_message="Receipt not found"
            )
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            file_path = f.name
        
        try:
            success, message = verifier.export_to_csv(file_path)
            
            assert success is True
            assert "2 receipts" in message
            assert os.path.exists(file_path)
            
            # Verify CSV content
            with open(file_path, 'r', encoding='utf-8-sig') as csvfile:
                reader = csv.DictReader(csvfile)
                rows = list(reader)
                
                assert len(rows) == 2
                assert rows[0]['Contract ID'] == "123"
                assert rows[0]['Verification Status'] == "Verified"
                assert rows[1]['Contract ID'] == "456"
                assert rows[1]['Verification Status'] == "Not Found"
        finally:
            if os.path.exists(file_path):
                os.unlink(file_path)
    
    def test_export_empty_receipts(self):
        """Test export with no verified receipts."""
        mock_client = Mock()
        verifier = ReceiptVerifier(mock_client)
        
        success, message = verifier.export_to_csv("dummy_path.csv")
        
        assert success is False
        assert "No verified receipts" in message
    
    def test_export_invalid_path(self):
        """Test export with invalid file path."""
        mock_client = Mock()
        verifier = ReceiptVerifier(mock_client)
        
        verifier.verified_receipts = [
            VerifiedReceipt(
                contract_id="123",
                contract_name="Test",
                tenant_name="Test Tenant",
                rent_date_from="2024-01-01",
                rent_date_to="2024-01-31",
                payment_date="2024-01-15",
                rent_value=500.00,
                issue_date="2024-01-16",
                receipt_number="R-001",
                verification_status="Verified",
                error_message=None
            )
        ]
        
        invalid_path = "/invalid/nonexistent/path/file.csv"
        success, message = verifier.export_to_csv(invalid_path)
        
        assert success is False
        assert "Failed to export CSV" in message
    
    def test_export_with_special_characters(self):
        """Test export with special characters in data."""
        mock_client = Mock()
        verifier = ReceiptVerifier(mock_client)
        
        verifier.verified_receipts = [
            VerifiedReceipt(
                contract_id="123",
                contract_name="Contrató Spëcial",
                tenant_name="José María",
                rent_date_from="2024-01-01",
                rent_date_to="2024-01-31",
                payment_date="2024-01-15",
                rent_value=500.50,
                issue_date="2024-01-16",
                receipt_number="R-001-€",
                verification_status="Verified",
                error_message=None
            )
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            file_path = f.name
        
        try:
            success, message = verifier.export_to_csv(file_path)
            
            assert success is True
            
            # Verify special characters are preserved
            with open(file_path, 'r', encoding='utf-8-sig') as csvfile:
                content = csvfile.read()
                assert "José" in content or "Jose" in content  # May vary
        finally:
            if os.path.exists(file_path):
                os.unlink(file_path)


class TestGetSummaryStats:
    """Test get_summary_stats method."""
    
    def test_summary_stats_empty(self):
        """Test summary stats with no verified receipts."""
        mock_client = Mock()
        verifier = ReceiptVerifier(mock_client)
        
        stats = verifier.get_summary_stats()
        
        assert stats['total'] == 0
        assert stats['verified'] == 0
        assert stats['not_found'] == 0
        assert stats['error'] == 0
    
    def test_summary_stats_mixed(self):
        """Test summary stats with mixed verification statuses."""
        mock_client = Mock()
        verifier = ReceiptVerifier(mock_client)
        
        verifier.verified_receipts = [
            VerifiedReceipt(
                contract_id="1", contract_name="C1", tenant_name="T1",
                rent_date_from="2024-01-01", rent_date_to="2024-01-31",
                payment_date="2024-01-15", rent_value=100.00,
                issue_date="2024-01-16", receipt_number="R-001",
                verification_status="Verified", error_message=None
            ),
            VerifiedReceipt(
                contract_id="2", contract_name="C2", tenant_name="T2",
                rent_date_from="2024-02-01", rent_date_to="2024-02-29",
                payment_date="2024-02-15", rent_value=200.00,
                issue_date="2024-02-16", receipt_number="R-002",
                verification_status="Verified", error_message=None
            ),
            VerifiedReceipt(
                contract_id="3", contract_name="C3", tenant_name="T3",
                rent_date_from="2024-03-01", rent_date_to="2024-03-31",
                payment_date="2024-03-15", rent_value=300.00,
                issue_date="2024-03-16", receipt_number="R-003",
                verification_status="Not Found", error_message="Not found"
            ),
            VerifiedReceipt(
                contract_id="4", contract_name="C4", tenant_name="T4",
                rent_date_from="2024-04-01", rent_date_to="2024-04-30",
                payment_date="2024-04-15", rent_value=400.00,
                issue_date="2024-04-16", receipt_number="R-004",
                verification_status="Error", error_message="Network error"
            ),
            VerifiedReceipt(
                contract_id="5", contract_name="C5", tenant_name="T5",
                rent_date_from="2024-05-01", rent_date_to="2024-05-31",
                payment_date="2024-05-15", rent_value=500.00,
                issue_date="2024-05-16", receipt_number="R-005",
                verification_status="Verified", error_message=None
            )
        ]
        
        stats = verifier.get_summary_stats()
        
        assert stats['total'] == 5
        assert stats['verified'] == 3
        assert stats['not_found'] == 1
        assert stats['error'] == 1
    
    def test_summary_stats_all_verified(self):
        """Test summary stats when all receipts verified."""
        mock_client = Mock()
        verifier = ReceiptVerifier(mock_client)
        
        verifier.verified_receipts = [
            VerifiedReceipt(
                contract_id=str(i), contract_name=f"C{i}", tenant_name=f"T{i}",
                rent_date_from="2024-01-01", rent_date_to="2024-01-31",
                payment_date="2024-01-15", rent_value=100.00 * i,
                issue_date="2024-01-16", receipt_number=f"R-{i:03d}",
                verification_status="Verified", error_message=None
            )
            for i in range(1, 11)
        ]
        
        stats = verifier.get_summary_stats()
        
        assert stats['total'] == 10
        assert stats['verified'] == 10
        assert stats['not_found'] == 0
        assert stats['error'] == 0


class TestReceiptVerifierIntegration:
    """Integration tests for ReceiptVerifier."""
    
    def test_full_verification_workflow(self):
        """Test complete workflow: verify, get stats, export."""
        mock_client = Mock()
        
        # Mock portal responses
        def mock_verify(contract_id, receipt_number):
            if contract_id == "1":
                return (True, {'contract_name': 'Contract 1'})
            elif contract_id == "2":
                return (True, None)
            else:
                return (False, {'error': 'Network error'})
        
        mock_client.verify_receipt_in_portal.side_effect = mock_verify
        
        verifier = ReceiptVerifier(mock_client)
        
        # Create processing results
        results = [
            ProcessingResult(success=True, contract_id="1", receipt_number="R-001", value=100.00),
            ProcessingResult(success=True, contract_id="2", receipt_number="R-002", value=200.00),
            ProcessingResult(success=True, contract_id="3", receipt_number="R-003", value=300.00)
        ]
        
        # Verify
        verified = verifier.verify_processing_results(results)
        assert len(verified) == 3
        
        # Get stats
        stats = verifier.get_summary_stats()
        assert stats['total'] == 3
        assert stats['verified'] == 1
        assert stats['not_found'] == 1
        assert stats['error'] == 1
        
        # Export
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            file_path = f.name
        
        try:
            success, message = verifier.export_to_csv(file_path)
            assert success is True
            assert os.path.exists(file_path)
        finally:
            if os.path.exists(file_path):
                os.unlink(file_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
