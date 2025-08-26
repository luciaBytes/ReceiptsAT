"""
Portuguese localization system for complete interface translation.
Provides centralized Portuguese text for all user-facing strings.
"""

from typing import Dict, Any
import logging

# Import the new multilingual system
from .multilingual_localization import get_text as multilingual_get_text, multilingual

logger = logging.getLogger(__name__)


class PortugueseTexts:
    """
    Centralized Portuguese text constants for complete interface localization.
    All user-facing strings should be defined here for consistency.
    (Deprecated - use multilingual_localization instead)
    """
    
    # ==============================================
    # MAIN APPLICATION INTERFACE
    # ==============================================
    
    # Window titles and main interface
    MAIN_WINDOW_TITLE = "Recibos Portal das Financas - Processamento Automatizado"
    APPLICATION_NAME = "Portal das Financas - Recibos"
    
    # Authentication section
    AUTHENTICATION_SECTION = "Autenticacao"
    USERNAME_LABEL = "Utilizador:"
    PASSWORD_LABEL = "Palavra-passe:"
    LOGIN_BUTTON = "Iniciar Sessao"
    LOGOUT_BUTTON = "Terminar Sessao"
    CONNECTION_STATUS_READY = "Pronto para conectar"
    CONNECTION_STATUS_CONNECTING = "A conectar..."
    CONNECTION_STATUS_CONNECTED = "Conectado"
    CONNECTION_STATUS_ERROR = "Erro na conexao"
    SESSION_STATUS_NONE = "Sem sessao ativa"
    SESSION_STATUS_ACTIVE = "Sessao ativa"
    SESSION_STATUS_EXPIRED = "Sessao expirada"
    
    # File selection section
    CSV_FILE_SECTION = "Ficheiro CSV"
    FILE_LABEL = "Ficheiro:"
    BROWSE_BUTTON = "Procurar"
    FILE_NOT_SELECTED = "Nenhum ficheiro selecionado"
    
    # Processing options section
    OPTIONS_SECTION = "Opcoes de Processamento"
    MODE_LABEL = "Modo:"
    BULK_MODE = "Lote Completo"
    STEP_BY_STEP_MODE = "Passo a Passo"
    TESTING_MODE = "Modo de Teste"
    PRODUCTION_MODE = "Modo de Producao"
    
    # Action buttons
    VALIDATE_CONTRACTS_BUTTON = "Validar Contratos"
    PROCESS_RECEIPTS_BUTTON = "Processar Recibos"
    EXPORT_RESULTS_BUTTON = "Exportar Resultados"
    
    # Status and progress
    STATUS_SECTION = "Estado"
    STATUS_READY = "Pronto"
    STATUS_PROCESSING = "A processar..."
    STATUS_COMPLETED = "Concluido"
    STATUS_ERROR = "Erro"
    
    # ==============================================
    # PROGRESS TRACKING INTERFACE
    # ==============================================
    
    PROGRESS_OPERATION_TITLE = "Progresso da Operacao"
    PROGRESS_PROCESSING = "A processar: {current}/{total}"
    PROGRESS_CURRENT_OPERATION = "Atual: {operation}"
    PROGRESS_TIME_REMAINING = "Restam: {time}"
    PROGRESS_OPERATIONS_PER_SECOND = "{rate} ops/s"
    PROGRESS_ESTIMATED_TIME = "Tempo estimado: {time}"
    
    # Progress control buttons
    PAUSE_BUTTON = "Pausar"
    RESUME_BUTTON = "Retomar"
    CANCEL_BUTTON = "Cancelar"
    DETAILS_BUTTON = "Ver Detalhes"
    
    # Progress completion states
    PROGRESS_SUCCESS = "Operacao concluida com sucesso"
    PROGRESS_PARTIAL = "Operacao concluida com alguns erros"
    PROGRESS_FAILED = "Operacao falhada"
    PROGRESS_CANCELLED = "Operacao cancelada"
    
    # ==============================================
    # VALIDATION DIALOG INTERFACE
    # ==============================================
    
    VALIDATION_TITLE = "Resultados da Validacao"
    VALIDATION_SUMMARY = "RESUMO DA VALIDACAO (Apenas Contratos Ativos)"
    VALIDATION_PORTAL_CONTRACTS = "Contratos ativos no portal: {count}"
    VALIDATION_CSV_CONTRACTS = "Contratos no CSV: {count}"
    VALIDATION_VALID_MATCHES = "Correspondencias validas: {count}"
    
    # Validation sections
    VALID_CONTRACTS_SECTION = "CONTRATOS VALIDOS"
    INVALID_CONTRACTS_SECTION = "CONTRATOS INVALIDOS (nao encontrados no portal)"
    MISSING_FROM_CSV_SECTION = "CONTRATOS DO PORTAL NAO INCLUIDOS NO CSV"
    VALIDATION_ISSUES_SECTION = "PROBLEMAS DE VALIDACAO"
    
    # Validation dialog buttons
    OK_BUTTON = "OK"
    EXPORT_REPORT_BUTTON = "Exportar Relatorio"
    
    # ==============================================
    # TWO-FACTOR AUTHENTICATION
    # ==============================================
    
    TWO_FACTOR_TITLE = "Autenticacao de Dois Fatores"
    TWO_FACTOR_MESSAGE = ("Foi enviado um SMS com um codigo de verificacao para o seu "
                         "telefone registado.\nPor favor, introduza o codigo abaixo para "
                         "completar a autenticacao.")
    SMS_CODE_LABEL = "Codigo SMS:"
    VERIFY_BUTTON = "Verificar"
    TWO_FACTOR_HELP = ("Formato do codigo: 6 digitos (ex: 123456)\n"
                      "Se nao receber o SMS, verifique o seu telefone ou tente novamente.")
    
    # ==============================================
    # ERROR MESSAGES AND NOTIFICATIONS
    # ==============================================
    
    # Authentication errors
    ERROR_INVALID_CREDENTIALS = "Credenciais invalidas. Verifique o utilizador e palavra-passe."
    ERROR_CONNECTION_FAILED = "Falha na conexao. Verifique a sua ligacao a internet."
    ERROR_SESSION_EXPIRED = "Sessao expirada. Por favor, inicie sessao novamente."
    ERROR_AUTHENTICATION_FAILED = "Falha na autenticacao. Tente novamente."
    ERROR_TWO_FACTOR_REQUIRED = "Autenticacao de dois fatores necessaria."
    ERROR_TWO_FACTOR_INVALID = "Codigo de dois fatores invalido."
    
    # File errors
    ERROR_FILE_NOT_FOUND = "Ficheiro nao encontrado: {filename}"
    ERROR_FILE_READ_ERROR = "Erro ao ler o ficheiro: {filename}"
    ERROR_INVALID_CSV_FORMAT = "Formato de CSV invalido. Verifique o ficheiro."
    ERROR_EMPTY_CSV_FILE = "Ficheiro CSV vazio ou sem dados validos."
    
    # Processing errors
    ERROR_NO_VALID_CONTRACTS = "Nenhum contrato valido encontrado para processamento."
    ERROR_PROCESSING_FAILED = "Falha no processamento. Verifique os logs para detalhes."
    ERROR_NETWORK_ERROR = "Erro de rede. Verifique a sua conexao."
    ERROR_PORTAL_UNAVAILABLE = "Portal das Financas temporariamente indisponivel."
    
    # ==============================================
    # SUCCESS MESSAGES
    # ==============================================
    
    SUCCESS_LOGIN = "Inicio de sessao bem-sucedido"
    SUCCESS_VALIDATION = "Validacao de contratos concluida"
    SUCCESS_PROCESSING = "Processamento de recibos concluido"
    SUCCESS_EXPORT = "Resultados exportados com sucesso"
    SUCCESS_FILE_LOADED = "Ficheiro carregado com sucesso: {filename}"
    
    # ==============================================
    # DIALOG TITLES AND MESSAGES
    # ==============================================
    
    DIALOG_ERROR_TITLE = "Erro"
    DIALOG_SUCCESS_TITLE = "Sucesso"
    DIALOG_WARNING_TITLE = "Aviso"
    DIALOG_CONFIRMATION_TITLE = "Confirmacao"
    DIALOG_INFORMATION_TITLE = "Informacao"
    
    # File dialogs
    SELECT_CSV_FILE_TITLE = "Selecionar Ficheiro CSV"
    SAVE_EXPORT_FILE_TITLE = "Guardar Ficheiro de Exportacao"
    CSV_FILE_FILTER = "Ficheiros CSV (*.csv)"
    ALL_FILES_FILTER = "Todos os Ficheiros (*.*)"
    
    # ==============================================
    # PROCESSING MESSAGES
    # ==============================================
    
    PROCESSING_LOADING_CONTRACTS = "A carregar contratos do portal..."
    PROCESSING_VALIDATING_CSV = "A validar ficheiro CSV..."
    PROCESSING_GENERATING_RECEIPTS = "A gerar recibos..."
    PROCESSING_SUBMITTING_RECEIPT = "A submeter recibo para {tenant}..."
    PROCESSING_COMPLETED_RECEIPT = "Recibo concluido para {tenant}"
    PROCESSING_FAILED_RECEIPT = "Falha no recibo para {tenant}: {error}"
    
    # ==============================================
    # STEP-BY-STEP MODE INTERFACE
    # ==============================================
    
    STEP_BY_STEP_TITLE = "Processamento Passo a Passo"
    STEP_BY_STEP_QUESTION = "Processar recibo para {tenant}?"
    STEP_BY_STEP_DETAILS = ("Contrato: {contract_id}\n"
                           "Valor: €{amount}\n"
                           "Data: {date}")
    
    STEP_CONFIRM_BUTTON = "Confirmar"
    STEP_EDIT_BUTTON = "Editar"
    STEP_SKIP_BUTTON = "Saltar"
    STEP_CANCEL_BUTTON = "Cancelar Tudo"
    
    # ==============================================
    # VALIDATION RESULTS FORMAT
    # ==============================================
    
    VALIDATION_CONTRACT_FORMAT = "  • {contract_id} → {tenant_name}"
    VALIDATION_CONTRACT_DETAILS = "    €{amount:.2f} - {address} ({status})"
    VALIDATION_ERROR_FORMAT = "  • {error_message}"
    
    # ==============================================
    # TIME AND DATE FORMATTING
    # ==============================================
    
    TIME_SECONDS = "{seconds}s"
    TIME_MINUTES = "{minutes:.1f}m"
    TIME_HOURS = "{hours:.1f}h"
    TIME_DAYS = "{days:.1f}d"
    
    DATE_FORMAT_DD_MM_YYYY = "%d/%m/%Y"
    DATE_FORMAT_YYYY_MM_DD = "%Y-%m-%d"
    
    # ==============================================
    # MENU AND TOOLBAR ITEMS
    # ==============================================
    
    MENU_FILE = "Ficheiro"
    MENU_EDIT = "Editar"
    MENU_VIEW = "Ver"
    MENU_TOOLS = "Ferramentas"
    MENU_HELP = "Ajuda"
    
    MENU_NEW = "Novo"
    MENU_OPEN = "Abrir"
    MENU_SAVE = "Guardar"
    MENU_SAVE_AS = "Guardar Como..."
    MENU_EXIT = "Sair"
    
    MENU_PREFERENCES = "Preferencias"
    MENU_SETTINGS = "Definicoes"
    MENU_ABOUT = "Acerca"
    
    # Status messages
    STATUS_AUTHENTICATED = "Autenticado"
    STATUS_DISCONNECTED = "Desconectado"
    
    # Additional interface elements
    LOG_SECTION = "Registo"
    ACTION_SECTION = "Acao"
    
    # ==============================================
    # HELP AND TOOLTIPS
    # ==============================================
    
    TOOLTIP_LOGIN = "Iniciar sessao no Portal das Financas"
    TOOLTIP_BROWSE_FILE = "Selecionar ficheiro CSV com dados dos contratos"
    TOOLTIP_BULK_MODE = "Processar todos os recibos automaticamente"
    TOOLTIP_STEP_MODE = "Confirmar cada recibo individualmente"
    TOOLTIP_VALIDATE = "Verificar se os contratos no CSV existem no portal"
    TOOLTIP_PROCESS = "Iniciar o processamento dos recibos"
    
    HELP_BULK_MODE = ("Modo de Lote: Processa todos os recibos automaticamente "
                     "sem intervencao do utilizador.")
    HELP_STEP_MODE = ("Modo Passo a Passo: Permite confirmar, editar ou saltar "
                     "cada recibo individualmente.")


class PortugueseLocalizer:
    """
    Portuguese localization manager for dynamic text formatting and substitution.
    """
    
    def __init__(self):
        self.texts = PortugueseTexts()
        logger.info("Sistema de localizacao em portugues inicializado")
    
    def get_text(self, key: str, **kwargs) -> str:
        """
        Get localized text with optional parameter substitution.
        
        Args:
            key: The text key to retrieve
            **kwargs: Parameters for string formatting
            
        Returns:
            Formatted Portuguese text
        """
        try:
            text = getattr(self.texts, key, key)
            if kwargs:
                return text.format(**kwargs)
            return text
        except (AttributeError, KeyError, ValueError) as e:
            logger.warning(f"Falha na localizacao para a chave '{key}': {e}")
            return key  # Return key as fallback
    
    def format_validation_summary(self, validation_report: Dict[str, Any]) -> str:
        """
        Format validation report summary in Portuguese.
        
        Args:
            validation_report: Validation results dictionary
            
        Returns:
            Formatted Portuguese validation summary
        """
        lines = []
        
        # Header
        lines.append(f"📊 {self.texts.VALIDATION_SUMMARY}")
        lines.append(self.get_text('VALIDATION_PORTAL_CONTRACTS', 
                                 count=validation_report['portal_contracts_count']))
        lines.append(self.get_text('VALIDATION_CSV_CONTRACTS',
                                 count=validation_report['csv_contracts_count']))
        lines.append(self.get_text('VALIDATION_VALID_MATCHES',
                                 count=len(validation_report['valid_contracts'])))
        
        # Valid contracts
        if validation_report.get('valid_contracts_data'):
            lines.append(f"\n✅ {self.texts.VALID_CONTRACTS_SECTION}:")
            for contract in validation_report['valid_contracts_data']:
                contract_id = contract.get('numero') or contract.get('referencia', 'N/A')
                tenant_name = contract.get('nomeLocatario', 'Desconhecido')
                rent_amount = contract.get('valorRenda', 0)
                address = contract.get('imovelAlternateId', 'N/A')
                status = contract.get('estado', {}).get('label', 'Desconhecido')
                
                lines.append(self.get_text('VALIDATION_CONTRACT_FORMAT',
                                         contract_id=contract_id, tenant_name=tenant_name))
                lines.append(self.get_text('VALIDATION_CONTRACT_DETAILS',
                                         amount=rent_amount, address=address, status=status))
        
        # Invalid contracts
        if validation_report['invalid_contracts']:
            lines.append(f"\n❌ {self.texts.INVALID_CONTRACTS_SECTION}:")
            for contract in validation_report['invalid_contracts']:
                lines.append(f"  • {contract}")
        
        # Missing from CSV
        if validation_report.get('missing_from_csv_data'):
            lines.append(f"\n⚠️ {self.texts.MISSING_FROM_CSV_SECTION}:")
            for contract in validation_report['missing_from_csv_data']:
                contract_id = contract.get('numero') or contract.get('referencia', 'N/A')
                tenant_name = contract.get('nomeLocatario', 'Desconhecido')
                rent_amount = contract.get('valorRenda', 0)
                address = contract.get('imovelAlternateId', 'N/A')
                
                lines.append(self.get_text('VALIDATION_CONTRACT_FORMAT',
                                         contract_id=contract_id, tenant_name=tenant_name))
                lines.append(self.get_text('VALIDATION_CONTRACT_DETAILS',
                                         amount=rent_amount, address=address, status='Ativo'))
        
        # Validation errors
        if validation_report['validation_errors']:
            lines.append(f"\n🔍 {self.texts.VALIDATION_ISSUES_SECTION}:")
            for error in validation_report['validation_errors']:
                lines.append(f"  • {error}")
        
        return "\n".join(lines)
    
    def format_time_duration(self, seconds: float) -> str:
        """
        Format time duration in Portuguese.
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Formatted time string in Portuguese
        """
        if seconds < 60:
            return self.get_text('TIME_SECONDS', seconds=int(seconds))
        elif seconds < 3600:
            return self.get_text('TIME_MINUTES', minutes=seconds / 60)
        elif seconds < 86400:
            return self.get_text('TIME_HOURS', hours=seconds / 3600)
        else:
            return self.get_text('TIME_DAYS', days=seconds / 86400)
    
    def format_progress_message(self, current: int, total: int, errors: int = 0) -> str:
        """
        Format progress message in Portuguese.
        
        Args:
            current: Current operation count
            total: Total operations
            errors: Error count (optional)
            
        Returns:
            Formatted progress message
        """
        base_message = self.get_text('PROGRESS_PROCESSING', current=current, total=total)
        
        if errors > 0:
            error_text = f" ({errors} erro{'s' if errors != 1 else ''})"
            return base_message + error_text
        
        return base_message


# Global instance for easy access
portuguese = PortugueseLocalizer()


def get_text(key: str, **kwargs) -> str:
    """
    Convenience function to get localized text (multilingual aware).
    
    Args:
        key: Text key to retrieve
        **kwargs: Parameters for string formatting
        
    Returns:
        Formatted text in current language
    """
    return multilingual_get_text(key, **kwargs)


def format_validation_report(validation_report: Dict[str, Any]) -> str:
    """
    Convenience function to format validation reports in Portuguese.
    
    Args:
        validation_report: Validation results dictionary
        
    Returns:
        Formatted Portuguese validation report
    """
    return portuguese.format_validation_summary(validation_report)


def format_time(seconds: float) -> str:
    """
    Convenience function to format time duration in Portuguese.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted time string
    """
    return portuguese.format_time_duration(seconds)


def format_progress(current: int, total: int, errors: int = 0) -> str:
    """
    Convenience function to format progress messages in Portuguese.
    
    Args:
        current: Current operation count
        total: Total operations
        errors: Error count (optional)
        
    Returns:
        Formatted progress message
    """
    return portuguese.format_progress_message(current, total, errors)
