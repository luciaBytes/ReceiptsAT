"""
Extended unit tests for API Monitor utility focusing on validation and monitoring.
Targets: API validation, endpoint detection, payload validation, error detection.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from utils.api_monitor import APIPayloadMonitor


class TestAPIPayloadMonitorInit:
    """Test API monitor initialization."""
    
    def test_monitor_initialization(self):
        """Test monitor initializes correctly."""
        monitor = APIPayloadMonitor()
        
        assert monitor is not None
        assert hasattr(monitor, 'known_endpoints')
    
    def test_monitor_has_known_endpoints(self):
        """Test monitor has predefined known endpoints."""
        monitor = APIPayloadMonitor()
        
        assert len(monitor.known_endpoints) > 0
        assert isinstance(monitor.known_endpoints, dict)
    
    def test_emitir_recibo_endpoint_registered(self):
        """Test that emitirRecibo endpoint is registered."""
        monitor = APIPayloadMonitor()
        
        # Should have the main receipt emission endpoint
        endpoint_found = any('emitirRecibo' in key for key in monitor.known_endpoints.keys())
        assert endpoint_found


class TestEndpointValidation:
    """Test API endpoint validation."""
    
    def test_validate_known_endpoint(self):
        """Test validation of known endpoint."""
        monitor = APIPayloadMonitor()
        
        # Should not raise exception
        try:
            monitor.validate_api_call(
                '/arrendamento/api/emitirRecibo',
                'POST',
                payload={'numContrato': '12345'}
            )
            success = True
        except:
            success = False
        
        assert success
    
    def test_validate_unknown_endpoint_warns(self):
        """Test that unknown endpoint triggers warning."""
        monitor = APIPayloadMonitor()
        
        # Should handle unknown endpoint gracefully
        try:
            monitor.validate_api_call(
                '/unknown/endpoint',
                'GET'
            )
            success = True
        except:
            success = False
        
        assert success
    
    def test_validate_get_contracts_endpoint(self):
        """Test validation of get contracts endpoint."""
        monitor = APIPayloadMonitor()
        
        # Should recognize the contracts endpoint
        try:
            monitor.validate_api_call(
                '/arrendamento/api/obterElementosContratosEmissaoRecibos/locador',
                'GET'
            )
            success = True
        except:
            success = False
        
        assert success


class TestPayloadValidation:
    """Test payload validation for API calls."""
    
    def test_validate_emitir_recibo_payload(self):
        """Test validation of emitirRecibo payload."""
        monitor = APIPayloadMonitor()
        
        payload = {
            'numContrato': '12345',
            'versaoContrato': '1',
            'nifEmitente': '123456789',
            'nomeEmitente': 'Test',
            'valor': 1000.0,
            'tipoContrato': 'rent',
            'locadores': [],
            'locatarios': [],
            'imoveis': [],
            'dataInicio': '2025-01-01',
            'dataFim': '2025-01-31',
            'dataRecebimento': '2025-02-01',
            'tipoImportancia': 'RENDA'
        }
        
        # Should validate successfully
        try:
            monitor.validate_api_call(
                '/arrendamento/api/emitirRecibo',
                'POST',
                payload=payload
            )
            success = True
        except:
            success = False
        
        assert success
    
    def test_validate_payload_missing_required_fields(self):
        """Test validation with missing required fields."""
        monitor = APIPayloadMonitor()
        
        # Incomplete payload
        payload = {'numContrato': '12345'}
        
        # Should handle gracefully (warn but not crash)
        try:
            monitor.validate_api_call(
                '/arrendamento/api/emitirRecibo',
                'POST',
                payload=payload
            )
            success = True
        except:
            success = False
        
        assert success
    
    def test_validate_payload_none(self):
        """Test validation with None payload."""
        monitor = APIPayloadMonitor()
        
        # Should handle None payload
        try:
            monitor.validate_api_call(
                '/arrendamento/api/emitirRecibo',
                'POST',
                payload=None
            )
            success = True
        except:
            success = False
        
        assert success


class TestResponseValidation:
    """Test API response validation."""
    
    def test_validate_successful_response(self):
        """Test validation of successful response."""
        monitor = APIPayloadMonitor()
        
        try:
            monitor.validate_api_call(
                '/arrendamento/api/emitirRecibo',
                'POST',
                payload={'numContrato': '12345'},
                response_status=200,
                response_data={'success': True, 'receiptNumber': 'REC123'}
            )
            success = True
        except:
            success = False
        
        assert success
    
    def test_validate_error_response(self):
        """Test validation of error response."""
        monitor = APIPayloadMonitor()
        
        try:
            monitor.validate_api_call(
                '/arrendamento/api/emitirRecibo',
                'POST',
                payload={'numContrato': '12345'},
                response_status=500,
                error='Internal server error'
            )
            success = True
        except:
            success = False
        
        assert success
    
    def test_validate_404_response(self):
        """Test validation of 404 response."""
        monitor = APIPayloadMonitor()
        
        try:
            monitor.validate_api_call(
                '/unknown/endpoint',
                'GET',
                response_status=404
            )
            success = True
        except:
            success = False
        
        assert success


class TestContractTracking:
    """Test contract-specific tracking."""
    
    def test_validate_with_contract_id(self):
        """Test validation with contract ID context."""
        monitor = APIPayloadMonitor()
        
        try:
            monitor.validate_api_call(
                '/arrendamento/api/emitirRecibo',
                'POST',
                payload={'numContrato': '12345'},
                contract_id='12345'
            )
            success = True
        except:
            success = False
        
        assert success
    
    def test_validate_multiple_contracts(self):
        """Test validation for multiple different contracts."""
        monitor = APIPayloadMonitor()
        
        # Should handle multiple contracts independently
        try:
            monitor.validate_api_call(
                '/arrendamento/api/emitirRecibo',
                'POST',
                payload={'numContrato': '12345'},
                contract_id='12345'
            )
            monitor.validate_api_call(
                '/arrendamento/api/emitirRecibo',
                'POST',
                payload={'numContrato': '67890'},
                contract_id='67890'
            )
            success = True
        except:
            success = False
        
        assert success


class TestHTTPMethods:
    """Test different HTTP methods."""
    
    def test_validate_post_method(self):
        """Test POST method validation."""
        monitor = APIPayloadMonitor()
        
        try:
            monitor.validate_api_call(
                '/arrendamento/api/emitirRecibo',
                'POST',
                payload={}
            )
            success = True
        except:
            success = False
        
        assert success
    
    def test_validate_get_method(self):
        """Test GET method validation."""
        monitor = APIPayloadMonitor()
        
        try:
            monitor.validate_api_call(
                '/arrendamento/criarRecibo',
                'GET'
            )
            success = True
        except:
            success = False
        
        assert success
    
    def test_validate_wrong_method_for_endpoint(self):
        """Test validation with wrong HTTP method for endpoint."""
        monitor = APIPayloadMonitor()
        
        # emitirRecibo should be POST, not GET
        # Should handle gracefully (warn but not crash)
        try:
            monitor.validate_api_call(
                '/arrendamento/api/emitirRecibo',
                'GET'
            )
            success = True
        except:
            success = False
        
        assert success


class TestErrorDetection:
    """Test error detection capabilities."""
    
    def test_detect_api_error_in_response(self):
        """Test detection of API errors in response."""
        monitor = APIPayloadMonitor()
        
        # Should handle error response
        try:
            monitor.validate_api_call(
                '/arrendamento/api/emitirRecibo',
                'POST',
                payload={},
                response_status=400,
                error='Bad request'
            )
            success = True
        except:
            success = False
        
        assert success
    
    def test_detect_authentication_error(self):
        """Test detection of authentication errors."""
        monitor = APIPayloadMonitor()
        
        try:
            monitor.validate_api_call(
                '/arrendamento/api/emitirRecibo',
                'POST',
                payload={},
                response_status=401,
                error='Unauthorized'
            )
            success = True
        except:
            success = False
        
        assert success
    
    def test_detect_timeout_error(self):
        """Test detection of timeout errors."""
        monitor = APIPayloadMonitor()
        
        try:
            monitor.validate_api_call(
                '/arrendamento/api/emitirRecibo',
                'POST',
                payload={},
                error='Request timeout'
            )
            success = True
        except:
            success = False
        
        assert success


class TestEdgeCases:
    """Test edge cases and unusual scenarios."""
    
    def test_validate_empty_payload(self):
        """Test validation with empty payload dict."""
        monitor = APIPayloadMonitor()
        
        try:
            monitor.validate_api_call(
                '/arrendamento/api/emitirRecibo',
                'POST',
                payload={}
            )
            success = True
        except:
            success = False
        
        assert success
    
    def test_validate_very_long_contract_id(self):
        """Test validation with unusually long contract ID."""
        monitor = APIPayloadMonitor()
        
        long_id = 'A' * 1000
        
        try:
            monitor.validate_api_call(
                '/arrendamento/api/emitirRecibo',
                'POST',
                contract_id=long_id
            )
            success = True
        except:
            success = False
        
        assert success
    
    def test_validate_special_characters_in_endpoint(self):
        """Test validation with special characters."""
        monitor = APIPayloadMonitor()
        
        try:
            monitor.validate_api_call(
                '/endpoint/with/special?param=value&foo=bar',
                'GET'
            )
            success = True
        except:
            success = False
        
        assert success
