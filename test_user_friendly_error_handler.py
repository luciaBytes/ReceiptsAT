"""
Unit tests for the user-friendly error handling system.
Tests various error scenarios and ensures proper user guidance.
"""

import unittest
from unittest.mock import Mock, patch
import logging

from src.utils.error_handler import (
    UserFriendlyErrorHandler,
    UserFriendlyError,
    ErrorCategory,
    handle_login_error,
    handle_csv_error,
    handle_portal_error
)


class TestUserFriendlyErrorHandler(unittest.TestCase):
    """Test cases for the UserFriendlyErrorHandler class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.handler = UserFriendlyErrorHandler()
        
    def test_authentication_error_handling(self):
        """Test handling of authentication-related errors."""
        # Test credentials error
        error = Exception("Invalid credentials provided")
        result = self.handler.handle_error(error, "login")
        
        self.assertEqual(result.title, "Problema de Login")
        self.assertEqual(result.category, ErrorCategory.AUTHENTICATION)
        self.assertIn("credenciais", result.message.lower())
        self.assertIn("Portal das Finanças", result.action)
        self.assertIsNotNone(result.technical_details)
        
    def test_2fa_error_handling(self):
        """Test handling of two-factor authentication errors."""
        error = Exception("2FA verification required")
        result = self.handler.handle_error(error, "login")
        
        self.assertEqual(result.title, "Autenticação de Dois Fatores Requerida")
        self.assertEqual(result.category, ErrorCategory.AUTHENTICATION)
        self.assertIn("SMS", result.action)
        
    def test_session_expired_error(self):
        """Test handling of session expiration errors."""
        error = Exception("Session expired, please login again")
        result = self.handler.handle_error(error, "receipt_generation")
        
        self.assertEqual(result.title, "Sessão Expirada")
        self.assertEqual(result.category, ErrorCategory.AUTHENTICATION)
        self.assertIn("login", result.action.lower())
        
    def test_network_connection_error(self):
        """Test handling of network connection errors."""
        error = Exception("Connection failed to server")
        result = self.handler.handle_error(error, "portal_access")
        
        self.assertEqual(result.title, "Problema de Ligação")
        self.assertEqual(result.category, ErrorCategory.NETWORK)
        self.assertIn("internet", result.suggestion.lower())
        
    def test_timeout_error(self):
        """Test handling of timeout errors."""
        error = Exception("Request timeout after 30 seconds")
        result = self.handler.handle_error(error, "receipt_download")
        
        self.assertEqual(result.title, "Ligação Muito Lenta")
        self.assertEqual(result.category, ErrorCategory.NETWORK)
        self.assertIn("aguarde", result.action.lower())
        
    def test_csv_format_error(self):
        """Test handling of CSV format errors."""
        error = Exception("CSV format is invalid - missing columns")
        result = self.handler.handle_error(error, "csv_processing")
        
        self.assertEqual(result.title, "Formato CSV Inválido")
        self.assertEqual(result.category, ErrorCategory.DATA_FORMAT)
        self.assertIn("contract_id", result.action)
        self.assertIn("#csv_template", result.help_url)
        
    def test_date_format_error(self):
        """Test handling of date format errors."""
        error = Exception("Date format invalid - expected YYYY-MM-DD")
        result = self.handler.handle_error(error, "date_validation")
        
        self.assertEqual(result.title, "Formato de Data Inválido")
        self.assertEqual(result.category, ErrorCategory.DATA_FORMAT)
        self.assertIn("AAAA-MM-DD", result.suggestion)
        
    def test_contract_not_found_error(self):
        """Test handling of contract not found errors."""
        error = Exception("Contract not found in portal system")
        result = self.handler.handle_error(error, "receipt_generation")
        
        self.assertEqual(result.title, "Contrato Não Encontrado")
        self.assertEqual(result.category, ErrorCategory.PORTAL_INTEGRATION)
        self.assertIn("contract_id", result.action)
        
    def test_receipt_exists_error(self):
        """Test handling of duplicate receipt errors."""
        error = Exception("Receipt already exists for this period")
        result = self.handler.handle_error(error, "receipt_creation")
        
        self.assertEqual(result.title, "Recibo Já Existe")
        self.assertEqual(result.category, ErrorCategory.PORTAL_INTEGRATION)
        self.assertIn("cancele", result.action)
        
    def test_file_not_found_error(self):
        """Test handling of file not found errors."""
        error = Exception("File not found at specified path")
        result = self.handler.handle_error(error, "file_access")
        
        self.assertEqual(result.title, "Ficheiro Não Encontrado")
        self.assertEqual(result.category, ErrorCategory.FILE_SYSTEM)
        self.assertIn("Procurar", result.action)
        
    def test_permission_denied_error(self):
        """Test handling of permission errors."""
        error = Exception("Permission denied - access not allowed")
        result = self.handler.handle_error(error, "file_write")
        
        self.assertEqual(result.title, "Sem Permissões")
        self.assertEqual(result.category, ErrorCategory.FILE_SYSTEM)
        self.assertIn("administrador", result.action)
        
    def test_generic_error_fallback(self):
        """Test handling of unmapped errors with generic fallback."""
        error = Exception("Some completely unknown error occurred")
        result = self.handler.handle_error(error, "unknown_operation")
        
        self.assertEqual(result.title, "Erro Inesperado")
        self.assertEqual(result.category, ErrorCategory.SYSTEM)
        self.assertIn("unknown_operation", result.technical_details)
        self.assertIn("Some completely unknown error occurred", result.technical_details)
        
    def test_format_error_message_basic(self):
        """Test basic error message formatting."""
        error = UserFriendlyError(
            title="Test Error",
            message="Test message",
            suggestion="Test suggestion", 
            action="Test action",
            category=ErrorCategory.VALIDATION
        )
        
        formatted = self.handler.format_error_message(error)
        
        self.assertIn("❌ Test Error", formatted)
        self.assertIn("Problema: Test message", formatted)
        self.assertIn("Sugestão: Test suggestion", formatted)
        self.assertIn("Como resolver:\nTest action", formatted)
        
    def test_format_error_message_with_technical(self):
        """Test error message formatting with technical details."""
        error = UserFriendlyError(
            title="Test Error",
            message="Test message",
            suggestion="Test suggestion",
            action="Test action", 
            category=ErrorCategory.VALIDATION,
            technical_details="Technical error details",
            help_url="https://example.com/help"
        )
        
        formatted = self.handler.format_error_message(error, include_technical=True)
        
        self.assertIn("--- Detalhes Técnicos ---", formatted)
        self.assertIn("Technical error details", formatted)
        self.assertIn("https://example.com/help", formatted)
        
    def test_logging_on_error_handling(self):
        """Test that errors are properly logged."""
        with patch('src.utils.error_handler.logging.getLogger') as mock_logger:
            mock_logger_instance = Mock()
            mock_logger.return_value = mock_logger_instance
            
            handler = UserFriendlyErrorHandler()
            error = Exception("Test error for logging")
            
            result = handler.handle_error(error, "test_context")
            
            # Verify logging was called
            mock_logger_instance.error.assert_called()
            call_args = mock_logger_instance.error.call_args[0]
            self.assertIn("test_context", call_args[0])
            self.assertIn("Test error for logging", call_args[0])


class TestConvenienceFunctions(unittest.TestCase):
    """Test cases for convenience functions."""
    
    def test_handle_login_error(self):
        """Test the handle_login_error convenience function."""
        error = Exception("Invalid credentials")
        result = handle_login_error(error)
        
        self.assertIsInstance(result, UserFriendlyError)
        self.assertEqual(result.category, ErrorCategory.AUTHENTICATION)
        
    def test_handle_csv_error(self):
        """Test the handle_csv_error convenience function."""
        error = Exception("CSV format is invalid - missing columns")
        result = handle_csv_error(error)
        
        self.assertIsInstance(result, UserFriendlyError)
        self.assertEqual(result.category, ErrorCategory.DATA_FORMAT)
        
    def test_handle_portal_error(self):
        """Test the handle_portal_error convenience function."""
        error = Exception("Contract not found")
        result = handle_portal_error(error)
        
        self.assertIsInstance(result, UserFriendlyError)
        self.assertEqual(result.category, ErrorCategory.PORTAL_INTEGRATION)


class TestUserFriendlyError(unittest.TestCase):
    """Test cases for the UserFriendlyError dataclass."""
    
    def test_user_friendly_error_creation(self):
        """Test creating a UserFriendlyError instance."""
        error = UserFriendlyError(
            title="Test Title",
            message="Test message",
            suggestion="Test suggestion",
            action="Test action",
            category=ErrorCategory.VALIDATION
        )
        
        self.assertEqual(error.title, "Test Title")
        self.assertEqual(error.message, "Test message")
        self.assertEqual(error.suggestion, "Test suggestion")
        self.assertEqual(error.action, "Test action")
        self.assertEqual(error.category, ErrorCategory.VALIDATION)
        self.assertIsNone(error.technical_details)
        self.assertIsNone(error.help_url)
        
    def test_user_friendly_error_with_optionals(self):
        """Test creating a UserFriendlyError with optional fields."""
        error = UserFriendlyError(
            title="Test Title",
            message="Test message", 
            suggestion="Test suggestion",
            action="Test action",
            category=ErrorCategory.NETWORK,
            technical_details="Technical info",
            help_url="https://help.example.com"
        )
        
        self.assertEqual(error.technical_details, "Technical info")
        self.assertEqual(error.help_url, "https://help.example.com")


class TestErrorCategory(unittest.TestCase):
    """Test cases for the ErrorCategory enum."""
    
    def test_error_categories(self):
        """Test that all expected error categories exist."""
        categories = [
            ErrorCategory.AUTHENTICATION,
            ErrorCategory.NETWORK,
            ErrorCategory.DATA_FORMAT,
            ErrorCategory.PORTAL_INTEGRATION,
            ErrorCategory.FILE_SYSTEM,
            ErrorCategory.VALIDATION,
            ErrorCategory.SYSTEM
        ]
        
        # Verify all categories have expected values
        self.assertEqual(ErrorCategory.AUTHENTICATION.value, "authentication")
        self.assertEqual(ErrorCategory.NETWORK.value, "network")
        self.assertEqual(ErrorCategory.DATA_FORMAT.value, "data_format")
        self.assertEqual(ErrorCategory.PORTAL_INTEGRATION.value, "portal_integration")
        self.assertEqual(ErrorCategory.FILE_SYSTEM.value, "file_system")
        self.assertEqual(ErrorCategory.VALIDATION.value, "validation")
        self.assertEqual(ErrorCategory.SYSTEM.value, "system")


if __name__ == '__main__':
    # Configure logging for tests
    logging.basicConfig(level=logging.DEBUG)
    
    # Run the tests
    unittest.main(verbosity=2)
