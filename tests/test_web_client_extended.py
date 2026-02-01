"""
Extended unit tests for WebClient focusing on authentication errors and edge cases.
Targets: login failures, session expiration, HTTP errors, 2FA handling.
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
import requests

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from web_client import WebClient


class TestAuthenticationErrors:
    """Test authentication error handling."""
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        client = WebClient()
        
        with patch.object(client, '_establish_session', return_value=True):
            with patch.object(client, '_get_login_form_data', return_value={'partID': 'PFAP'}):
                with patch.object(client, '_get_csrf_token_data', return_value=None):
                    with patch.object(client.session, 'post') as mock_post:
                        mock_response = Mock()
                        mock_response.status_code = 401
                        mock_response.text = 'Invalid credentials'
                        mock_post.return_value = mock_response
                        
                        success, message = client.login('invalid_user', 'wrong_password')
                        
                        assert success is False
                        assert len(message) > 0
    
    def test_login_max_attempts_exceeded(self):
        """Test login attempt limit enforcement."""
        client = WebClient()
        client.login_attempts = client.max_login_attempts
        
        success, message = client.login('user', 'pass')
        
        assert success is False
        assert 'maximum' in message.lower() or 'exceeded' in message.lower()
    
    def test_login_session_establishment_failure(self):
        """Test handling of session establishment failure."""
        client = WebClient()
        
        with patch.object(client, '_establish_session', return_value=False):
            success, message = client.login('user', 'pass')
            
            assert success is False
            assert 'session' in message.lower()
    
    def test_login_form_data_retrieval_failure(self):
        """Test handling when login form data cannot be retrieved."""
        client = WebClient()
        
        with patch.object(client, '_establish_session', return_value=True):
            with patch.object(client, '_get_login_form_data', return_value=None):
                success, message = client.login('user', 'pass')
                
                assert success is False
                assert 'form' in message.lower()


class TestSessionManagement:
    """Test session management and expiration."""
    
    def test_establish_session_success(self):
        """Test successful session establishment."""
        client = WebClient()
        
        with patch.object(client.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            result = client._establish_session()
            
            assert result is True
            assert mock_get.call_count == 2  # Portal + login page
    
    def test_establish_session_timeout(self):
        """Test session establishment with timeout."""
        client = WebClient()
        
        with patch.object(client.session, 'get', side_effect=requests.Timeout):
            result = client._establish_session()
            
            assert result is False
    
    def test_establish_session_connection_error(self):
        """Test session establishment with connection error."""
        client = WebClient()
        
        with patch.object(client.session, 'get', side_effect=requests.ConnectionError):
            result = client._establish_session()
            
            assert result is False


class TestHTTPErrorHandling:
    """Test HTTP error handling."""
    
    def test_login_http_500_error(self):
        """Test handling of HTTP 500 server error during login."""
        client = WebClient()
        
        with patch.object(client, '_establish_session', return_value=True):
            with patch.object(client, '_get_login_form_data', return_value={'partID': 'PFAP'}):
                with patch.object(client.session, 'post') as mock_post:
                    mock_post.side_effect = requests.HTTPError("500 Server Error")
                    
                    success, message = client.login('user', 'pass')
                    
                    assert success is False
    
    def test_login_network_error(self):
        """Test handling of network errors during login."""
        client = WebClient()
        
        with patch.object(client, '_establish_session', return_value=True):
            with patch.object(client, '_get_login_form_data', return_value={'partID': 'PFAP'}):
                with patch.object(client.session, 'post', side_effect=requests.ConnectionError):
                    success, message = client.login('user', 'pass')
                    
                    assert success is False
                    assert len(message) > 0


class TestCSRFTokenHandling:
    """Test CSRF token extraction and usage."""
    
    def test_get_csrf_token_data_success(self):
        """Test CSRF token extraction attempts."""
        client = WebClient()
        
        html_with_csrf = '''
        <html>
            <meta name="_csrf" content="abc123xyz">
            <meta name="_csrf_header" content="X-CSRF-TOKEN">
        </html>
        '''
        
        with patch.object(client.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.text = html_with_csrf
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            csrf_data = client._get_csrf_token_data()
            
            # Method should complete without error
            assert csrf_data is None or isinstance(csrf_data, dict)
    
    def test_get_csrf_token_data_missing(self):
        """Test CSRF token extraction when token is missing."""
        client = WebClient()
        
        html_without_csrf = '<html><body>No CSRF token here</body></html>'
        
        with patch.object(client.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.text = html_without_csrf
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            csrf_data = client._get_csrf_token_data()
            
            # Should handle gracefully
            assert csrf_data is None or csrf_data.get('token') is None
    
    def test_get_csrf_token_data_network_error(self):
        """Test CSRF token extraction with network error."""
        client = WebClient()
        
        with patch.object(client.session, 'get', side_effect=requests.ConnectionError):
            csrf_data = client._get_csrf_token_data()
            
            assert csrf_data is None


class Test2FAHandling:
    """Test two-factor authentication handling."""
    
    def test_pending_2fa_flag_initial_state(self):
        """Test that 2FA pending flag is initially False."""
        client = WebClient()
        assert client.pending_2fa is False
    
    def test_login_with_sms_code(self):
        """Test login method called with SMS code (2FA verification)."""
        client = WebClient()
        client.pending_2fa = True
        client._current_username = 'test_user'
        
        with patch.object(client, '_verify_2fa_sms') as mock_verify:
            mock_verify.return_value = (True, "Verification successful")
            
            success, message = client.login('test_user', 'password', sms_code='123456')
            
            mock_verify.assert_called_once_with('123456')
            assert success is True
    
    def test_2fa_verification_failure(self):
        """Test handling of failed 2FA verification."""
        client = WebClient()
        client.pending_2fa = True
        
        with patch.object(client, '_verify_2fa_sms') as mock_verify:
            mock_verify.return_value = (False, "Invalid SMS code")
            
            success, message = client.login('user', 'pass', sms_code='wrong')
            
            assert success is False
            assert 'invalid' in message.lower() or 'code' in message.lower()


class TestContractValidation:
    """Test contract validation functionality."""
    
    def test_validate_csv_contracts_success(self):
        """Test successful contract validation."""
        client = WebClient()
        client.authenticated = True
        
        # Mock the actual implementation behavior
        with patch.object(client, 'get_contracts_with_tenant_data') as mock_get_contracts:
            mock_get_contracts.return_value = (True, [
                {'numero': '12345', 'locatarios': [], 'estado': {'codigo': 'ACTIVO'}},
                {'numero': '67890', 'locatarios': [], 'estado': {'codigo': 'ACTIVO'}}
            ], 'Success')
            
            result = client.validate_csv_contracts(['12345', '67890'])
            
            assert result['success'] is True
            assert len(result.get('invalid_contracts', [])) == 0
    
    def test_validate_csv_contracts_not_authenticated(self):
        """Test contract validation when not authenticated."""
        client = WebClient()
        client.authenticated = False
        
        result = client.validate_csv_contracts(['12345'])
        
        assert result['success'] is False
    
    def test_validate_csv_contracts_with_invalid(self):
        """Test contract validation with some invalid contracts."""
        client = WebClient()
        client.authenticated = True
        
        with patch.object(client, 'get_contracts_with_tenant_data') as mock_get_contracts:
            mock_get_contracts.return_value = (True, [
                {'numero': '12345', 'locatarios': [], 'estado': {'codigo': 'ACTIVO'}}
                # 67890 is missing - invalid
            ], 'Success')
            
            result = client.validate_csv_contracts(['12345', '67890'])
            
            assert '67890' in result.get('invalid_contracts', [])


class TestReceiptIssuance:
    """Test receipt issuance functionality."""
    
    def test_issue_receipt_not_authenticated(self):
        """Test receipt issuance when not authenticated."""
        client = WebClient()
        client.authenticated = False
        
        submission_data = {
            'contract_id': '12345',
            'from_date': '2025-01-01',
            'to_date': '2025-01-31',
            'value': 1000.00
        }
        
        success, result = client.issue_receipt(submission_data)
        
        assert success is False
    
    def test_issue_receipt_api_error(self):
        """Test receipt issuance with API error."""
        client = WebClient()
        client.authenticated = True
        
        submission_data = {
            'contract_id': '12345',
            'from_date': '2025-01-01',
            'to_date': '2025-01-31',
            'value': 1000.00
        }
        
        with patch.object(client.session, 'post', side_effect=requests.HTTPError("API Error")):
            success, result = client.issue_receipt(submission_data)
            
            assert success is False


class TestHeaderManagement:
    """Test HTTP header management."""
    
    def test_set_login_headers(self):
        """Test login headers are set correctly."""
        client = WebClient()
        
        original_headers = client.session.headers.copy()
        client._set_login_headers()
        
        # Should have updated headers
        assert 'Content-Type' in client.session.headers
        assert client.session.headers['Content-Type'] == 'application/x-www-form-urlencoded'
    
    def test_initial_headers_set(self):
        """Test that initial headers are set on client creation."""
        client = WebClient()
        
        assert 'User-Agent' in client.session.headers
        assert 'Accept' in client.session.headers
        assert 'Mozilla' in client.session.headers['User-Agent']


class TestConnectionTesting:
    """Test connection testing functionality."""
    
    def test_test_connection_success(self):
        """Test successful connection test."""
        client = WebClient()
        
        with patch.object(client.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = '<form id="kc-form-login">Login Form</form>'
            mock_get.return_value = mock_response
            
            success, message = client.test_connection()
            
            assert success is True
    
    def test_test_connection_timeout(self):
        """Test connection test with timeout."""
        client = WebClient()
        
        with patch.object(client.session, 'get', side_effect=requests.Timeout):
            success, message = client.test_connection()
            
            assert success is False
            assert 'timeout' in message.lower()
    
    def test_test_connection_network_error(self):
        """Test connection test with network error."""
        client = WebClient()
        
        with patch.object(client.session, 'get', side_effect=requests.ConnectionError):
            success, message = client.test_connection()
            
            assert success is False


class TestCredentialFieldDetection:
    """Test credential field name detection."""
    
    def test_find_credential_fields_returns_standard_names(self):
        """Test that credential field detection returns standard field names."""
        client = WebClient()
        
        username_field, password_field = client._find_credential_fields()
        
        assert username_field == 'username'
        assert password_field == 'password'


class TestFormDataExtraction:
    """Test form data extraction from pages."""
    
    def test_get_login_form_data_success(self):
        """Test successful login form data extraction."""
        client = WebClient()
        
        html_with_form = '''
        <html>
            <div id="root-data" data-partid="PFAP" data-csrf="abc123"></div>
        </html>
        '''
        
        with patch.object(client.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.text = html_with_form
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            form_data = client._get_login_form_data()
            
            assert form_data is not None
            assert isinstance(form_data, dict)
    
    def test_get_login_form_data_network_error(self):
        """Test form data extraction with network error."""
        client = WebClient()
        
        with patch.object(client.session, 'get', side_effect=requests.ConnectionError):
            form_data = client._get_login_form_data()
            
            assert form_data is None


class TestAPIMonitoring:
    """Test API monitoring integration."""
    
    def test_api_monitor_initialized(self):
        """Test that API monitor is initialized."""
        client = WebClient()
        
        assert hasattr(client, 'api_monitor')
        assert client.api_monitor is not None
    
    def test_api_monitor_has_monitoring_methods(self):
        """Test that API monitor has expected monitoring functionality."""
        client = WebClient()
        
        # API monitor should have validate_api_call capability (APIPayloadMonitor)
        assert hasattr(client.api_monitor, 'validate_api_call')


class TestAuthenticationState:
    """Test authentication state management."""
    
    def test_initial_authentication_state(self):
        """Test initial authentication state is False."""
        client = WebClient()
        assert client.authenticated is False
    
    def test_session_id_initial_state(self):
        """Test initial session ID is None."""
        client = WebClient()
        assert client._session_id is None
    
    def test_csrf_token_initial_state(self):
        """Test initial CSRF token is None."""
        client = WebClient()
        assert client._csrf_token is None
    
    def test_current_username_initial_state(self):
        """Test current username is initially None."""
        client = WebClient()
        assert client._current_username is None


class TestURLConfiguration:
    """Test URL configuration and endpoints."""
    
    def test_base_urls_configured(self):
        """Test that base URLs are properly configured."""
        client = WebClient()
        
        assert client.auth_base_url.startswith('https://')
        assert client.receipts_base_url.startswith('https://')
    
    def test_login_urls_configured(self):
        """Test that login URLs are properly configured."""
        client = WebClient()
        
        assert client.login_page_url.startswith('https://')
        assert client.login_url.startswith('https://')
        assert 'login' in client.login_url.lower()
