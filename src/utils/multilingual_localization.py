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
        "pt": "Autenticacao",
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
        "pt": "Sem sessao ativa",
        "en": "No active session"
    }
    SESSION_STATUS_ACTIVE = {
        "pt": "Sessao ativa",
        "en": "Active session"
    }
    SESSION_STATUS_EXPIRED = {
        "pt": "Sessao expirada",
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
        "pt": "Validar Contratos",
        "en": "Validate Contracts"
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
