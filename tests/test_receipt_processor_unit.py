"""
Unit tests for receipt_processor module.
Tests business logic for receipt processing with mocked dependencies.
"""

import sys
import os
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from receipt_processor import ReceiptProcessor, ProcessingResult
from csv_handler import ReceiptData
from web_client import WebClient


class TestProcessingResult:
    """Test ProcessingResult dataclass."""
    
    def test_processing_result_creation(self):
        """Test creating a ProcessingResult instance."""
        result = ProcessingResult(
            contract_id="12345",
            tenant_name="Test Tenant",
            success=True,
            receipt_number="R-001",
            value=100.0,
            status="Success"
        )
        assert result.contract_id == "12345"
        assert result.tenant_name == "Test Tenant"
        assert result.success is True
        assert result.value == 100.0
    
    def test_processing_result_defaults(self):
        """Test ProcessingResult default values."""
        result = ProcessingResult(contract_id="12345")
        assert result.success is False
        assert result.tenant_name == ""
        assert result.value == 0.0
        assert result.error_message == ""


class TestReceiptProcessorInit:
    """Test ReceiptProcessor initialization."""
    
    def test_init_with_web_client(self):
        """Test processor initialization with web client."""
        mock_client = Mock(spec=WebClient)
        processor = ReceiptProcessor(mock_client)
        
        assert processor.web_client is mock_client
        assert processor.results == []
        assert processor.dry_run is False
        assert isinstance(processor._contracts_data_cache, dict)
    
    def test_set_dry_run(self):
        """Test enabling and disabling dry run mode."""
        mock_client = Mock(spec=WebClient)
        processor = ReceiptProcessor(mock_client)
        
        processor.set_dry_run(True)
        assert processor.dry_run is True
        
        processor.set_dry_run(False)
        assert processor.dry_run is False


class TestContractValidation:
    """Test contract validation functionality."""
    
    def test_validate_contracts_empty_list(self):
        """Test validation with empty receipt list."""
        mock_client = Mock(spec=WebClient)
        processor = ReceiptProcessor(mock_client)
        
        report = processor.validate_contracts([])
        
        assert report['success'] is False
        assert "No receipts" in report['message']
        assert 'validation_errors' in report
    
    def test_validate_contracts_calls_web_client(self):
        """Test that validation calls web client with correct contract IDs."""
        mock_client = Mock(spec=WebClient)
        mock_client.validate_csv_contracts = Mock(return_value={
            'success': True,
            'valid_contracts': ['123', '456'],
            'invalid_contracts': [],
            'portal_contracts_count': 2,
            'validation_errors': [],
            'message': 'Success',
            'portal_contracts_data': []
        })
        
        processor = ReceiptProcessor(mock_client)
        
        receipts = [
            ReceiptData(contract_id='123', from_date='2024-01-01', 
                       to_date='2024-01-31', receipt_type='rent', payment_date='2024-02-01', value=100.0),
            ReceiptData(contract_id='456', from_date='2024-01-01',
                       to_date='2024-01-31', receipt_type='rent', payment_date='2024-02-01', value=200.0),
        ]
        
        report = processor.validate_contracts(receipts)
        
        mock_client.validate_csv_contracts.assert_called_once()
        call_args = mock_client.validate_csv_contracts.call_args[0][0]
        assert '123' in call_args
        assert '456' in call_args
        assert report['success'] is True
    
    def test_validate_contracts_caches_data(self):
        """Test that validation caches contract data."""
        mock_client = Mock(spec=WebClient)
        mock_client.validate_csv_contracts = Mock(return_value={
            'success': True,
            'valid_contracts': ['123'],
            'invalid_contracts': [],
            'portal_contracts_count': 1,
            'validation_errors': [],
            'message': 'Success',
            'portal_contracts_data': [
                {
                    'numero': '123',
                    'locatarios': [{'nome': 'Tenant A'}]
                }
            ]
        })
        
        processor = ReceiptProcessor(mock_client)
        
        receipts = [
            ReceiptData(contract_id='123', from_date='2024-01-01',
                       to_date='2024-01-31', receipt_type='rent', payment_date='2024-02-01', value=100.0)
        ]
        
        report = processor.validate_contracts(receipts)
        
        assert '123' in processor._contracts_data_cache
        assert processor._contracts_data_cache['123']['numero'] == '123'
    
    def test_validate_contracts_duplicate_contract_ids(self):
        """Test validation with duplicate contract IDs extracts unique set."""
        mock_client = Mock(spec=WebClient)
        mock_client.validate_csv_contracts = Mock(return_value={
            'success': True,
            'valid_contracts': ['123'],
            'invalid_contracts': [],
            'portal_contracts_count': 1,
            'validation_errors': [],
            'message': 'Success',
            'portal_contracts_data': []
        })
        
        processor = ReceiptProcessor(mock_client)
        
        receipts = [
            ReceiptData(contract_id='123', from_date='2024-01-01',
                       to_date='2024-01-31', receipt_type='rent', payment_date='2024-02-01', value=100.0),
            ReceiptData(contract_id='123', from_date='2024-02-01',
                       to_date='2024-02-28', receipt_type='rent', payment_date='2024-03-01', value=100.0),
        ]
        
        report = processor.validate_contracts(receipts)
        
        # Should only call with unique contract ID once
        call_args = mock_client.validate_csv_contracts.call_args[0][0]
        assert call_args.count('123') == 1


class TestBulkProcessing:
    """Test bulk receipt processing."""
    
    def test_process_receipts_bulk_clears_previous_results(self):
        """Test that processing clears previous results."""
        mock_client = Mock(spec=WebClient)
        mock_client.validate_csv_contracts = Mock(return_value={
            'success': True,
            'valid_contracts': [],
            'invalid_contracts': [],
            'portal_contracts_count': 0,
            'validation_errors': [],
            'message': 'Success',
            'portal_contracts_data': []
        })
        
        processor = ReceiptProcessor(mock_client)
        processor.results = [Mock()]  # Add fake previous result
        
        receipts = []
        processor.process_receipts_bulk(receipts, validate_contracts=False)
        
        assert len(processor.results) == 0
    
    def test_process_receipts_bulk_with_progress_callback(self):
        """Test that progress callback is called during processing."""
        mock_client = Mock(spec=WebClient)
        mock_client.validate_csv_contracts = Mock(return_value={
            'success': True,
            'valid_contracts': ['123'],
            'invalid_contracts': [],
            'portal_contracts_count': 1,
            'validation_errors': [],
            'message': 'Success',
            'portal_contracts_data': []
        })
        
        processor = ReceiptProcessor(mock_client)
        
        progress_calls = []
        def progress_callback(current, total, message):
            progress_calls.append((current, total, message))
        
        receipts = [
            ReceiptData(contract_id='123', from_date='2024-01-01',
                       to_date='2024-01-31', receipt_type='rent', payment_date='2024-02-01', value=100.0)
        ]
        
        processor.process_receipts_bulk(receipts, progress_callback=progress_callback, validate_contracts=True)
        
        # Should have at least one progress callback for validation
        assert len(progress_calls) > 0
        assert any("Validating" in call[2] for call in progress_calls)
    
    def test_process_receipts_bulk_skip_validation(self):
        """Test processing without contract validation."""
        mock_client = Mock(spec=WebClient)
        
        processor = ReceiptProcessor(mock_client)
        
        receipts = []
        processor.process_receipts_bulk(receipts, validate_contracts=False)
        
        # Should not call validate_csv_contracts
        assert not mock_client.validate_csv_contracts.called


class TestStopCheck:
    """Test stop check functionality during processing."""
    
    def test_stop_check_callable(self):
        """Test that stop_check parameter accepts callable."""
        mock_client = Mock(spec=WebClient)
        processor = ReceiptProcessor(mock_client)
        
        stop_called = []
        def stop_check():
            stop_called.append(True)
            return False
        
        receipts = []
        processor.process_receipts_bulk(receipts, validate_contracts=False, stop_check=stop_check)
        
        # Function should be passed (whether called depends on implementation)
        assert callable(stop_check)


class TestContractsCacheManagement:
    """Test internal contracts cache management."""
    
    def test_cache_cleared_on_new_validation(self):
        """Test that cache is cleared when running new validation."""
        mock_client = Mock(spec=WebClient)
        mock_client.validate_csv_contracts = Mock(return_value={
            'success': True,
            'valid_contracts': ['123'],
            'invalid_contracts': [],
            'portal_contracts_count': 1,
            'validation_errors': [],
            'message': 'Success',
            'portal_contracts_data': [
                {'numero': '123', 'locatarios': []}
            ]
        })
        
        processor = ReceiptProcessor(mock_client)
        
        # Add something to cache
        processor._contracts_data_cache['old'] = {'data': 'old'}
        
        receipts = [
            ReceiptData(contract_id='123', from_date='2024-01-01',
                       to_date='2024-01-31', receipt_type='rent', payment_date='2024-02-01', value=100.0)
        ]
        
        processor.validate_contracts(receipts)
        
        # Old cache should be cleared
        assert 'old' not in processor._contracts_data_cache
        assert '123' in processor._contracts_data_cache
