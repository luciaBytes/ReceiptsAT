"""
Unit tests for the Portuguese localization system.
Tests text retrieval, formatting, and validation report generation.
"""

import unittest
from unittest.mock import patch
from typing import Dict, Any

from src.utils.portuguese_localization import (
    PortugueseTexts,
    PortugueseLocalizer,
    portuguese,
    get_text,
    format_validation_report,
    format_time,
    format_progress
)


class TestPortugueseTexts(unittest.TestCase):
    """Test cases for the PortugueseTexts constants class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.texts = PortugueseTexts()
        
    def test_main_interface_texts(self):
        """Test main interface text constants."""
        self.assertEqual(self.texts.MAIN_WINDOW_TITLE, "Recibos Portal das Financas - Processamento Automatizado")
        self.assertEqual(self.texts.LOGIN_BUTTON, "Iniciar Sessao")
        self.assertEqual(self.texts.LOGOUT_BUTTON, "Terminar Sessao")
        self.assertEqual(self.texts.USERNAME_LABEL, "Utilizador:")
        self.assertEqual(self.texts.PASSWORD_LABEL, "Palavra-passe:")
        
    def test_authentication_texts(self):
        """Test authentication-related text constants."""
        self.assertEqual(self.texts.AUTHENTICATION_SECTION, "Autenticacao")
        self.assertEqual(self.texts.CONNECTION_STATUS_READY, "Pronto para conectar")
        self.assertEqual(self.texts.SESSION_STATUS_NONE, "Sem sessao ativa")
        self.assertEqual(self.texts.SESSION_STATUS_ACTIVE, "Sessao ativa")
        
    def test_file_section_texts(self):
        """Test file section text constants."""
        self.assertEqual(self.texts.CSV_FILE_SECTION, "Ficheiro CSV")
        self.assertEqual(self.texts.FILE_LABEL, "Ficheiro:")
        self.assertEqual(self.texts.BROWSE_BUTTON, "Procurar")
        
    def test_processing_texts(self):
        """Test processing-related text constants."""
        self.assertEqual(self.texts.OPTIONS_SECTION, "Opcoes de Processamento")
        self.assertEqual(self.texts.BULK_MODE, "Lote Completo")
        self.assertEqual(self.texts.STEP_BY_STEP_MODE, "Passo a Passo")
        self.assertEqual(self.texts.PROCESS_RECEIPTS_BUTTON, "Processar Recibos")
        
    def test_progress_texts(self):
        """Test progress tracking text constants."""
        self.assertEqual(self.texts.PROGRESS_OPERATION_TITLE, "Progresso da Operacao")
        self.assertEqual(self.texts.PAUSE_BUTTON, "Pausar")
        self.assertEqual(self.texts.RESUME_BUTTON, "Retomar")
        self.assertEqual(self.texts.CANCEL_BUTTON, "Cancelar")
        
    def test_validation_texts(self):
        """Test validation dialog text constants."""
        self.assertEqual(self.texts.VALIDATION_TITLE, "Resultados da Validacao")
        self.assertEqual(self.texts.VALID_CONTRACTS_SECTION, "CONTRATOS VALIDOS")
        self.assertEqual(self.texts.INVALID_CONTRACTS_SECTION, "CONTRATOS INVALIDOS (nao encontrados no portal)")
        
    def test_error_messages(self):
        """Test error message constants."""
        self.assertEqual(self.texts.ERROR_INVALID_CREDENTIALS, "Credenciais invalidas. Verifique o utilizador e palavra-passe.")
        self.assertEqual(self.texts.ERROR_CONNECTION_FAILED, "Falha na conexao. Verifique a sua ligacao a internet.")
        
    def test_dialog_texts(self):
        """Test dialog-related text constants."""
        self.assertEqual(self.texts.DIALOG_ERROR_TITLE, "Erro")
        self.assertEqual(self.texts.DIALOG_SUCCESS_TITLE, "Sucesso")
        self.assertEqual(self.texts.OK_BUTTON, "OK")


class TestPortugueseLocalizer(unittest.TestCase):
    """Test cases for the PortugueseLocalizer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.localizer = PortugueseLocalizer()
        
    def test_initialization(self):
        """Test localizer initialization."""
        self.assertIsNotNone(self.localizer.texts)
        self.assertIsInstance(self.localizer.texts, PortugueseTexts)
        
    def test_get_text_basic(self):
        """Test basic text retrieval."""
        text = self.localizer.get_text('LOGIN_BUTTON')
        self.assertEqual(text, "Iniciar Sessao")
        
    def test_get_text_with_formatting(self):
        """Test text retrieval with parameter substitution."""
        text = self.localizer.get_text('PROGRESS_PROCESSING', current=5, total=10)
        self.assertEqual(text, "A processar: 5/10")
        
    def test_get_text_missing_key(self):
        """Test handling of missing text keys."""
        text = self.localizer.get_text('NONEXISTENT_KEY')
        self.assertEqual(text, 'NONEXISTENT_KEY')  # Should return key as fallback
        
    def test_get_text_formatting_error(self):
        """Test handling of formatting errors."""
        # Try to format a non-formatted string with parameters
        text = self.localizer.get_text('LOGIN_BUTTON', invalid_param="test")
        self.assertEqual(text, "Iniciar Sessao")  # Should return text without formatting
        
    def test_format_time_duration(self):
        """Test time duration formatting."""
        # Test seconds
        time_str = self.localizer.format_time_duration(45)
        self.assertEqual(time_str, "45s")
        
        # Test minutes
        time_str = self.localizer.format_time_duration(90)
        self.assertEqual(time_str, "1.5m")
        
        # Test hours
        time_str = self.localizer.format_time_duration(7200)
        self.assertEqual(time_str, "2.0h")
        
        # Test days
        time_str = self.localizer.format_time_duration(172800)
        self.assertEqual(time_str, "2.0d")
        
    def test_format_progress_message(self):
        """Test progress message formatting."""
        # Without errors
        message = self.localizer.format_progress_message(5, 10)
        self.assertEqual(message, "A processar: 5/10")
        
        # With single error
        message = self.localizer.format_progress_message(5, 10, 1)
        self.assertEqual(message, "A processar: 5/10 (1 erro)")
        
        # With multiple errors
        message = self.localizer.format_progress_message(5, 10, 3)
        self.assertEqual(message, "A processar: 5/10 (3 erros)")
        
    def test_format_validation_summary(self):
        """Test validation report formatting."""
        validation_report = {
            'portal_contracts_count': 5,
            'csv_contracts_count': 3,
            'valid_contracts': ['C001', 'C002'],
            'invalid_contracts': ['C999'],
            'validation_errors': ['Invalid date format'],
            'valid_contracts_data': [
                {
                    'numero': 'C001',
                    'nomeLocatario': 'João Silva',
                    'valorRenda': 500.0,
                    'imovelAlternateId': 'Lisboa, Rua A',
                    'estado': {'label': 'Ativo'}
                }
            ],
            'missing_from_csv_data': [
                {
                    'numero': 'C003',
                    'nomeLocatario': 'Maria Santos',
                    'valorRenda': 600.0,
                    'imovelAlternateId': 'Porto, Rua B'
                }
            ]
        }
        
        summary = self.localizer.format_validation_summary(validation_report)
        
        # Check that the summary contains expected Portuguese text
        self.assertIn("RESUMO DA VALIDACAO", summary)
        self.assertIn("Contratos ativos no portal: 5", summary)
        self.assertIn("Contratos no CSV: 3", summary)
        self.assertIn("Correspondencias validas: 2", summary)
        self.assertIn("CONTRATOS VALIDOS", summary)
        self.assertIn("CONTRATOS INVALIDOS", summary)
        self.assertIn("CONTRATOS DO PORTAL NAO INCLUIDOS NO CSV", summary)
        self.assertIn("PROBLEMAS DE VALIDACAO", summary)
        self.assertIn("João Silva", summary)
        self.assertIn("Maria Santos", summary)


class TestConvenienceFunctions(unittest.TestCase):
    """Test cases for the convenience functions."""
    
    def test_get_text_function(self):
        """Test the get_text convenience function."""
        text = get_text('LOGIN_BUTTON')
        self.assertEqual(text, "Iniciar Sessao")
        
    def test_get_text_with_params(self):
        """Test get_text with parameters."""
        text = get_text('PROGRESS_PROCESSING', current=3, total=7)
        self.assertEqual(text, "A processar: 3/7")
        
    def test_format_time_function(self):
        """Test the format_time convenience function."""
        time_str = format_time(120)
        self.assertEqual(time_str, "2.0m")
        
    def test_format_progress_function(self):
        """Test the format_progress convenience function."""
        message = format_progress(8, 10, 1)
        self.assertEqual(message, "A processar: 8/10 (1 erro)")
        
    def test_format_validation_report_function(self):
        """Test the format_validation_report convenience function."""
        validation_report = {
            'portal_contracts_count': 2,
            'csv_contracts_count': 1,
            'valid_contracts': ['C001'],
            'invalid_contracts': [],
            'validation_errors': [],
            'valid_contracts_data': [],
            'missing_from_csv_data': []
        }
        
        summary = format_validation_report(validation_report)
        self.assertIn("RESUMO DA VALIDACAO", summary)
        self.assertIn("Contratos ativos no portal: 2", summary)


class TestGlobalInstance(unittest.TestCase):
    """Test cases for the global portuguese instance."""
    
    def test_global_instance_exists(self):
        """Test that the global portuguese instance exists."""
        self.assertIsNotNone(portuguese)
        self.assertIsInstance(portuguese, PortugueseLocalizer)
        
    def test_global_instance_functionality(self):
        """Test that the global instance works correctly."""
        text = portuguese.get_text('AUTHENTICATION_SECTION')
        self.assertEqual(text, "Autenticacao")
        
    def test_consistent_results(self):
        """Test that multiple calls return consistent results."""
        text1 = get_text('BROWSE_BUTTON')
        text2 = get_text('BROWSE_BUTTON')
        self.assertEqual(text1, text2)
        self.assertEqual(text1, "Procurar")


class TestEdgeCases(unittest.TestCase):
    """Test cases for edge cases and error conditions."""
    
    def test_empty_validation_report(self):
        """Test formatting empty validation report."""
        empty_report = {
            'portal_contracts_count': 0,
            'csv_contracts_count': 0,
            'valid_contracts': [],
            'invalid_contracts': [],
            'validation_errors': [],
            'valid_contracts_data': [],
            'missing_from_csv_data': []
        }
        
        summary = format_validation_report(empty_report)
        self.assertIn("RESUMO DA VALIDACAO", summary)
        self.assertIn("Contratos ativos no portal: 0", summary)
        self.assertIn("Correspondencias validas: 0", summary)
        
    def test_zero_time_formatting(self):
        """Test formatting zero time duration."""
        time_str = format_time(0)
        self.assertEqual(time_str, "0s")
        
    def test_zero_progress_formatting(self):
        """Test formatting zero progress."""
        message = format_progress(0, 0)
        self.assertEqual(message, "A processar: 0/0")
        
    def test_missing_contract_data(self):
        """Test handling missing contract data fields."""
        validation_report = {
            'portal_contracts_count': 1,
            'csv_contracts_count': 1,
            'valid_contracts': ['C001'],
            'invalid_contracts': [],
            'validation_errors': [],
            'valid_contracts_data': [
                {
                    # Missing some fields to test fallbacks
                    'numero': 'C001'
                    # nomeLocatario, valorRenda, etc. missing
                }
            ],
            'missing_from_csv_data': []
        }
        
        summary = format_validation_report(validation_report)
        self.assertIn("CONTRATOS VALIDOS", summary)
        self.assertIn("Desconhecido", summary)  # Should use fallback for missing tenant name


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)
