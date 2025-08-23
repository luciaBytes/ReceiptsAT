"""
Enhanced error handling system for user-friendly error messages.
Provides clear guidance and actionable solutions for common issues.
"""

import logging
import copy
from enum import Enum
from typing import Dict, Optional, Tuple
from dataclasses import dataclass


class ErrorCategory(Enum):
    """Categories of errors for better organization."""
    AUTHENTICATION = "authentication"
    NETWORK = "network"
    DATA_FORMAT = "data_format"
    PORTAL_INTEGRATION = "portal_integration"
    FILE_SYSTEM = "file_system"
    VALIDATION = "validation"
    SYSTEM = "system"


@dataclass
class UserFriendlyError:
    """User-friendly error information with actionable guidance."""
    title: str
    message: str
    suggestion: str
    action: str
    category: ErrorCategory
    technical_details: Optional[str] = None
    help_url: Optional[str] = None


class UserFriendlyErrorHandler:
    """
    Converts technical errors into user-friendly messages with actionable guidance.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Error patterns and their user-friendly translations
        self.error_mappings = {
            # Authentication errors
            "credentials": UserFriendlyError(
                title="Problema de Login",
                message="As suas credenciais não foram aceites pelo Portal das Finanças.",
                suggestion="Verifique o seu nome de utilizador e palavra-passe.",
                action="1. Teste o login manualmente no site do Portal das Finanças\n2. Verifique se tem autenticação de dois fatores ativa\n3. Confirme que a conta não está bloqueada",
                category=ErrorCategory.AUTHENTICATION,
                help_url="https://www.portaldasfinancas.gov.pt"
            ),
            
            "2fa": UserFriendlyError(
                title="Autenticação de Dois Fatores Requerida",
                message="O Portal das Finanças requer autenticação adicional.",
                suggestion="Complete a verificação de dois fatores conforme solicitado.",
                action="1. Verifique o seu telemóvel para código SMS\n2. Use a app de autenticação se configurada\n3. Certifique-se que tem rede móvel/internet",
                category=ErrorCategory.AUTHENTICATION
            ),
            
            "session_expired": UserFriendlyError(
                title="Sessão Expirada",
                message="A sua sessão no Portal das Finanças expirou.",
                suggestion="Faça login novamente para continuar.",
                action="1. Clique em 'Login' para iniciar nova sessão\n2. Se persistir, reinicie a aplicação\n3. Verifique a sua ligação à internet",
                category=ErrorCategory.AUTHENTICATION
            ),
            
            # Network errors
            "connection": UserFriendlyError(
                title="Problema de Ligação",
                message="Não foi possível ligar ao Portal das Finanças.",
                suggestion="Verifique a sua ligação à internet.",
                action="1. Teste a ligação à internet noutras aplicações\n2. Verifique se o Portal das Finanças está acessível no browser\n3. Desative temporariamente firewall/antivírus",
                category=ErrorCategory.NETWORK
            ),
            
            "timeout": UserFriendlyError(
                title="Ligação Muito Lenta",
                message="O Portal das Finanças demorou muito tempo a responder.",
                suggestion="Tente novamente ou verifique a velocidade da internet.",
                action="1. Aguarde alguns minutos e tente novamente\n2. Feche outras aplicações que usem internet\n3. Tente numa hora de menor tráfego",
                category=ErrorCategory.NETWORK
            ),
            
            # Data format errors
            "csv_format": UserFriendlyError(
                title="Formato CSV Inválido",
                message="O ficheiro CSV não tem o formato correto.",
                suggestion="Verifique se as colunas estão corretamente nomeadas.",
                action="1. Use o modelo CSV fornecido pela aplicação\n2. Verifique se tem as colunas: contract_id, tenant_name, amount, from_date, to_date\n3. Use formato de data AAAA-MM-DD",
                category=ErrorCategory.DATA_FORMAT,
                help_url="#csv_template"
            ),
            
            "date_format": UserFriendlyError(
                title="Formato de Data Inválido",
                message="As datas no ficheiro CSV não estão no formato correto.",
                suggestion="Use o formato AAAA-MM-DD para todas as datas.",
                action="1. Exemplo: 2025-01-31 para 31 de Janeiro de 2025\n2. Verifique se todas as datas seguem este formato\n3. Não use barras (/) ou pontos (.)",
                category=ErrorCategory.DATA_FORMAT
            ),
            
            # Portal integration errors
            "contract_not_found": UserFriendlyError(
                title="Contrato Não Encontrado",
                message="O contrato especificado não foi encontrado no Portal das Finanças.",
                suggestion="Verifique o número do contrato e tente novamente.",
                action="1. Confirme o contract_id no Portal das Finanças\n2. Certifique-se que o contrato está ativo\n3. Verifique se tem permissões para este contrato",
                category=ErrorCategory.PORTAL_INTEGRATION
            ),
            
            "receipt_already_exists": UserFriendlyError(
                title="Recibo Já Existe",
                message="Já existe um recibo para este período e contrato.",
                suggestion="Verifique se o recibo já foi emitido anteriormente.",
                action="1. Consulte os recibos já emitidos no Portal das Finanças\n2. Se necessário, cancele o recibo existente primeiro\n3. Ajuste as datas no CSV se apropriado",
                category=ErrorCategory.PORTAL_INTEGRATION
            ),
            
            # File system errors
            "file_not_found": UserFriendlyError(
                title="Ficheiro Não Encontrado",
                message="O ficheiro especificado não foi encontrado.",
                suggestion="Verifique se o caminho do ficheiro está correto.",
                action="1. Confirme que o ficheiro existe na localização indicada\n2. Verifique se tem permissões para aceder ao ficheiro\n3. Use o botão 'Procurar' para selecionar o ficheiro",
                category=ErrorCategory.FILE_SYSTEM
            ),
            
            "permission_denied": UserFriendlyError(
                title="Sem Permissões",
                message="Não tem permissões para aceder ao ficheiro ou pasta.",
                suggestion="Execute a aplicação como administrador ou mude as permissões.",
                action="1. Clique com botão direito na aplicação > 'Executar como administrador'\n2. Ou mova os ficheiros para uma pasta acessível (ex: Documentos)\n3. Verifique se o ficheiro não está aberto noutro programa",
                category=ErrorCategory.FILE_SYSTEM
            )
        }
    
    def handle_error(self, error: Exception, context: str = "") -> UserFriendlyError:
        """
        Convert a technical error into a user-friendly error with guidance.
        
        Args:
            error: The original exception
            context: Additional context about where/when the error occurred
            
        Returns:
            UserFriendlyError with appropriate guidance
        """
        error_str = str(error).lower()
        
        # Define specific error patterns (order matters - most specific first)
        patterns = [
            # Very specific patterns first
            (["2fa", "verification required"], "2fa"),
            (["2fa", "two-factor"], "2fa"),  
            (["mfa"], "2fa"),
            (["session", "expired"], "session_expired"),
            (["contract", "not found"], "contract_not_found"),
            (["receipt", "already", "exists"], "receipt_already_exists"),
            (["csv", "format", "invalid"], "csv_format"),
            (["csv", "missing columns"], "csv_format"),
            (["date", "format", "invalid"], "date_format"),
            (["yyyy-mm-dd"], "date_format"),
            (["permission", "denied"], "permission_denied"),
            (["file", "not found"], "file_not_found"),
            (["request", "timeout"], "timeout"),
            (["connection", "failed"], "connection"),
            
            # More general patterns last
            (["invalid", "credentials"], "credentials"),
            (["authentication"], "credentials"),
            (["timeout"], "timeout"),
            (["connection"], "connection"),
        ]
        
        # Find the first matching pattern
        for keywords, pattern_key in patterns:
            # Check if ALL keywords are present (for precise matching)
            if all(keyword in error_str for keyword in keywords):
                return self._get_mapped_error(pattern_key, error, context)
        
        # Fallback for unmapped errors
        return self._create_generic_error(error, context)
    
    def _get_mapped_error(self, pattern_key: str, error: Exception, context: str) -> UserFriendlyError:
        """Get the mapped error for a pattern key."""
        if pattern_key in self.error_mappings:
            # Make a copy to avoid modifying the original
            friendly_error = copy.deepcopy(self.error_mappings[pattern_key])
            # Log technical details for debugging
            self.logger.error(f"Error in context '{context}': {error}", exc_info=True)
            
            # Add technical details
            friendly_error.technical_details = f"Technical error: {str(error)}"
            return friendly_error
        
        # Should not happen, but fallback
        return self._create_generic_error(error, context)
    
    def _create_generic_error(self, error: Exception, context: str) -> UserFriendlyError:
        """Create a generic user-friendly error for unmapped exceptions."""
        self.logger.error(f"Unmapped error in context '{context}': {error}", exc_info=True)
        
        return UserFriendlyError(
            title="Erro Inesperado",
            message="Ocorreu um erro inesperado durante a operação.",
            suggestion="Tente novamente ou contacte o suporte técnico.",
            action="1. Reinicie a aplicação e tente novamente\n2. Verifique se tem a versão mais recente\n3. Se persistir, contacte o suporte com os detalhes técnicos",
            category=ErrorCategory.SYSTEM,
            technical_details=f"Context: {context}\nError: {str(error)}\nType: {type(error).__name__}"
        )
    
    def format_error_message(self, friendly_error: UserFriendlyError, include_technical: bool = False) -> str:
        """
        Format the error message for display to user.
        
        Args:
            friendly_error: The user-friendly error information
            include_technical: Whether to include technical details
            
        Returns:
            Formatted error message string
        """
        message = f"❌ {friendly_error.title}\n\n"
        message += f"Problema: {friendly_error.message}\n\n"
        message += f"Sugestão: {friendly_error.suggestion}\n\n"
        message += f"Como resolver:\n{friendly_error.action}\n"
        
        if friendly_error.help_url:
            message += f"\nMais informações: {friendly_error.help_url}"
        
        if include_technical and friendly_error.technical_details:
            message += f"\n\n--- Detalhes Técnicos ---\n{friendly_error.technical_details}"
        
        return message


# Convenience functions for common usage patterns
def handle_login_error(error: Exception) -> UserFriendlyError:
    """Quick helper for login-related errors."""
    handler = UserFriendlyErrorHandler()
    return handler.handle_error(error, "login")


def handle_csv_error(error: Exception) -> UserFriendlyError:
    """Quick helper for CSV processing errors."""
    handler = UserFriendlyErrorHandler()
    return handler.handle_error(error, "csv_processing")


def handle_portal_error(error: Exception) -> UserFriendlyError:
    """Quick helper for Portal das Finanças integration errors."""
    handler = UserFriendlyErrorHandler()
    return handler.handle_error(error, "portal_integration")
