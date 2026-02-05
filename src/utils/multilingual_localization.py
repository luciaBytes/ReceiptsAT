"""
Multilingual localization system for complete interface translation.
Provides centralized text for all user-facing strings in Portuguese and English.
"""

from typing import Dict, Any
import logging
import os
import json


logger = logging.getLogger(__name__)

# Global language setting
_current_language = "pt"  # Default to Portuguese

# Language configuration file path
_config_file = os.path.join(os.path.dirname(__file__), "..", "..", "config", "language.json")

def load_language_preference():
    """Load saved language preference from config file."""
    global _current_language
    try:
        if os.path.exists(_config_file):
            with open(_config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                _current_language = config.get('language', 'pt')
    except Exception as e:
        logger.warning(f"Failed to load language preference: {e}")
        _current_language = "pt"

def save_language_preference(language: str):
    """Save language preference to config file."""
    try:
        os.makedirs(os.path.dirname(_config_file), exist_ok=True)
        config = {'language': language}
        with open(_config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Failed to save language preference: {e}")

def get_current_language():
    """Get the current language setting."""
    return _current_language

def set_language(language: str):
    """Set the current language and save preference."""
    global _current_language
    if language in ["pt", "en"]:
        _current_language = language
        save_language_preference(language)
        logger.info(f"Language changed to: {language}")
        return True
    return False

class MultilingualTexts:
    """
    Centralized text constants for complete interface localization.
    All user-facing strings should be defined here for consistency.
    """
    
    # ==============================================
    # MAIN APPLICATION INTERFACE
    # ==============================================
    
    # Language selector - shows the OTHER language option
    LANGUAGE_BUTTON = {
        "pt": "EN",  # Show "EN" when current language is PT
        "en": "PT"   # Show "PT" when current language is EN  
    }
    
    # Window titles and main interface
    MAIN_WINDOW_TITLE = {
        "pt": "Recibos Portal das Financas - Processamento Automatizado",
        "en": "Portal das Financas Receipts - Automated Processing"
    }
    APPLICATION_NAME = {
        "pt": "Portal das Financas - Recibos",
        "en": "Portal das Financas - Receipts"
    }
    
    # Authentication section
    AUTHENTICATION_SECTION = {
        "pt": "Autenticação",
        "en": "Authentication"
    }
    USERNAME_LABEL = {
        "pt": "Utilizador:",
        "en": "Username:"
    }
    PASSWORD_LABEL = {
        "pt": "Palavra-passe:",
        "en": "Password:"
    }
    LOGIN_BUTTON = {
        "pt": "Iniciar Sessao",
        "en": "Login"
    }
    LOGOUT_BUTTON = {
        "pt": "Terminar Sessao",
        "en": "Logout"
    }
    CONNECTION_STATUS_READY = {
        "pt": "Pronto para conectar",
        "en": "Ready to connect"
    }
    CONNECTION_STATUS_CONNECTING = {
        "pt": "A conectar...",
        "en": "Connecting..."
    }
    CONNECTION_STATUS_CONNECTED = {
        "pt": "Conectado",
        "en": "Connected"
    }
    CONNECTION_STATUS_ERROR = {
        "pt": "Erro na conexao",
        "en": "Connection error"
    }
    SESSION_STATUS_NONE = {
        "pt": "Sem sessão ativa",
        "en": "No active session"
    }
    SESSION_STATUS_ACTIVE = {
        "pt": "Sessão ativa",
        "en": "Active session"
    }
    SESSION_STATUS_EXPIRED = {
        "pt": "Sessão expirada",
        "en": "Session expired"
    }
    
    # File selection section
    CSV_FILE_SECTION = {
        "pt": "Ficheiro CSV",
        "en": "CSV File"
    }
    FILE_LABEL = {
        "pt": "Ficheiro:",
        "en": "File:"
    }
    BROWSE_BUTTON = {
        "pt": "Procurar",
        "en": "Browse"
    }
    FILE_NOT_SELECTED = {
        "pt": "Nenhum ficheiro selecionado",
        "en": "No file selected"
    }
    
    # Processing options section
    OPTIONS_SECTION = {
        "pt": "Opcoes de Processamento",
        "en": "Processing Options"
    }
    MODE_LABEL = {
        "pt": "Modo:",
        "en": "Mode:"
    }
    BULK_MODE = {
        "pt": "Lote Completo",
        "en": "Bulk Mode"
    }
    STEP_BY_STEP_MODE = {
        "pt": "Passo a Passo",
        "en": "Step by Step"
    }
    TESTING_MODE = {
        "pt": "Modo de Teste",
        "en": "Test Mode"
    }
    PRODUCTION_MODE = {
        "pt": "Modo de Producao",
        "en": "Production Mode"
    }
    
    # Action buttons
    VALIDATE_CONTRACTS_BUTTON = {
        "pt": "Mostrar Contratos Válidos",
        "en": "Show Valid Contracts"
    }
    PROCESS_RECEIPTS_BUTTON = {
        "pt": "Processar Recibos",
        "en": "Process Receipts"
    }
    EXPORT_RESULTS_BUTTON = {
        "pt": "Exportar Resultados",
        "en": "Export Results"
    }
    
    # Status and progress
    STATUS_SECTION = {
        "pt": "Estado",
        "en": "Status"
    }
    STATUS_READY = {
        "pt": "Pronto",
        "en": "Ready"
    }
    STATUS_PROCESSING = {
        "pt": "A processar...",
        "en": "Processing..."
    }
    STATUS_COMPLETED = {
        "pt": "Concluido",
        "en": "Completed"
    }
    STATUS_ERROR = {
        "pt": "Erro",
        "en": "Error"
    }

    # CSV Template Generator Interface
    GENERATE_TEMPLATE_BUTTON = {
        "pt": "Gerar Modelo",
        "en": "Generate Template"
    }
    
    # ==============================================
    # SMART IMPORT TAB INTERFACE
    # ==============================================
    
    SMART_IMPORT_TAB = {
        "pt": "Importacao Inteligente",
        "en": "Smart Import"
    }
    QUICK_IMPORT_TAB = {
        "pt": "Importacao Rapida",
        "en": "Quick Import"
    }
    API_MONITOR_TAB = {
        "pt": "Monitor de API",
        "en": "API Monitor"
    }
    
    # ==============================================
    # PROGRESS TRACKING INTERFACE
    # ==============================================
    
    PROGRESS_OPERATION_TITLE = {
        "pt": "Progresso da Operacao",
        "en": "Operation Progress"
    }
    PROGRESS_PROCESSING = {
        "pt": "A processar: {current}/{total}",
        "en": "Processing: {current}/{total}"
    }
    
    # Progress control buttons
    PAUSE_BUTTON = {
        "pt": "Pausar",
        "en": "Pause"
    }
    RESUME_BUTTON = {
        "pt": "Retomar",
        "en": "Resume"
    }
    CANCEL_BUTTON = {
        "pt": "Cancelar",
        "en": "Cancel"
    }
    OK_BUTTON = {
        "pt": "OK",
        "en": "OK"
    }
    VERIFY_BUTTON = {
        "pt": "Verificar",
        "en": "Verify"
    }
    EXPORT_REPORT_BUTTON = {
        "pt": "Exportar Relatorio",
        "en": "Export Report"
    }
    
    # ==============================================
    # VALIDATION DIALOG INTERFACE
    # ==============================================
    
    VALIDATION_TITLE = {
        "pt": "Resultados da Validacao",
        "en": "Validation Results"
    }
    VALIDATION_SUMMARY = {
        "pt": "RESUMO DA VALIDACAO (Apenas Contratos Ativos)\nContratos ativos no portal: {portal_count}\nContratos no CSV: {csv_count}\nCorrespondencias validas: {valid_count}",
        "en": "VALIDATION SUMMARY (Active Contracts Only)\nActive contracts in portal: {portal_count}\nContracts in CSV: {csv_count}\nValid matches: {valid_count}"
    }
    
    # ==============================================
    # FILE DIALOGS
    # ==============================================
    
    SELECT_CSV_FILE_TITLE = {
        "pt": "Selecionar Ficheiro CSV",
        "en": "Select CSV File"
    }
    SAVE_EXPORT_FILE_TITLE = {
        "pt": "Guardar Ficheiro de Exportacao",
        "en": "Save Export File"
    }
    CSV_FILE_FILTER = {
        "pt": "Ficheiros CSV (*.csv)",
        "en": "CSV Files (*.csv)"
    }
    ALL_FILES_FILTER = {
        "pt": "Todos os Ficheiros (*.*)",
        "en": "All Files (*.*)"
    }
    
    # ==============================================
    # DIALOG AND FRAME SECTIONS
    # ==============================================
    
    RECEIPT_INFORMATION_SECTION = {
        "pt": "Informacao do Recibo",
        "en": "Receipt Information"
    }
    
    CONTRACT_INFORMATION_SECTION = {
        "pt": "Informacao do Contrato",
        "en": "Contract Information"
    }
    
    ACTION_SECTION = {
        "pt": "Acao",
        "en": "Action"
    }
    
    LOG_SECTION = {
        "pt": "Registo",
        "en": "Log"
    }
    
    # Help and field labels
    CSV_HELP_TEXT = {
        "pt": "💡 Precisa de ajuda com formato CSV? Use o gerador de template acima",
        "en": "💡 Need help with CSV format? Use the template generator above"
    }
    
    CONTRACT_ID_LABEL = {
        "pt": "ID do Contrato: {id}",
        "en": "Contract ID: {id}"
    }
    
    PERIOD_LABEL = {
        "pt": "Periodo: {from_date} a {to_date}",
        "en": "Period: {from_date} to {to_date}"
    }
    
    PAYMENT_DATE_LABEL = {
        "pt": "Data de Pagamento: {date}",
        "en": "Payment Date: {date}"
    }
    
    PAYMENT_DATE_DEFAULTED_LABEL = {
        "pt": "Data de Pagamento: {date} (predefinida para data final)",
        "en": "Payment Date: {date} (defaulted to end date)"
    }
    
    VALUE_LABEL = {
        "pt": "Valor: €{value:.2f}",
        "en": "Value: €{value:.2f}"
    }
    
    VALUE_DEFAULTED_LABEL = {
        "pt": "Valor: €{value:.2f} (predefinido do contrato)",
        "en": "Value: €{value:.2f} (defaulted from contract)"
    }
    
    VALUE_NOT_SPECIFIED_LABEL = {
        "pt": "Valor: €{value:.2f} (nao especificado no CSV)",
        "en": "Value: €{value:.2f} (not specified in CSV)"
    }
    
    RECEIPT_TYPE_LABEL = {
        "pt": "Tipo de Recibo: {type}",
        "en": "Receipt Type: {type}"
    }
    
    RECEIPT_TYPE_DEFAULTED_LABEL = {
        "pt": "Tipo de Recibo: {type} (predefinido)",
        "en": "Receipt Type: {type} (defaulted)"
    }
    
    # ==============================================
    # DIALOG MESSAGES
    # ==============================================
    
    # Dialog Titles
    ERROR_TITLE = {
        "pt": "Erro",
        "en": "Error"
    }
    
    CONNECTION_FAILED_TITLE = {
        "pt": "Falha de Ligacao",
        "en": "Connection Failed"
    }
    
    LOGIN_FAILED_TITLE = {
        "pt": "Falha no Login",
        "en": "Login Failed"
    }
    
    LOGOUT_FAILED_TITLE = {
        "pt": "Falha no Logout",
        "en": "Logout Failed"
    }
    
    TWO_FA_ERROR_TITLE = {
        "pt": "Erro de 2FA",
        "en": "2FA Error"
    }
    
    TWO_FA_VERIFICATION_FAILED_TITLE = {
        "pt": "Falha na Verificacao 2FA",
        "en": "2FA Verification Failed"
    }
    
    CSV_VALIDATION_FAILED_TITLE = {
        "pt": "Falha na Validacao CSV",
        "en": "CSV Validation Failed"
    }
    
    VALIDATION_ERROR_TITLE = {
        "pt": "Erro de Validacao",
        "en": "Validation Error"
    }
    
    PROCESSING_ERROR_TITLE = {
        "pt": "Erro de Processamento",
        "en": "Processing Error"
    }
    
    PROCESSING_COMPLETE_TITLE = {
        "pt": "Processamento Completo",
        "en": "Processing Complete"
    }
    
    EXPORT_FAILED_TITLE = {
        "pt": "Falha na Exportacao",
        "en": "Export Failed"
    }
    
    EXPORT_SUCCESSFUL_TITLE = {
        "pt": "Exportacao Bem-sucedida",
        "en": "Export Successful"
    }
    
    INFORMATION_TITLE = {
        "pt": "Informacao",
        "en": "Information"
    }
    
    NO_DATA_TITLE = {
        "pt": "Sem Dados",
        "en": "No Data"
    }
    
    # Dialog Messages
    LANGUAGE_SWITCH_FAILED_MESSAGE = {
        "pt": "Falha ao mudar idioma: {error}",
        "en": "Failed to switch language: {error}"
    }
    
    ENTER_USERNAME_PASSWORD_MESSAGE = {
        "pt": "Por favor, introduza o nome de utilizador e palavra-passe",
        "en": "Please enter username and password"
    }
    
    CONNECTION_FAILED_MESSAGE = {
        "pt": "Nao foi possivel ligar ao servidor de autenticacao:\n{error}",
        "en": "Could not connect to authentication server:\n{error}"
    }
    
    SMS_LIMIT_REACHED_MESSAGE = {
        "pt": "Nao ha mais envios de SMS disponiveis. Aguarde ou use autenticacao alternativa.",
        "en": "No more SMS sends available. Wait or use alternative authentication."
    }
    
    # Two-Factor Authentication Dialog
    TWO_FACTOR_TITLE = {
        "pt": "Verificacao SMS",
        "en": "SMS Verification"
    }
    
    TWO_FACTOR_MESSAGE = {
        "pt": "Foi enviado um codigo de verificacao por SMS. Por favor, introduza o codigo de 6 digitos recebido.",
        "en": "A verification code has been sent by SMS. Please enter the 6-digit code received."
    }
    
    SMS_CODE_LABEL = {
        "pt": "Codigo SMS:",
        "en": "SMS Code:"
    }
    
    TWO_FACTOR_HELP = {
        "pt": "Se nao recebeu o SMS, aguarde alguns minutos ou contacte o suporte.",
        "en": "If you didn't receive the SMS, wait a few minutes or contact support."
    }
    
    ENTER_SMS_CODE_MESSAGE = {
        "pt": "Por favor, introduza o codigo de verificacao SMS",
        "en": "Please enter the SMS verification code"
    }
    
    SMS_CODE_SIX_DIGITS_MESSAGE = {
        "pt": "O codigo SMS deve ter 6 digitos",
        "en": "SMS code must be 6 digits"
    }
    
    SMS_VERIFICATION_FAILED_MESSAGE = {
        "pt": "Falha na verificacao SMS:\n{message}",
        "en": "SMS verification failed:\n{message}"
    }
    
    PLEASE_LOGIN_FIRST_MESSAGE = {
        "pt": "Por favor, faca login primeiro",
        "en": "Please login first"
    }
    
    LOAD_VALID_CSV_FIRST_MESSAGE = {
        "pt": "Por favor, carregue primeiro um ficheiro CSV valido",
        "en": "Please load a valid CSV file first"
    }
    
    CONTRACT_VALIDATION_FAILED_MESSAGE = {
        "pt": "Falha na validacao do contrato:\n{error}",
        "en": "Contract validation failed:\n{error}"
    }
    
    NO_VALID_RECEIPTS_MESSAGE = {
        "pt": "Nenhum recibo valido para processar",
        "en": "No valid receipts to process"
    }
    
    NO_PROCESSING_RESULTS_EXPORT_MESSAGE = {
        "pt": "Nenhum resultado de processamento para exportar",
        "en": "No processing results to export"
    }
    
    EXPORT_REPORT_FAILED_MESSAGE = {
        "pt": "Falha ao exportar relatorio",
        "en": "Failed to export report"
    }
    
    REPORT_EXPORTED_TO_MESSAGE = {
        "pt": "Relatorio exportado para:\n{path}",
        "en": "Report exported to:\n{path}"
    }
    
    NO_VALIDATION_RESULTS_EXPORT_MESSAGE = {
        "pt": "Nenhum resultado de validacao para exportar",
        "en": "No validation results to export"
    }

# Initialize language preference on module load
load_language_preference()

class MultilingualLocalizer:
    """
    Multilingual localization manager for dynamic text formatting and substitution.
    """
    
    def __init__(self):
        self.texts = MultilingualTexts()
        logger.info(f"Multilingual localization system initialized - Current language: {_current_language}")
    
    def get_text(self, key: str, **kwargs) -> str:
        """
        Get localized text with optional parameter substitution.
        
        Args:
            key: The text key to retrieve
            **kwargs: Parameters for string formatting
            
        Returns:
            Formatted text in current language
        """
        try:
            text_dict = getattr(self.texts, key, None)
            if isinstance(text_dict, dict):
                text = text_dict.get(_current_language, text_dict.get("pt", key))
            else:
                # Fallback for old single-language strings
                text = text_dict or key
            
            if kwargs:
                return text.format(**kwargs)
            return text
        except (AttributeError, KeyError, ValueError) as e:
            logger.warning(f"Localization failed for key '{key}': {e}")
            return key  # Return key as fallback


# Global instance for easy access
multilingual = MultilingualLocalizer()


def get_text(key: str, **kwargs) -> str:
    """
    Convenience function to get text in current language.
    
    Args:
        key: Text key to retrieve
        **kwargs: Parameters for string formatting
        
    Returns:
        Formatted text in current language
    """
    return multilingual.get_text(key, **kwargs)


def switch_language():
    """
    Switch between Portuguese and English languages.
    
    Returns:
        New language code (pt or en)
    """
    current = get_current_language()
    new_language = "en" if current == "pt" else "pt"
    set_language(new_language)
    return new_language


def get_language_button_text():
    """
    Get the text to show on the language button (the OTHER language).
    
    Returns:
        Button text for switching to the other language
    """
    return get_text('LANGUAGE_BUTTON')
