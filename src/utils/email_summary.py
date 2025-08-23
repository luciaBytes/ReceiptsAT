"""
Email Summary System for Receipt Processing

Automatically sends summarized reports of issued receipts to configured
email addresses. Provides daily, weekly, and on-demand reporting with
professional formatting and Portuguese localization.

Features:
- Automated daily/weekly email summaries
- Professional HTML formatting with charts
- Multiple recipient management
- Portuguese localization
- Configurable templates and schedules
- Secure SMTP configuration with popular providers
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.utils import formatdate
import json
import os
from datetime import datetime, timedelta, date
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
import csv
import io
import base64
import hashlib

try:
    from .logger import get_logger
except ImportError:
    # Fallback for when imported directly
    from utils.logger import get_logger

# Import receipt database - we'll create a dummy version for testing if not available
try:
    from .receipt_database import ReceiptDatabase, ReceiptRecord
except ImportError:
    try:
        from utils.receipt_database import ReceiptDatabase, ReceiptRecord
    except ImportError:
        # Create minimal dummy classes for testing
        class ReceiptRecord:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)
        
        class ReceiptDatabase:
            def __init__(self):
                pass
            def get_statistics(self):
                return {'total_receipts': 0}
            def search_receipts(self, **kwargs):
                return []

logger = get_logger(__name__)

@dataclass
class EmailConfig:
    """Email configuration settings."""
    smtp_server: str = ""
    smtp_port: int = 587
    username: str = ""
    password: str = ""  # Should be encrypted in production
    use_tls: bool = True
    from_name: str = "Sistema de Recibos"
    from_email: str = ""
    
    # Popular SMTP configurations
    @classmethod
    def gmail_config(cls, email: str, password: str) -> 'EmailConfig':
        return cls(
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            username=email,
            password=password,
            use_tls=True,
            from_name="Sistema de Recibos Portal das Finanças",
            from_email=email
        )
    
    @classmethod
    def outlook_config(cls, email: str, password: str) -> 'EmailConfig':
        return cls(
            smtp_server="smtp-mail.outlook.com",
            smtp_port=587,
            username=email,
            password=password,
            use_tls=True,
            from_name="Sistema de Recibos Portal das Finanças",
            from_email=email
        )

@dataclass
class EmailSummaryConfig:
    """Configuration for email summary system."""
    enabled: bool = False
    recipients: List[str] = None
    daily_summary_enabled: bool = True
    weekly_summary_enabled: bool = True
    send_time_hour: int = 9  # 9 AM
    include_statistics: bool = True
    include_charts: bool = True
    include_csv_attachment: bool = True
    language: str = "pt"  # Portuguese by default
    
    def __post_init__(self):
        if self.recipients is None:
            self.recipients = []

@dataclass
class SummaryData:
    """Data structure for receipt summary."""
    period_start: str
    period_end: str
    total_receipts: int
    successful_receipts: int
    failed_receipts: int
    total_value: float
    unique_contracts: int
    processing_modes: Dict[str, int]
    receipt_types: Dict[str, int]
    daily_counts: List[Tuple[str, int]]  # (date, count) pairs
    recent_failures: List[Dict[str, Any]]
    top_contracts: List[Tuple[str, int, float]]  # (contract_id, count, value)


class EmailSummarySystem:
    """Manages email summaries for receipt processing."""
    
    def __init__(self, data_dir: str = "email_data"):
        self.data_dir = data_dir
        self.config_file = os.path.join(data_dir, "email_config.json")
        self.email_config_file = os.path.join(data_dir, "smtp_config.json")
        self.sent_log_file = os.path.join(data_dir, "sent_emails.json")
        
        # Create data directory
        os.makedirs(data_dir, exist_ok=True)
        
        # Load configurations
        self.summary_config = self._load_summary_config()
        self.email_config = self._load_email_config()
        
        # Load sent email log
        self.sent_emails = self._load_sent_log()
        
        # Initialize database connection
        self.database = ReceiptDatabase()
    
    def _load_summary_config(self) -> EmailSummaryConfig:
        """Load email summary configuration."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return EmailSummaryConfig(**data)
            except Exception as e:
                logger.warning(f"Failed to load summary config: {e}")
        
        # Create default config
        config = EmailSummaryConfig()
        self._save_summary_config(config)
        return config
    
    def _save_summary_config(self, config: EmailSummaryConfig):
        """Save email summary configuration."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(config), f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save summary config: {e}")
    
    def _load_email_config(self) -> Optional[EmailConfig]:
        """Load SMTP email configuration."""
        if os.path.exists(self.email_config_file):
            try:
                with open(self.email_config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return EmailConfig(**data)
            except Exception as e:
                logger.warning(f"Failed to load email config: {e}")
        return None
    
    def _save_email_config(self, config: EmailConfig):
        """Save SMTP email configuration."""
        try:
            with open(self.email_config_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(config), f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save email config: {e}")
    
    def _load_sent_log(self) -> List[Dict[str, Any]]:
        """Load sent email log."""
        if os.path.exists(self.sent_log_file):
            try:
                with open(self.sent_log_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load sent email log: {e}")
        return []
    
    def _save_sent_log(self):
        """Save sent email log."""
        try:
            with open(self.sent_log_file, 'w', encoding='utf-8') as f:
                json.dump(self.sent_emails, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save sent email log: {e}")
    
    def configure_email(self, config: EmailConfig):
        """Configure SMTP email settings."""
        self.email_config = config
        self._save_email_config(config)
        logger.info("Email configuration updated")
    
    def configure_summaries(self, config: EmailSummaryConfig):
        """Configure email summary settings."""
        self.summary_config = config
        self._save_summary_config(config)
        logger.info("Email summary configuration updated")
    
    def add_recipient(self, email: str) -> bool:
        """Add an email recipient."""
        if email and email not in self.summary_config.recipients:
            self.summary_config.recipients.append(email)
            self._save_summary_config(self.summary_config)
            logger.info(f"Added email recipient: {email}")
            return True
        return False
    
    def remove_recipient(self, email: str) -> bool:
        """Remove an email recipient."""
        if email in self.summary_config.recipients:
            self.summary_config.recipients.remove(email)
            self._save_summary_config(self.summary_config)
            logger.info(f"Removed email recipient: {email}")
            return True
        return False
    
    def generate_summary_data(self, days_back: int = 1) -> SummaryData:
        """Generate summary data for the specified period."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Get database statistics for the period
        stats = self.database.get_statistics()
        
        # Get receipts for the period
        receipts = self.database.search_receipts(
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )
        
        # Calculate metrics
        total_receipts = len(receipts)
        successful_receipts = sum(1 for r in receipts if r.status == "Success")
        failed_receipts = sum(1 for r in receipts if r.status == "Failed")
        
        total_value = sum(r.value for r in receipts if r.status == "Success")
        unique_contracts = len(set(r.contract_id for r in receipts))
        
        # Processing modes breakdown
        processing_modes = {}
        for receipt in receipts:
            mode = receipt.processing_mode or "unknown"
            processing_modes[mode] = processing_modes.get(mode, 0) + 1
        
        # Receipt types breakdown
        receipt_types = {}
        for receipt in receipts:
            rtype = receipt.receipt_type or "unknown"
            receipt_types[rtype] = receipt_types.get(rtype, 0) + 1
        
        # Daily counts
        daily_counts = []
        for i in range(days_back):
            day = start_date + timedelta(days=i)
            day_str = day.strftime('%Y-%m-%d')
            day_receipts = [r for r in receipts if r.timestamp.startswith(day_str)]
            daily_counts.append((day_str, len(day_receipts)))
        
        # Recent failures
        recent_failures = []
        for receipt in receipts:
            if receipt.status == "Failed" and receipt.error_message:
                recent_failures.append({
                    'contract_id': receipt.contract_id,
                    'tenant_name': receipt.tenant_name,
                    'error': receipt.error_message[:100],  # Truncate
                    'timestamp': receipt.timestamp
                })
        
        # Top contracts by activity
        contract_stats = {}
        for receipt in receipts:
            if receipt.contract_id not in contract_stats:
                contract_stats[receipt.contract_id] = {'count': 0, 'value': 0.0}
            contract_stats[receipt.contract_id]['count'] += 1
            if receipt.status == "Success":
                contract_stats[receipt.contract_id]['value'] += receipt.value
        
        top_contracts = sorted(
            [(cid, stats['count'], stats['value']) for cid, stats in contract_stats.items()],
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return SummaryData(
            period_start=start_date.strftime('%Y-%m-%d'),
            period_end=end_date.strftime('%Y-%m-%d'),
            total_receipts=total_receipts,
            successful_receipts=successful_receipts,
            failed_receipts=failed_receipts,
            total_value=total_value,
            unique_contracts=unique_contracts,
            processing_modes=processing_modes,
            receipt_types=receipt_types,
            daily_counts=daily_counts,
            recent_failures=recent_failures[-5:],  # Last 5 failures
            top_contracts=top_contracts
        )
    
    def generate_html_summary(self, summary_data: SummaryData, summary_type: str = "daily") -> str:
        """Generate HTML email summary."""
        period_text = {
            "daily": "Diário",
            "weekly": "Semanal", 
            "monthly": "Mensal",
            "custom": "Personalizado"
        }.get(summary_type, "Diário")
        
        # Calculate success rate
        success_rate = 0
        if summary_data.total_receipts > 0:
            success_rate = (summary_data.successful_receipts / summary_data.total_receipts) * 100
        
        # Create HTML content
        html_content = f"""
<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório {period_text} - Recibos Portal das Finanças</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 800px; margin: 0 auto; background-color: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px 10px 0 0; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 24px; }}
        .header p {{ margin: 5px 0 0 0; opacity: 0.9; }}
        .content {{ padding: 30px; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .stat-card {{ background: #f8f9ff; border: 1px solid #e1e5f2; border-radius: 8px; padding: 20px; text-align: center; }}
        .stat-number {{ font-size: 32px; font-weight: bold; color: #667eea; margin-bottom: 5px; }}
        .stat-label {{ color: #666; font-size: 14px; }}
        .section {{ margin-bottom: 30px; }}
        .section h2 {{ color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px; margin-bottom: 15px; }}
        .progress-bar {{ background: #e1e5f2; height: 20px; border-radius: 10px; overflow: hidden; margin: 10px 0; }}
        .progress-fill {{ height: 100%; background: linear-gradient(90deg, #667eea, #764ba2); transition: width 0.3s ease; }}
        .table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        .table th, .table td {{ padding: 12px; text-align: left; border-bottom: 1px solid #eee; }}
        .table th {{ background: #f8f9ff; color: #333; font-weight: 600; }}
        .success {{ color: #28a745; }}
        .error {{ color: #dc3545; }}
        .warning {{ color: #ffc107; }}
        .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; border-top: 1px solid #eee; }}
        .chart-placeholder {{ background: #f8f9ff; border: 2px dashed #667eea; border-radius: 8px; padding: 40px; text-align: center; color: #667eea; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Relatório {period_text} - Recibos</h1>
            <p>Período: {summary_data.period_start} a {summary_data.period_end}</p>
        </div>
        
        <div class="content">
            <!-- Main Statistics -->
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number">{summary_data.total_receipts}</div>
                    <div class="stat-label">Total de Recibos</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number success">{summary_data.successful_receipts}</div>
                    <div class="stat-label">Bem Sucedidos</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number error">{summary_data.failed_receipts}</div>
                    <div class="stat-label">Falharam</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">€{summary_data.total_value:,.2f}</div>
                    <div class="stat-label">Valor Total</div>
                </div>
            </div>
            
            <!-- Success Rate -->
            <div class="section">
                <h2>📈 Taxa de Sucesso</h2>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {success_rate}%"></div>
                </div>
                <p><strong>{success_rate:.1f}%</strong> dos recibos foram processados com sucesso</p>
            </div>
            
            <!-- Contract Summary -->
            <div class="section">
                <h2>🏠 Resumo de Contratos</h2>
                <p><strong>{summary_data.unique_contracts}</strong> contratos únicos processados</p>
                
                {self._generate_top_contracts_table(summary_data.top_contracts)}
            </div>
            
            <!-- Receipt Types -->
            <div class="section">
                <h2>📋 Tipos de Recibos</h2>
                {self._generate_receipt_types_table(summary_data.receipt_types)}
            </div>
            
            <!-- Processing Modes -->
            <div class="section">
                <h2>⚙️ Modos de Processamento</h2>
                {self._generate_processing_modes_table(summary_data.processing_modes)}
            </div>
            
            <!-- Recent Failures -->
            {self._generate_failures_section(summary_data.recent_failures)}
            
            <!-- Daily Activity Chart Placeholder -->
            {self._generate_daily_chart_section(summary_data.daily_counts)}
        </div>
        
        <div class="footer">
            <p>Este relatório foi gerado automaticamente pelo Sistema de Recibos Portal das Finanças</p>
            <p>Data de geração: {datetime.now().strftime('%d/%m/%Y às %H:%M')}</p>
        </div>
    </div>
</body>
</html>
"""
        return html_content
    
    def _generate_top_contracts_table(self, top_contracts: List[Tuple[str, int, float]]) -> str:
        """Generate HTML table for top contracts."""
        if not top_contracts:
            return "<p>Nenhum contrato processado no período.</p>"
        
        table_html = '<table class="table"><thead><tr><th>Contrato</th><th>Recibos</th><th>Valor Total</th></tr></thead><tbody>'
        
        for contract_id, count, value in top_contracts[:5]:  # Top 5
            table_html += f'<tr><td>{contract_id}</td><td>{count}</td><td>€{value:,.2f}</td></tr>'
        
        table_html += '</tbody></table>'
        return table_html
    
    def _generate_receipt_types_table(self, receipt_types: Dict[str, int]) -> str:
        """Generate HTML table for receipt types."""
        if not receipt_types:
            return "<p>Nenhum tipo de recibo identificado.</p>"
        
        # Portuguese type names
        type_names = {
            'rent': 'Renda',
            'utilities': 'Despesas',
            'deposit': 'Caução',
            'maintenance': 'Manutenção',
            'other': 'Outros',
            'unknown': 'Desconhecido'
        }
        
        table_html = '<table class="table"><thead><tr><th>Tipo</th><th>Quantidade</th></tr></thead><tbody>'
        
        for rtype, count in sorted(receipt_types.items(), key=lambda x: x[1], reverse=True):
            type_display = type_names.get(rtype, rtype.capitalize())
            table_html += f'<tr><td>{type_display}</td><td>{count}</td></tr>'
        
        table_html += '</tbody></table>'
        return table_html
    
    def _generate_processing_modes_table(self, processing_modes: Dict[str, int]) -> str:
        """Generate HTML table for processing modes."""
        if not processing_modes:
            return "<p>Nenhum modo de processamento identificado.</p>"
        
        # Portuguese mode names
        mode_names = {
            'bulk': 'Lote Completo',
            'step': 'Passo a Passo',
            'unknown': 'Desconhecido'
        }
        
        table_html = '<table class="table"><thead><tr><th>Modo</th><th>Quantidade</th></tr></thead><tbody>'
        
        for mode, count in sorted(processing_modes.items(), key=lambda x: x[1], reverse=True):
            mode_display = mode_names.get(mode, mode.capitalize())
            table_html += f'<tr><td>{mode_display}</td><td>{count}</td></tr>'
        
        table_html += '</tbody></table>'
        return table_html
    
    def _generate_failures_section(self, recent_failures: List[Dict[str, Any]]) -> str:
        """Generate HTML section for recent failures."""
        if not recent_failures:
            return ""
        
        section_html = '''
            <div class="section">
                <h2>⚠️ Falhas Recentes</h2>
                <table class="table">
                    <thead>
                        <tr><th>Contrato</th><th>Inquilino</th><th>Erro</th><th>Data</th></tr>
                    </thead>
                    <tbody>
        '''
        
        for failure in recent_failures:
            timestamp = failure['timestamp'][:16].replace('T', ' ')
            section_html += f'''
                <tr>
                    <td>{failure['contract_id']}</td>
                    <td>{failure['tenant_name'] or 'N/A'}</td>
                    <td class="error">{failure['error']}</td>
                    <td>{timestamp}</td>
                </tr>
            '''
        
        section_html += '</tbody></table></div>'
        return section_html
    
    def _generate_daily_chart_section(self, daily_counts: List[Tuple[str, int]]) -> str:
        """Generate HTML section for daily activity chart."""
        if not daily_counts:
            return ""
        
        return '''
            <div class="section">
                <h2>📊 Atividade Diária</h2>
                <div class="chart-placeholder">
                    📈 Gráfico de atividade diária<br>
                    <small>(Funcionalidade de gráficos pode ser adicionada com bibliotecas JavaScript)</small>
                </div>
            </div>
        '''
    
    def generate_csv_attachment(self, summary_data: SummaryData) -> bytes:
        """Generate CSV attachment with summary data."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['Relatório de Recibos - Portal das Finanças'])
        writer.writerow([f'Período: {summary_data.period_start} a {summary_data.period_end}'])
        writer.writerow([])
        
        # Summary statistics
        writer.writerow(['Resumo Estatístico'])
        writer.writerow(['Métrica', 'Valor'])
        writer.writerow(['Total de Recibos', summary_data.total_receipts])
        writer.writerow(['Recibos Bem Sucedidos', summary_data.successful_receipts])
        writer.writerow(['Recibos Falhados', summary_data.failed_receipts])
        writer.writerow(['Valor Total', f'€{summary_data.total_value:.2f}'])
        writer.writerow(['Contratos Únicos', summary_data.unique_contracts])
        writer.writerow([])
        
        # Top contracts
        if summary_data.top_contracts:
            writer.writerow(['Top Contratos'])
            writer.writerow(['Contrato', 'Recibos', 'Valor Total'])
            for contract_id, count, value in summary_data.top_contracts:
                writer.writerow([contract_id, count, f'€{value:.2f}'])
            writer.writerow([])
        
        # Receipt types
        if summary_data.receipt_types:
            writer.writerow(['Tipos de Recibos'])
            writer.writerow(['Tipo', 'Quantidade'])
            for rtype, count in summary_data.receipt_types.items():
                writer.writerow([rtype, count])
            writer.writerow([])
        
        # Daily activity
        if summary_data.daily_counts:
            writer.writerow(['Atividade Diária'])
            writer.writerow(['Data', 'Recibos'])
            for date_str, count in summary_data.daily_counts:
                writer.writerow([date_str, count])
        
        # Convert to bytes
        csv_content = output.getvalue()
        output.close()
        return csv_content.encode('utf-8-sig')  # BOM for Excel compatibility
    
    def send_email(self, recipients: List[str], subject: str, html_content: str, 
                   csv_attachment: Optional[bytes] = None) -> bool:
        """Send email with summary."""
        if not self.email_config:
            logger.error("Email configuration not set")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.email_config.from_name} <{self.email_config.from_email}>"
            msg['To'] = ', '.join(recipients)
            msg['Date'] = formatdate(localtime=True)
            
            # Add HTML content
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Add CSV attachment if provided
            if csv_attachment:
                attachment = MIMEApplication(csv_attachment, _subtype='csv')
                attachment.add_header('Content-Disposition', 'attachment', 
                                    filename=f'relatorio_recibos_{datetime.now().strftime("%Y%m%d")}.csv')
                msg.attach(attachment)
            
            # Connect to SMTP server and send
            if self.email_config.use_tls:
                context = ssl.create_default_context()
                with smtplib.SMTP(self.email_config.smtp_server, self.email_config.smtp_port) as server:
                    server.starttls(context=context)
                    server.login(self.email_config.username, self.email_config.password)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(self.email_config.smtp_server, self.email_config.smtp_port) as server:
                    server.login(self.email_config.username, self.email_config.password)
                    server.send_message(msg)
            
            # Log sent email
            sent_record = {
                'timestamp': datetime.now().isoformat(),
                'recipients': recipients,
                'subject': subject,
                'success': True
            }
            self.sent_emails.append(sent_record)
            self._save_sent_log()
            
            logger.info(f"Email sent successfully to {len(recipients)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            
            # Log failed email
            sent_record = {
                'timestamp': datetime.now().isoformat(),
                'recipients': recipients,
                'subject': subject,
                'success': False,
                'error': str(e)
            }
            self.sent_emails.append(sent_record)
            self._save_sent_log()
            
            return False
    
    def send_daily_summary(self) -> bool:
        """Send daily summary email."""
        if not self.summary_config.enabled or not self.summary_config.daily_summary_enabled:
            return False
        
        if not self.summary_config.recipients:
            logger.warning("No email recipients configured")
            return False
        
        try:
            # Generate summary data for yesterday
            summary_data = self.generate_summary_data(days_back=1)
            
            # Check if there's activity to report
            if summary_data.total_receipts == 0:
                logger.info("No receipt activity for daily summary")
                return True  # Not an error, just no activity
            
            # Generate email content
            html_content = self.generate_html_summary(summary_data, "daily")
            subject = f"📊 Relatório Diário de Recibos - {summary_data.period_start}"
            
            # Generate CSV attachment if enabled
            csv_attachment = None
            if self.summary_config.include_csv_attachment:
                csv_attachment = self.generate_csv_attachment(summary_data)
            
            # Send email
            return self.send_email(
                recipients=self.summary_config.recipients,
                subject=subject,
                html_content=html_content,
                csv_attachment=csv_attachment
            )
            
        except Exception as e:
            logger.error(f"Failed to send daily summary: {e}")
            return False
    
    def send_weekly_summary(self) -> bool:
        """Send weekly summary email."""
        if not self.summary_config.enabled or not self.summary_config.weekly_summary_enabled:
            return False
        
        if not self.summary_config.recipients:
            logger.warning("No email recipients configured")
            return False
        
        try:
            # Generate summary data for last week
            summary_data = self.generate_summary_data(days_back=7)
            
            # Check if there's activity to report
            if summary_data.total_receipts == 0:
                logger.info("No receipt activity for weekly summary")
                return True  # Not an error, just no activity
            
            # Generate email content
            html_content = self.generate_html_summary(summary_data, "weekly")
            subject = f"📊 Relatório Semanal de Recibos - {summary_data.period_start} a {summary_data.period_end}"
            
            # Generate CSV attachment if enabled
            csv_attachment = None
            if self.summary_config.include_csv_attachment:
                csv_attachment = self.generate_csv_attachment(summary_data)
            
            # Send email
            return self.send_email(
                recipients=self.summary_config.recipients,
                subject=subject,
                html_content=html_content,
                csv_attachment=csv_attachment
            )
            
        except Exception as e:
            logger.error(f"Failed to send weekly summary: {e}")
            return False
    
    def send_custom_summary(self, days_back: int, summary_title: str = "Personalizado") -> bool:
        """Send custom period summary email."""
        if not self.summary_config.enabled:
            return False
        
        if not self.summary_config.recipients:
            logger.warning("No email recipients configured")
            return False
        
        try:
            # Generate summary data for custom period
            summary_data = self.generate_summary_data(days_back=days_back)
            
            # Generate email content
            html_content = self.generate_html_summary(summary_data, "custom")
            subject = f"📊 Relatório {summary_title} - {summary_data.period_start} a {summary_data.period_end}"
            
            # Generate CSV attachment if enabled
            csv_attachment = None
            if self.summary_config.include_csv_attachment:
                csv_attachment = self.generate_csv_attachment(summary_data)
            
            # Send email
            return self.send_email(
                recipients=self.summary_config.recipients,
                subject=subject,
                html_content=html_content,
                csv_attachment=csv_attachment
            )
            
        except Exception as e:
            logger.error(f"Failed to send custom summary: {e}")
            return False
    
    def test_email_configuration(self) -> Tuple[bool, str]:
        """Test email configuration by sending a test email."""
        if not self.email_config:
            return False, "Configuração de email não definida"
        
        if not self.summary_config.recipients:
            return False, "Nenhum destinatário configurado"
        
        try:
            test_html = """
            <html>
                <body style="font-family: Arial, sans-serif; padding: 20px;">
                    <h2>🧪 Teste de Configuração - Sistema de Recibos</h2>
                    <p>Este é um email de teste para verificar a configuração SMTP.</p>
                    <p><strong>Data:</strong> {timestamp}</p>
                    <p><strong>Status:</strong> ✅ Configuração funcionando corretamente</p>
                    <hr>
                    <small>Sistema de Recibos Portal das Finanças</small>
                </body>
            </html>
            """.format(timestamp=datetime.now().strftime('%d/%m/%Y às %H:%M'))
            
            success = self.send_email(
                recipients=self.summary_config.recipients,
                subject="🧪 Teste - Sistema de Recibos Portal das Finanças",
                html_content=test_html
            )
            
            if success:
                return True, "Email de teste enviado com sucesso"
            else:
                return False, "Falha ao enviar email de teste"
                
        except Exception as e:
            return False, f"Erro no teste: {str(e)}"
    
    def should_send_daily_summary(self) -> bool:
        """Check if daily summary should be sent."""
        if not self.summary_config.enabled or not self.summary_config.daily_summary_enabled:
            return False
        
        # Check if we already sent today's summary
        today = date.today()
        for sent_email in self.sent_emails:
            if sent_email.get('success') and 'Relatório Diário' in sent_email.get('subject', ''):
                try:
                    sent_date = datetime.fromisoformat(sent_email['timestamp']).date()
                    if sent_date == today:
                        return False  # Already sent today
                except ValueError:
                    continue
        
        # Check if it's time to send (based on configured hour)
        current_hour = datetime.now().hour
        return current_hour >= self.summary_config.send_time_hour
    
    def should_send_weekly_summary(self) -> bool:
        """Check if weekly summary should be sent."""
        if not self.summary_config.enabled or not self.summary_config.weekly_summary_enabled:
            return False
        
        # Check if it's Monday and we haven't sent this week's summary
        today = date.today()
        if today.weekday() != 0:  # 0 = Monday
            return False
        
        # Check if we already sent this week's summary
        week_start = today - timedelta(days=today.weekday())
        for sent_email in self.sent_emails:
            if sent_email.get('success') and 'Relatório Semanal' in sent_email.get('subject', ''):
                try:
                    sent_date = datetime.fromisoformat(sent_email['timestamp']).date()
                    if sent_date >= week_start:
                        return False  # Already sent this week
                except ValueError:
                    continue
        
        return True
    
    def get_sent_emails_summary(self, days_back: int = 30) -> Dict[str, Any]:
        """Get summary of sent emails."""
        cutoff_date = datetime.now() - timedelta(days=days_back)
        recent_emails = []
        
        for email in self.sent_emails:
            try:
                sent_date = datetime.fromisoformat(email['timestamp'])
                if sent_date >= cutoff_date:
                    recent_emails.append(email)
            except ValueError:
                continue
        
        total_sent = len(recent_emails)
        successful_sent = sum(1 for email in recent_emails if email.get('success', False))
        failed_sent = total_sent - successful_sent
        
        return {
            'total_sent': total_sent,
            'successful_sent': successful_sent,
            'failed_sent': failed_sent,
            'success_rate': (successful_sent / total_sent * 100) if total_sent > 0 else 0,
            'recent_emails': recent_emails[-10:],  # Last 10 emails
        }


def create_email_system() -> EmailSummarySystem:
    """Create email summary system with default configuration."""
    return EmailSummarySystem()


if __name__ == "__main__":
    # Demo usage
    email_system = create_email_system()
    
    print("📧 Email Summary System Demo")
    print("=" * 40)
    
    # Example: Configure Gmail
    if False:  # Set to True and provide real credentials to test
        gmail_config = EmailConfig.gmail_config("your-email@gmail.com", "your-app-password")
        email_system.configure_email(gmail_config)
        
        # Add recipients
        email_system.add_recipient("recipient@example.com")
        
        # Enable daily summaries
        summary_config = email_system.summary_config
        summary_config.enabled = True
        summary_config.daily_summary_enabled = True
        email_system.configure_summaries(summary_config)
        
        # Send test email
        success, message = email_system.test_email_configuration()
        print(f"Test result: {message}")
        
        # Send manual summary
        if success:
            result = email_system.send_custom_summary(7, "Teste Semanal")
            print(f"Summary sent: {result}")
    
    # Show configuration status
    print(f"Email configured: {email_system.email_config is not None}")
    print(f"Recipients: {len(email_system.summary_config.recipients)}")
    print(f"Daily summaries enabled: {email_system.summary_config.daily_summary_enabled}")
    print(f"Weekly summaries enabled: {email_system.summary_config.weekly_summary_enabled}")
