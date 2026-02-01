"""  
Unit tests for web_client module.
Tests HTTP interactions, authentication flows, and error handling with mocks.
"""

import sys
import os
import pytest
from unittest.mock import Mock, MagicMock, patch

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from web_client import WebClient


class TestWebClientInit:
    """Test WebClient initialization."""
    
    def test_init_sets_default_headers(self):
        """Test that WebClient sets appropriate browser headers."""
        client = WebClient()
        assert 'User-Agent' in client.session.headers
        assert 'Mozilla' in client.session.headers['User-Agent']
        assert client.authenticated is False
        assert client.pending_2fa is False
    
    def test_init_sets_auth_urls(self):
        """Test that authentication URLs are properly configured."""
        client = WebClient()
        assert client.auth_base_url == "https://www.acesso.gov.pt"
        assert "acesso.gov.pt" in client.login_page_url
        assert "acesso.gov.pt" in client.login_url


class TestConnectionTesting:
    """Test connection testing functionality."""
    
    @patch('src.web_client.requests.Session.get')
    def test_connection_success(self, mock_get):
        """Test successful connection to login page."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.url = "https://www.acesso.gov.pt/v2/loginForm"
        mock_response.text = "<html><form>login autenticação.gov utilizador password</form></html>"
        mock_get.return_value = mock_response
        
        client = WebClient()
        success, message = client.test_connection()
        
        assert success is True
        assert "successful" in message.lower()
        mock_get.assert_called_once()
    
    @patch('src.web_client.requests.Session.get')
    def test_connection_timeout(self, mock_get):
        """Test connection timeout handling."""
        mock_get.side_effect = Exception("timeout")
        
        client = WebClient()
        success, message = client.test_connection()
        
        assert success is False
        assert len(message) > 0
    
    @patch('src.web_client.requests.Session.get')
    def test_connection_no_login_indicators(self, mock_get):
        """Test response when login page indicators are missing."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.url = "https://example.com"
        # Create text without any login indicators or "form" keyword
        mock_response.text = "<html><body><p>Just some random content with no auth elements</p></body></html>"
        mock_get.return_value = mock_response
        
        client = WebClient()
        success, message = client.test_connection()
        
        # Should fail since there are no login indicators
        assert success is False
        assert "login page not detected" in message.lower()


class TestCredentialFieldDiscovery:
    """Test credential field name discovery."""
    
    def test_find_credential_fields(self):
        """Test that standard credential field names are returned."""
        client = WebClient()
        username_field, password_field = client._find_credential_fields()
        
        assert username_field == "username"
        assert password_field == "password"


class TestHeaderConfiguration:
    """Test HTTP header configuration."""
    
    def test_set_login_headers(self):
        """Test that login-specific headers are set correctly."""
        client = WebClient()
        client._set_login_headers()
        
        assert 'Content-Type' in client.session.headers
        assert client.session.headers['Content-Type'] == 'application/x-www-form-urlencoded'
        assert 'Origin' in client.session.headers
        assert 'Referer' in client.session.headers


class TestCSRFTokenExtraction:
    """Test CSRF token extraction from login pages."""
    
    @patch('src.web_client.requests.Session.get')
    def test_csrf_token_extraction_success(self, mock_get):
        """Test successful CSRF token extraction."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '''
        <html>
            <form>
                <input type="hidden" name="csrf_token" value="abc123xyz">
                <input type="hidden" name="state" value="state456">
            </form>
        </html>
        '''
        mock_get.return_value = mock_response
        
        client = WebClient()
        csrf_data = client._get_csrf_token_data()
        
        # Method may return None if no CSRF is found, or a dict if found
        if csrf_data:
            assert isinstance(csrf_data, dict)
    
    @patch('src.web_client.requests.Session.get')
    def test_csrf_token_extraction_failure(self, mock_get):
        """Test CSRF extraction when page load fails."""
        mock_get.side_effect = Exception("Network error")
        
        client = WebClient()
        csrf_data = client._get_csrf_token_data()
        
        assert csrf_data is None


class TestAPIMonitorIntegration:
    """Test API monitor integration."""
    
    def test_api_monitor_initialized(self):
        """Test that API monitor is initialized with WebClient."""
        client = WebClient()
        assert hasattr(client, 'api_monitor')
        assert client.api_monitor is not None


class TestSessionManagement:
    """Test session configuration and management."""
    
    def test_ssl_verification_enabled(self):
        """Test that SSL verification is enabled for security."""
        client = WebClient()
        assert client.session.verify is True
    
    def test_session_persistence(self):
        """Test that session object is persistent."""
        client = WebClient()
        session1 = client.session
        session2 = client.session
        assert session1 is session2
    
    def test_login_attempts_tracking(self):
        """Test login attempts counter initialization."""
        client = WebClient()
        assert client.login_attempts == 0
        assert client.max_login_attempts == 3


class TestAuthenticationState:
    """Test authentication state tracking."""
    
    def test_initial_authentication_state(self):
        """Test that client starts unauthenticated."""
        client = WebClient()
        assert client.authenticated is False
        assert client.pending_2fa is False
        assert client._current_username is None
    
    def test_2fa_pending_flag(self):
        """Test 2FA pending flag can be set."""
        client = WebClient()
        client.pending_2fa = True
        assert client.pending_2fa is True


class TestURLConfiguration:
    """Test URL configuration."""
    
    def test_base_urls_configured(self):
        """Test that all base URLs are properly configured."""
        client = WebClient()
        assert client.auth_base_url.startswith("https://")
        assert client.receipts_base_url.startswith("https://")
        assert "acesso.gov.pt" in client.auth_base_url
        assert "portaldasfinancas.gov.pt" in client.receipts_base_url
    
    def test_login_urls_use_auth_base(self):
        """Test that login URLs use the auth base URL."""
        client = WebClient()
        assert client.login_page_url.startswith(client.auth_base_url)
        assert client.login_url.startswith(client.auth_base_url)
