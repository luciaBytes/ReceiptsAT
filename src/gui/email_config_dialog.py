"""
Email Configuration GUI Dialog

Provides a user-friendly interface for configuring email settings,
managing recipients, and sending manual summaries.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
from typing import Dict, List, Any, Optional
import re

try:
    from ..utils.email_summary import EmailSummarySystem, EmailConfig, EmailSummaryConfig
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
    from utils.email_summary import EmailSummarySystem, EmailConfig, EmailSummaryConfig

try:
    from ..utils.logger import get_logger
except ImportError:
    from utils.logger import get_logger

logger = get_logger(__name__)


class EmailConfigDialog:
    """GUI dialog for email configuration and management."""
    
    def __init__(self, parent):
        self.parent = parent
        self.email_system = EmailSummarySystem()
        
        # Create dialog window
        self.window = tk.Toplevel(parent)
        self.window.title("Configuração de Email - Resumos Automáticos")
        self.window.geometry("700x600")
        self.window.transient(parent)
        self.window.grab_set()
        
        # Center the window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (350)
        y = (self.window.winfo_screenheight() // 2) - (300)
        self.window.geometry(f"700x600+{x}+{y}")
        
        self._setup_gui()
        self._load_current_config()
    
    def _setup_gui(self):
        """Setup the GUI components."""
        # Main frame
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="📧 Configuração de Resumos por Email", 
                               font=('TkDefaultFont', 12, 'bold'))
        title_label.grid(row=0, column=0, pady=(0, 10))
        
        # Notebook for different configuration sections
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Create tabs
        self._create_smtp_tab()
        self._create_recipients_tab()
        self._create_schedule_tab()
        self._create_test_tab()
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        ttk.Button(button_frame, text="💾 Guardar Configurações", 
                  command=self._save_config).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="🧪 Testar Email", 
                  command=self._test_email).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="📊 Enviar Resumo Manual", 
                  command=self._send_manual_summary).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Fechar", 
                  command=self.window.destroy).pack(side=tk.RIGHT)
    
    def _create_smtp_tab(self):
        """Create SMTP configuration tab."""
        smtp_frame = ttk.Frame(self.notebook)
        self.notebook.add(smtp_frame, text="📤 Configuração SMTP")
        
        # Create scrollable frame
        canvas = tk.Canvas(smtp_frame)
        scrollbar = ttk.Scrollbar(smtp_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side="right", fill="y", padx=(0, 10), pady=10)
        
        # SMTP configuration fields
        current_row = 0
        
        # Quick setup section
        quick_setup_frame = ttk.LabelFrame(scrollable_frame, text="⚡ Configuração Rápida", padding=10)
        quick_setup_frame.grid(row=current_row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        quick_setup_frame.columnconfigure(1, weight=1)
        
        ttk.Label(quick_setup_frame, text="Tipo de Email:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.email_type_var = tk.StringVar(value="gmail")
        type_combo = ttk.Combobox(quick_setup_frame, textvariable=self.email_type_var, 
                                  values=["gmail", "outlook", "custom"], width=20)
        type_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 0), pady=5)
        type_combo.bind('<<ComboboxSelected>>', self._on_email_type_change)
        
        current_row += 1
        
        # Basic settings
        basic_frame = ttk.LabelFrame(scrollable_frame, text="📋 Configurações Básicas", padding=10)
        basic_frame.grid(row=current_row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        basic_frame.columnconfigure(1, weight=1)
        
        ttk.Label(basic_frame, text="Nome do Remetente:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.from_name_var = tk.StringVar(value="Sistema de Recibos")
        ttk.Entry(basic_frame, textvariable=self.from_name_var, width=40).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 0), pady=5)
        
        ttk.Label(basic_frame, text="Email do Remetente:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.from_email_var = tk.StringVar()
        ttk.Entry(basic_frame, textvariable=self.from_email_var, width=40).grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 0), pady=5)
        
        current_row += 1
        
        # Server settings
        server_frame = ttk.LabelFrame(scrollable_frame, text="🖥️ Configurações do Servidor", padding=10)
        server_frame.grid(row=current_row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        server_frame.columnconfigure(1, weight=1)
        
        ttk.Label(server_frame, text="Servidor SMTP:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.smtp_server_var = tk.StringVar()
        ttk.Entry(server_frame, textvariable=self.smtp_server_var, width=40).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 0), pady=5)
        
        ttk.Label(server_frame, text="Porta:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.smtp_port_var = tk.IntVar(value=587)
        ttk.Spinbox(server_frame, from_=1, to=65535, textvariable=self.smtp_port_var, width=10).grid(row=1, column=1, sticky=tk.W, padx=(5, 0), pady=5)
        
        ttk.Label(server_frame, text="Usar TLS:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.use_tls_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(server_frame, variable=self.use_tls_var).grid(row=2, column=1, sticky=tk.W, padx=(5, 0), pady=5)
        
        current_row += 1
        
        # Authentication settings
        auth_frame = ttk.LabelFrame(scrollable_frame, text="🔐 Autenticação", padding=10)
        auth_frame.grid(row=current_row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        auth_frame.columnconfigure(1, weight=1)
        
        ttk.Label(auth_frame, text="Utilizador:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.username_var = tk.StringVar()
        ttk.Entry(auth_frame, textvariable=self.username_var, width=40).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 0), pady=5)
        
        ttk.Label(auth_frame, text="Palavra-passe:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.password_var = tk.StringVar()
        password_entry = ttk.Entry(auth_frame, textvariable=self.password_var, show="*", width=40)
        password_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 0), pady=5)
        
        # Help text
        help_frame = ttk.LabelFrame(scrollable_frame, text="💡 Ajuda", padding=10)
        help_frame.grid(row=current_row+1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        
        help_text = """Gmail: Use uma palavra-passe de aplicação (não a sua palavra-passe normal)
1. Vá para myaccount.google.com → Segurança
2. Active a verificação em 2 etapas
3. Gere uma palavra-passe de aplicação
4. Use essa palavra-passe aqui

Outlook/Hotmail: Use a sua palavra-passe normal se não tiver 2FA ativo,
caso contrário use uma palavra-passe de aplicação."""
        
        help_label = ttk.Label(help_frame, text=help_text, font=("TkDefaultFont", 8), 
                              justify=tk.LEFT, wraplength=500)
        help_label.pack(anchor=tk.W)
    
    def _create_recipients_tab(self):
        """Create recipients management tab."""
        recipients_frame = ttk.Frame(self.notebook)
        self.notebook.add(recipients_frame, text="👥 Destinatários")
        
        # Recipients management
        ttk.Label(recipients_frame, text="📧 Destinatários dos Resumos", 
                 font=('TkDefaultFont', 11, 'bold')).pack(pady=(10, 15))
        
        # Add recipient frame
        add_frame = ttk.Frame(recipients_frame)
        add_frame.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        ttk.Label(add_frame, text="Adicionar Email:").pack(side=tk.LEFT)
        self.new_recipient_var = tk.StringVar()
        recipient_entry = ttk.Entry(add_frame, textvariable=self.new_recipient_var, width=30)
        recipient_entry.pack(side=tk.LEFT, padx=(10, 5))
        recipient_entry.bind('<Return>', lambda e: self._add_recipient())
        
        ttk.Button(add_frame, text="➕ Adicionar", 
                  command=self._add_recipient).pack(side=tk.LEFT)
        
        # Recipients list
        list_frame = ttk.LabelFrame(recipients_frame, text="Lista de Destinatários", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))
        
        # Create treeview for recipients
        columns = ('Email', 'Status')
        self.recipients_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=10)
        
        self.recipients_tree.heading('Email', text='Endereço de Email')
        self.recipients_tree.heading('Status', text='Status')
        
        self.recipients_tree.column('Email', width=300)
        self.recipients_tree.column('Status', width=100)
        
        # Scrollbar for recipients
        recipients_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.recipients_tree.yview)
        self.recipients_tree.configure(yscrollcommand=recipients_scrollbar.set)
        
        self.recipients_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        recipients_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Recipients buttons
        recipients_button_frame = ttk.Frame(recipients_frame)
        recipients_button_frame.pack(fill=tk.X, padx=20, pady=5)
        
        ttk.Button(recipients_button_frame, text="🗑️ Remover Selecionado", 
                  command=self._remove_recipient).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(recipients_button_frame, text="🔄 Atualizar Lista", 
                  command=self._refresh_recipients).pack(side=tk.LEFT)
    
    def _create_schedule_tab(self):
        """Create schedule configuration tab."""
        schedule_frame = ttk.Frame(self.notebook)
        self.notebook.add(schedule_frame, text="⏰ Agendamento")
        
        # Main settings
        ttk.Label(schedule_frame, text="📅 Configuração de Agendamento", 
                 font=('TkDefaultFont', 11, 'bold')).pack(pady=(10, 15))
        
        # Enable/disable
        enable_frame = ttk.Frame(schedule_frame)
        enable_frame.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        self.summaries_enabled_var = tk.BooleanVar()
        ttk.Checkbutton(enable_frame, text="✅ Ativar resumos automáticos por email", 
                       variable=self.summaries_enabled_var,
                       command=self._on_summaries_toggle).pack(anchor=tk.W)
        
        # Daily summary settings
        daily_frame = ttk.LabelFrame(schedule_frame, text="📊 Resumo Diário", padding=10)
        daily_frame.pack(fill=tk.X, padx=20, pady=(0, 15))
        daily_frame.columnconfigure(1, weight=1)
        
        self.daily_enabled_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(daily_frame, text="Enviar resumo diário", 
                       variable=self.daily_enabled_var).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        ttk.Label(daily_frame, text="Hora de envio:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.send_time_var = tk.IntVar(value=9)
        time_frame = ttk.Frame(daily_frame)
        time_frame.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        ttk.Spinbox(time_frame, from_=0, to=23, textvariable=self.send_time_var, width=5).pack(side=tk.LEFT)
        ttk.Label(time_frame, text="h (formato 24h)").pack(side=tk.LEFT, padx=(5, 0))
        
        # Weekly summary settings
        weekly_frame = ttk.LabelFrame(schedule_frame, text="📈 Resumo Semanal", padding=10)
        weekly_frame.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        self.weekly_enabled_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(weekly_frame, text="Enviar resumo semanal (segundas-feiras)", 
                       variable=self.weekly_enabled_var).pack(anchor=tk.W, pady=5)
        
        # Content settings
        content_frame = ttk.LabelFrame(schedule_frame, text="📋 Conteúdo dos Resumos", padding=10)
        content_frame.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        self.include_statistics_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(content_frame, text="Incluir estatísticas detalhadas", 
                       variable=self.include_statistics_var).pack(anchor=tk.W, pady=2)
        
        self.include_charts_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(content_frame, text="Incluir gráficos (futura implementação)", 
                       variable=self.include_charts_var).pack(anchor=tk.W, pady=2)
        
        self.include_csv_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(content_frame, text="Anexar ficheiro CSV com dados detalhados", 
                       variable=self.include_csv_var).pack(anchor=tk.W, pady=2)
        
        # Status info
        status_frame = ttk.LabelFrame(schedule_frame, text="ℹ️ Estado Atual", padding=10)
        status_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        self.status_text = scrolledtext.ScrolledText(status_frame, height=6, width=60)
        self.status_text.pack(fill=tk.BOTH, expand=True)
    
    def _create_test_tab(self):
        """Create test and logs tab."""
        test_frame = ttk.Frame(self.notebook)
        self.notebook.add(test_frame, text="🧪 Testes e Logs")
        
        # Test section
        test_section = ttk.LabelFrame(test_frame, text="🧪 Teste de Configuração", padding=10)
        test_section.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(test_section, text="Teste a configuração de email enviando um email de verificação.").pack(anchor=tk.W, pady=(0, 10))
        
        test_button_frame = ttk.Frame(test_section)
        test_button_frame.pack(fill=tk.X)
        
        ttk.Button(test_button_frame, text="📤 Enviar Email de Teste", 
                  command=self._test_email).pack(side=tk.LEFT, padx=(0, 10))
        
        self.test_status_label = ttk.Label(test_button_frame, text="", foreground="gray")
        self.test_status_label.pack(side=tk.LEFT)
        
        # Manual summary section
        manual_section = ttk.LabelFrame(test_frame, text="📊 Resumo Manual", padding=10)
        manual_section.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(manual_section, text="Envie um resumo manual para testar o sistema completo.").pack(anchor=tk.W, pady=(0, 10))
        
        manual_frame = ttk.Frame(manual_section)
        manual_frame.pack(fill=tk.X)
        
        ttk.Label(manual_frame, text="Período (dias):").pack(side=tk.LEFT)
        self.manual_days_var = tk.IntVar(value=7)
        ttk.Spinbox(manual_frame, from_=1, to=365, textvariable=self.manual_days_var, width=5).pack(side=tk.LEFT, padx=(5, 10))
        
        ttk.Button(manual_frame, text="📧 Enviar Resumo", 
                  command=self._send_manual_summary).pack(side=tk.LEFT)
        
        # Logs section
        logs_section = ttk.LabelFrame(test_frame, text="📋 Histórico de Emails", padding=10)
        logs_section.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.logs_text = scrolledtext.ScrolledText(logs_section, height=12, width=70)
        self.logs_text.pack(fill=tk.BOTH, expand=True)
        
        # Refresh logs button
        ttk.Button(logs_section, text="🔄 Atualizar Logs", 
                  command=self._refresh_logs).pack(pady=5)
    
    def _on_email_type_change(self, event=None):
        """Handle email type selection change."""
        email_type = self.email_type_var.get()
        
        if email_type == "gmail":
            self.smtp_server_var.set("smtp.gmail.com")
            self.smtp_port_var.set(587)
            self.use_tls_var.set(True)
        elif email_type == "outlook":
            self.smtp_server_var.set("smtp-mail.outlook.com")
            self.smtp_port_var.set(587)
            self.use_tls_var.set(True)
        # For custom, leave fields as they are
    
    def _on_summaries_toggle(self):
        """Handle summaries enabled toggle."""
        # You could enable/disable other controls here
        pass
    
    def _load_current_config(self):
        """Load current configuration into the form."""
        # Load email config
        if self.email_system.email_config:
            config = self.email_system.email_config
            
            self.from_name_var.set(config.from_name)
            self.from_email_var.set(config.from_email)
            self.smtp_server_var.set(config.smtp_server)
            self.smtp_port_var.set(config.smtp_port)
            self.use_tls_var.set(config.use_tls)
            self.username_var.set(config.username)
            self.password_var.set(config.password)
            
            # Determine email type
            if "gmail.com" in config.smtp_server:
                self.email_type_var.set("gmail")
            elif "outlook.com" in config.smtp_server:
                self.email_type_var.set("outlook")
            else:
                self.email_type_var.set("custom")
        
        # Load summary config
        summary_config = self.email_system.summary_config
        
        self.summaries_enabled_var.set(summary_config.enabled)
        self.daily_enabled_var.set(summary_config.daily_summary_enabled)
        self.weekly_enabled_var.set(summary_config.weekly_summary_enabled)
        self.send_time_var.set(summary_config.send_time_hour)
        self.include_statistics_var.set(summary_config.include_statistics)
        self.include_charts_var.set(summary_config.include_charts)
        self.include_csv_var.set(summary_config.include_csv_attachment)
        
        # Refresh other displays
        self._refresh_recipients()
        self._update_status()
        self._refresh_logs()
    
    def _validate_email(self, email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _add_recipient(self):
        """Add a new email recipient."""
        email = self.new_recipient_var.get().strip()
        
        if not email:
            messagebox.showwarning("Aviso", "Por favor, introduza um endereço de email.")
            return
        
        if not self._validate_email(email):
            messagebox.showerror("Erro", "Formato de email inválido.")
            return
        
        if self.email_system.add_recipient(email):
            self.new_recipient_var.set("")
            self._refresh_recipients()
            messagebox.showinfo("Sucesso", f"Email {email} adicionado com sucesso!")
        else:
            messagebox.showwarning("Aviso", f"Email {email} já existe na lista.")
    
    def _remove_recipient(self):
        """Remove selected email recipient."""
        selection = self.recipients_tree.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Por favor, selecione um email para remover.")
            return
        
        item = self.recipients_tree.item(selection[0])
        email = item['values'][0]
        
        result = messagebox.askyesno("Confirmação", f"Remover {email} da lista?")
        if result:
            if self.email_system.remove_recipient(email):
                self._refresh_recipients()
                messagebox.showinfo("Sucesso", f"Email {email} removido com sucesso!")
    
    def _refresh_recipients(self):
        """Refresh the recipients list display."""
        # Clear existing items
        for item in self.recipients_tree.get_children():
            self.recipients_tree.delete(item)
        
        # Add current recipients
        for email in self.email_system.summary_config.recipients:
            self.recipients_tree.insert('', tk.END, values=(email, "Ativo"))
    
    def _save_config(self):
        """Save email configuration."""
        try:
            # Create email config
            email_config = EmailConfig(
                smtp_server=self.smtp_server_var.get(),
                smtp_port=self.smtp_port_var.get(),
                username=self.username_var.get(),
                password=self.password_var.get(),
                use_tls=self.use_tls_var.get(),
                from_name=self.from_name_var.get(),
                from_email=self.from_email_var.get()
            )
            
            # Create summary config
            summary_config = EmailSummaryConfig(
                enabled=self.summaries_enabled_var.get(),
                recipients=self.email_system.summary_config.recipients,  # Keep existing
                daily_summary_enabled=self.daily_enabled_var.get(),
                weekly_summary_enabled=self.weekly_enabled_var.get(),
                send_time_hour=self.send_time_var.get(),
                include_statistics=self.include_statistics_var.get(),
                include_charts=self.include_charts_var.get(),
                include_csv_attachment=self.include_csv_var.get()
            )
            
            # Save configurations
            self.email_system.configure_email(email_config)
            self.email_system.configure_summaries(summary_config)
            
            self._update_status()
            messagebox.showinfo("Sucesso", "Configurações guardadas com sucesso!")
            
        except Exception as e:
            logger.error(f"Error saving email config: {e}")
            messagebox.showerror("Erro", f"Erro ao guardar configurações: {e}")
    
    def _test_email(self):
        """Test email configuration."""
        def run_test():
            try:
                self.test_status_label.config(text="Testando...", foreground="blue")
                self.window.update()
                
                success, message = self.email_system.test_email_configuration()
                
                if success:
                    self.window.after(0, lambda: self.test_status_label.config(text="✅ Sucesso", foreground="green"))
                    self.window.after(0, lambda: messagebox.showinfo("Teste de Email", f"✅ {message}"))
                else:
                    self.window.after(0, lambda: self.test_status_label.config(text="❌ Falha", foreground="red"))
                    self.window.after(0, lambda: messagebox.showerror("Teste de Email", f"❌ {message}"))
                
                self.window.after(0, self._refresh_logs)
                
            except Exception as e:
                self.window.after(0, lambda: self.test_status_label.config(text="❌ Erro", foreground="red"))
                self.window.after(0, lambda: messagebox.showerror("Erro", f"Erro no teste: {e}"))
        
        # Save configuration first
        self._save_config()
        
        # Run test in background thread
        thread = threading.Thread(target=run_test, daemon=True)
        thread.start()
    
    def _send_manual_summary(self):
        """Send manual summary email."""
        def run_send():
            try:
                days = self.manual_days_var.get()
                success = self.email_system.send_custom_summary(days, f"Manual ({days} dias)")
                
                if success:
                    self.window.after(0, lambda: messagebox.showinfo("Resumo Manual", 
                                                                   f"✅ Resumo enviado com sucesso!\nPeríodo: {days} dias"))
                else:
                    self.window.after(0, lambda: messagebox.showerror("Resumo Manual", 
                                                                    "❌ Falha ao enviar resumo.\nVerifique os logs para detalhes."))
                
                self.window.after(0, self._refresh_logs)
                
            except Exception as e:
                self.window.after(0, lambda: messagebox.showerror("Erro", f"Erro ao enviar resumo: {e}"))
        
        # Save configuration first
        self._save_config()
        
        # Run in background thread
        thread = threading.Thread(target=run_send, daemon=True)
        thread.start()
    
    def _update_status(self):
        """Update status information."""
        try:
            email_summary = self.email_system.get_sent_emails_summary(30)
            
            status_text = f"""📊 ESTADO DO SISTEMA DE RESUMOS
{'=' * 50}

🔧 Configuração:
  Email configurado: {'✅ Sim' if self.email_system.email_config else '❌ Não'}
  Destinatários: {len(self.email_system.summary_config.recipients)}
  Resumos ativos: {'✅ Sim' if self.email_system.summary_config.enabled else '❌ Não'}
  Resumo diário: {'✅ Ativo' if self.email_system.summary_config.daily_summary_enabled else '❌ Inativo'}
  Resumo semanal: {'✅ Ativo' if self.email_system.summary_config.weekly_summary_enabled else '❌ Inativo'}

📧 Histórico (últimos 30 dias):
  Emails enviados: {email_summary['total_sent']}
  Bem sucedidos: {email_summary['successful_sent']}
  Falhados: {email_summary['failed_sent']}
  Taxa de sucesso: {email_summary['success_rate']:.1f}%

⏰ Próximo envio:
  Resumo diário: {'Hoje às ' + str(self.email_system.summary_config.send_time_hour) + 'h' if self.email_system.should_send_daily_summary() else 'Não agendado'}
  Resumo semanal: {'Segunda-feira' if self.email_system.should_send_weekly_summary() else 'Não agendado'}
"""
            
            self.status_text.delete(1.0, tk.END)
            self.status_text.insert(1.0, status_text)
            
        except Exception as e:
            logger.error(f"Error updating status: {e}")
            self.status_text.delete(1.0, tk.END)
            self.status_text.insert(1.0, f"Erro ao carregar estado: {e}")
    
    def _refresh_logs(self):
        """Refresh email logs display."""
        try:
            email_summary = self.email_system.get_sent_emails_summary(30)
            
            logs_text = "📧 HISTÓRICO DE EMAILS ENVIADOS\n"
            logs_text += "=" * 50 + "\n\n"
            
            if not email_summary['recent_emails']:
                logs_text += "Nenhum email enviado recentemente.\n"
            else:
                for email_record in reversed(email_summary['recent_emails']):  # Most recent first
                    timestamp = email_record['timestamp'][:19].replace('T', ' ')
                    recipients_count = len(email_record.get('recipients', []))
                    subject = email_record.get('subject', 'N/A')[:60]
                    
                    status_icon = "✅" if email_record.get('success', False) else "❌"
                    
                    logs_text += f"{status_icon} {timestamp}\n"
                    logs_text += f"   Para: {recipients_count} destinatários\n"
                    logs_text += f"   Assunto: {subject}\n"
                    
                    if not email_record.get('success', False) and 'error' in email_record:
                        logs_text += f"   Erro: {email_record['error'][:100]}\n"
                    
                    logs_text += "\n"
            
            self.logs_text.delete(1.0, tk.END)
            self.logs_text.insert(1.0, logs_text)
            
        except Exception as e:
            logger.error(f"Error refreshing logs: {e}")
            self.logs_text.delete(1.0, tk.END)
            self.logs_text.insert(1.0, f"Erro ao carregar logs: {e}")


def show_email_config_dialog(parent):
    """Show the email configuration dialog."""
    try:
        EmailConfigDialog(parent)
    except Exception as e:
        logger.error(f"Error showing email config dialog: {e}")
        messagebox.showerror("Erro", f"Erro ao abrir configuração de email: {e}")


if __name__ == "__main__":
    # Test the dialog
    root = tk.Tk()
    root.withdraw()  # Hide main window
    
    show_email_config_dialog(root)
    root.mainloop()
