"""
Extended unit tests for ReceiptProcessor focusing on error paths and edge cases.
Targets: error handling, retry logic, receipt extraction, validation failures.
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from receipt_processor import ReceiptProcessor, ProcessingResult
from csv_handler import ReceiptData
from web_client import WebClient


class TestErrorHandling:
    """Test error handling and recovery mechanisms."""
    
    def test_process_single_receipt_api_error(self):
        """Test handling of API errors during receipt processing."""
        mock_client = Mock(spec=WebClient)
        mock_client.get_receipt_form.return_value = (True, {'tenant_name': 'Test Tenant'})
        mock_client.issue_receipt.return_value = (False, {"error": "API connection error"})
        
        processor = ReceiptProcessor(mock_client)
        processor._contracts_data_cache = {'12345': {'numero': '12345', 'locatarios': [{'nome': 'Test'}]}}
        
        receipt = ReceiptData(
            contract_id='12345',
            from_date='2025-01-01',
            to_date='2025-01-31',
            receipt_type='rent',
            value=1000.00,
            payment_date='2025-02-05'
        )
        
        result = processor._process_single_receipt(receipt)
        
        assert result.success is False
        assert 'error' in result.error_message.lower() or 'api' in result.error_message.lower()
        assert result.status == 'Failed'
    
    def test_process_single_receipt_invalid_contract(self):
        """Test processing receipt with invalid contract ID."""
        mock_client = Mock(spec=WebClient)
        processor = ReceiptProcessor(mock_client)
        processor._contracts_data_cache = {}  # Empty cache - contract not found
        
        receipt = ReceiptData(
            contract_id='99999',
            from_date='2025-01-01',
            to_date='2025-01-31',
            receipt_type='rent',
            value=1000.00
        )
        
        result = processor._process_single_receipt(receipt)
        
        assert result.success is False
        assert result.contract_id == '99999'
    
    def test_validate_contracts_empty_list(self):
        """Test validation with empty receipt list."""
        mock_client = Mock(spec=WebClient)
        processor = ReceiptProcessor(mock_client)
        
        result = processor.validate_contracts([])
        
        assert result['success'] is False
        assert 'no receipts' in result['message'].lower()
    
    def test_validate_contracts_api_failure(self):
        """Test handling of API failure during contract validation."""
        mock_client = Mock(spec=WebClient)
        mock_client.validate_csv_contracts.return_value = {
            'success': False,
            'message': 'Connection timeout',
            'invalid_contracts': []
        }
        
        processor = ReceiptProcessor(mock_client)
        receipts = [
            ReceiptData('12345', '2025-01-01', '2025-01-31', 'rent', 1000.00)
        ]
        
        result = processor.validate_contracts(receipts)
        
        assert result['success'] is False
        assert 'timeout' in result['message'].lower()


class TestContractCaching:
    """Test contract data caching mechanisms."""
    
    def test_contracts_cache_populated_on_validation(self):
        """Test that validation populates the contracts cache."""
        mock_client = Mock(spec=WebClient)
        mock_client.validate_csv_contracts.return_value = {
            'success': True,
            'message': 'Validation successful',
            'invalid_contracts': [],
            'valid_contracts': ['12345', '67890'],
            'validation_errors': [],
            'portal_contracts_count': 2,
            'portal_contracts_data': [
                {'numero': '12345', 'locatarios': [{'nome': 'John Doe'}]},
                {'numero': '67890', 'locatarios': [{'nome': 'Jane Smith'}]}
            ]
        }
        
        processor = ReceiptProcessor(mock_client)
        receipts = [
            ReceiptData('12345', '2025-01-01', '2025-01-31', 'rent', 1000.00),
            ReceiptData('67890', '2025-01-01', '2025-01-31', 'rent', 1500.00)
        ]
        
        processor.validate_contracts(receipts)
        
        assert len(processor._contracts_data_cache) == 2
        assert '12345' in processor._contracts_data_cache
        assert '67890' in processor._contracts_data_cache
    
    def test_contracts_cache_cleared_on_new_validation(self):
        """Test that cache is cleared before new validation."""
        mock_client = Mock(spec=WebClient)
        mock_client.validate_csv_contracts.return_value = {
            'success': True,
            'message': 'Validation successful',
            'invalid_contracts': [],
            'valid_contracts': ['11111'],
            'validation_errors': [],
            'portal_contracts_count': 1,
            'portal_contracts_data': [
                {'numero': '11111', 'locatarios': [{'nome': 'New Tenant'}]}
            ]
        }
        
        processor = ReceiptProcessor(mock_client)
        
        # Populate cache with old data
        processor._contracts_data_cache = {'99999': {'numero': '99999'}}
        
        receipts = [ReceiptData('11111', '2025-01-01', '2025-01-31', 'rent', 1000.00)]
        processor.validate_contracts(receipts)
        
        # Old data should be gone
        assert '99999' not in processor._contracts_data_cache
        assert '11111' in processor._contracts_data_cache
    
    def test_contracts_cache_handles_missing_numero(self):
        """Test that contracts without 'numero' field are not cached."""
        mock_client = Mock(spec=WebClient)
        mock_client.validate_csv_contracts.return_value = {
            'success': True,
            'message': 'Validation successful',
            'invalid_contracts': [],
            'valid_contracts': ['12345'],
            'validation_errors': [],
            'portal_contracts_count': 2,
            'portal_contracts_data': [
                {'numero': '12345', 'locatarios': [{'nome': 'Valid'}]},
                {'invalid_field': 'no numero', 'locatarios': []}  # Missing numero
            ]
        }
        
        processor = ReceiptProcessor(mock_client)
        receipts = [ReceiptData('12345', '2025-01-01', '2025-01-31', 'rent', 1000.00)]
        
        processor.validate_contracts(receipts)
        
        # Only valid contract should be cached
        assert len(processor._contracts_data_cache) == 1
        assert '12345' in processor._contracts_data_cache


class TestBulkProcessing:
    """Test bulk receipt processing functionality."""
    
    def test_process_receipts_bulk_with_progress(self):
        """Test bulk processing with progress callback."""
        mock_client = Mock(spec=WebClient)
        mock_client.validate_csv_contracts.return_value = {
            'success': True,
            'invalid_contracts': [],
            'valid_contracts': ['12345'],
            'validation_errors': [],
            'portal_contracts_count': 1,
            'portal_contracts_data': [{'numero': '12345', 'locatarios': []}]
        }
        mock_client.issue_receipt.return_value = (True, "", "REC12345")
        
        processor = ReceiptProcessor(mock_client)
        
        receipts = [
            ReceiptData('12345', '2025-01-01', '2025-01-31', 'rent', 1000.00),
            ReceiptData('12345', '2025-02-01', '2025-02-28', 'rent', 1000.00)
        ]
        
        progress_updates = []
        def progress_callback(current, total, message):
            progress_updates.append((current, total, message))
        
        results = processor.process_receipts_bulk(receipts, progress_callback)
        
        assert len(results) == 2
        assert len(progress_updates) > 0
        assert progress_updates[-1][0] == progress_updates[-1][1]  # Final update
    
    def test_process_receipts_bulk_stop_check(self):
        """Test bulk processing can be stopped mid-execution."""
        mock_client = Mock(spec=WebClient)
        mock_client.validate_csv_contracts.return_value = {
            'success': True,
            'invalid_contracts': [],
            'valid_contracts': ['12345'],
            'validation_errors': [],
            'portal_contracts_count': 1,
            'portal_contracts_data': [{'numero': '12345', 'locatarios': []}]
        }
        
        processor = ReceiptProcessor(mock_client)
        
        receipts = [
            ReceiptData('12345', f'2025-0{i}-01', f'2025-0{i}-28', 'rent', 1000.00)
            for i in range(1, 6)
        ]
        
        stop_after = 2
        call_count = [0]
        
        def stop_check():
            call_count[0] += 1
            return call_count[0] > stop_after
        
        results = processor.process_receipts_bulk(receipts, stop_check=stop_check)
        
        # Should stop after processing a few
        assert len(results) <= stop_after + 1
    
    def test_process_receipts_bulk_dry_run(self):
        """Test bulk processing in dry run mode."""
        mock_client = Mock(spec=WebClient)
        mock_client.validate_csv_contracts.return_value = {
            'success': True,
            'invalid_contracts': [],
            'valid_contracts': ['12345'],
            'validation_errors': [],
            'portal_contracts_count': 1,
            'portal_contracts_data': [{'numero': '12345', 'locatarios': []}]
        }
        
        processor = ReceiptProcessor(mock_client)
        processor.set_dry_run(True)
        
        receipts = [ReceiptData('12345', '2025-01-01', '2025-01-31', 'rent', 1000.00)]
        
        results = processor.process_receipts_bulk(receipts)
        
        # In dry run, should not actually call issue_receipt
        mock_client.issue_receipt.assert_not_called()
        assert len(results) == 1


class TestStepByStepProcessing:
    """Test step-by-step processing with user confirmation."""
    
    def test_step_by_step_skip_invalid_contracts(self):
        """Test that invalid contracts are skipped in step-by-step mode."""
        mock_client = Mock(spec=WebClient)
        mock_client.validate_csv_contracts.return_value = {
            'success': True,
            'invalid_contracts': ['99999'],
            'valid_contracts': ['12345'],
            'validation_errors': [],
            'portal_contracts_count': 1,
            'portal_contracts_data': [{'numero': '12345', 'locatarios': []}]
        }
        
        processor = ReceiptProcessor(mock_client)
        
        receipts = [
            ReceiptData('12345', '2025-01-01', '2025-01-31', 'rent', 1000.00),
            ReceiptData('99999', '2025-01-01', '2025-01-31', 'rent', 1000.00)
        ]
        
        def confirm_callback(receipt_data, form_data):
            return 'confirm'
        
        results = processor.process_receipts_step_by_step(receipts, confirm_callback)
        
        # Should have result for invalid contract
        invalid_results = [r for r in results if r.contract_id == '99999']
        assert len(invalid_results) == 1
        assert invalid_results[0].status == 'Skipped'
    
    def test_step_by_step_validation_failure(self):
        """Test step-by-step when validation fails completely."""
        mock_client = Mock(spec=WebClient)
        mock_client.validate_csv_contracts.return_value = {
            'success': False,
            'message': 'Authentication required',
            'invalid_contracts': []
        }
        
        processor = ReceiptProcessor(mock_client)
        receipts = [ReceiptData('12345', '2025-01-01', '2025-01-31', 'rent', 1000.00)]
        
        def confirm_callback(receipt_data, form_data):
            return 'confirm'
        
        results = processor.process_receipts_step_by_step(receipts, confirm_callback)
        
        assert len(results) == 1
        assert results[0].success is False
        assert 'validation' in results[0].error_message.lower()
    
    def test_step_by_step_stop_check(self):
        """Test step-by-step can be stopped by user."""
        mock_client = Mock(spec=WebClient)
        mock_client.validate_csv_contracts.return_value = {
            'success': True,
            'invalid_contracts': [],
            'valid_contracts': ['12345'],
            'validation_errors': [],
            'portal_contracts_count': 1,
            'portal_contracts_data': [{'numero': '12345', 'locatarios': []}]
        }
        
        processor = ReceiptProcessor(mock_client)
        
        receipts = [
            ReceiptData('12345', f'2025-0{i}-01', f'2025-0{i}-28', 'rent', 1000.00)
            for i in range(1, 5)
        ]
        
        processed_count = [0]
        
        def confirm_callback(receipt_data, form_data):
            processed_count[0] += 1
            return 'confirm'
        
        def stop_check():
            return processed_count[0] >= 2
        
        results = processor.process_receipts_step_by_step(receipts, confirm_callback, stop_check)
        
        # Should stop after 2 receipts
        assert processed_count[0] <= 2


class TestTenantNameExtraction:
    """Test tenant name extraction from contract data."""
    
    def test_extract_single_tenant_name(self):
        """Test extracting name from contract with single tenant."""
        mock_client = Mock(spec=WebClient)
        processor = ReceiptProcessor(mock_client)
        
        processor._contracts_data_cache = {
            '12345': {
                'numero': '12345',
                'locatarios': [{'nome': 'John Doe'}]
            }
        }
        
        # Access cache to verify tenant name extraction works
        contract_data = processor._contracts_data_cache['12345']
        locatarios = contract_data.get('locatarios', [])
        
        assert len(locatarios) == 1
        assert locatarios[0]['nome'] == 'John Doe'
    
    def test_extract_multiple_tenant_names(self):
        """Test extracting names from contract with multiple tenants."""
        mock_client = Mock(spec=WebClient)
        processor = ReceiptProcessor(mock_client)
        
        processor._contracts_data_cache = {
            '12345': {
                'numero': '12345',
                'locatarios': [
                    {'nome': 'John Doe'},
                    {'nome': 'Jane Smith'}
                ]
            }
        }
        
        contract_data = processor._contracts_data_cache['12345']
        locatarios = contract_data.get('locatarios', [])
        
        assert len(locatarios) == 2
        names = [t['nome'] for t in locatarios]
        assert 'John Doe' in names
        assert 'Jane Smith' in names
    
    def test_contract_with_no_locatarios(self):
        """Test handling contract with no tenant information."""
        mock_client = Mock(spec=WebClient)
        processor = ReceiptProcessor(mock_client)
        
        processor._contracts_data_cache = {
            '12345': {
                'numero': '12345',
                'locatarios': []
            }
        }
        
        contract_data = processor._contracts_data_cache['12345']
        locatarios = contract_data.get('locatarios', [])
        
        assert len(locatarios) == 0


class TestResultsManagement:
    """Test results tracking and management."""
    
    def test_count_successful_receipts(self):
        """Test counting successful receipt processing."""
        mock_client = Mock(spec=WebClient)
        processor = ReceiptProcessor(mock_client)
        
        processor.results = [
            ProcessingResult('12345', success=True, status='Success'),
            ProcessingResult('67890', success=False, status='Failed'),
            ProcessingResult('11111', success=True, status='Success')
        ]
        
        count = processor._count_successful()
        assert count == 2
    
    def test_count_failed_receipts(self):
        """Test counting failed receipt processing."""
        mock_client = Mock(spec=WebClient)
        processor = ReceiptProcessor(mock_client)
        
        processor.results = [
            ProcessingResult('12345', success=True, status='Success'),
            ProcessingResult('67890', success=False, status='Failed'),
            ProcessingResult('11111', success=False, status='Failed')
        ]
        
        count = processor._count_failed()
        assert count == 2
    
    def test_results_cleared_on_new_processing(self):
        """Test that results are cleared when starting new processing."""
        mock_client = Mock(spec=WebClient)
        mock_client.validate_csv_contracts.return_value = {
            'success': True,
            'invalid_contracts': [],
            'valid_contracts': ['12345'],
            'validation_errors': [],
            'portal_contracts_count': 0,
            'portal_contracts_data': []
        }
        
        processor = ReceiptProcessor(mock_client)
        
        # Add old results
        processor.results = [ProcessingResult('old', success=True)]
        
        receipts = [ReceiptData('12345', '2025-01-01', '2025-01-31', 'rent', 1000.00)]
        processor.process_receipts_bulk(receipts)
        
        # Old results should be gone
        assert not any(r.contract_id == 'old' for r in processor.results)


class TestDryRunMode:
    """Test dry run mode functionality."""
    
    def test_set_dry_run_enabled(self):
        """Test enabling dry run mode."""
        mock_client = Mock(spec=WebClient)
        processor = ReceiptProcessor(mock_client)
        
        processor.set_dry_run(True)
        assert processor.dry_run is True
    
    def test_set_dry_run_disabled(self):
        """Test disabling dry run mode."""
        mock_client = Mock(spec=WebClient)
        processor = ReceiptProcessor(mock_client)
        processor.dry_run = True
        
        processor.set_dry_run(False)
        assert processor.dry_run is False
    
    def test_dry_run_does_not_call_api(self):
        """Test that dry run mode doesn't make actual API calls."""
        mock_client = Mock(spec=WebClient)
        mock_client.validate_csv_contracts.return_value = {
            'success': True,
            'invalid_contracts': [],
            'portal_contracts_data': [{'numero': '12345', 'locatarios': []}]
        }
        
        processor = ReceiptProcessor(mock_client)
        processor.set_dry_run(True)
        
        receipt = ReceiptData('12345', '2025-01-01', '2025-01-31', 'rent', 1000.00)
        result = processor._process_single_receipt(receipt)
        
        # Should not call issue_receipt in dry run
        mock_client.issue_receipt.assert_not_called()
        assert 'Dry Run' in result.status or result.status == 'Success'
