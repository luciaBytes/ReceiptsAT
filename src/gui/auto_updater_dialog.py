"""
Auto-updater GUI Dialog

Provides a comprehensive interface for managing automatic updates,
viewing update history, configuring settings, and performing manual
operations like backup and rollback.

Features:
- Update availability notifications with detailed information
- Download progress tracking with cancellation support
- Backup management and rollback functionality
- Update scheduling and configuration options
- Portuguese localization for all user-facing text
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

try:
    from ..utils.auto_updater import AutoUpdater, UpdateInfo
    from ..utils.logger import get_logger
except ImportError:
    # Fallback for when imported directly
    try:
        from utils.auto_updater import AutoUpdater, UpdateInfo
        from utils.logger import get_logger
    except ImportError:
        logging.basicConfig(level=logging.INFO)
        def get_logger(name):
            return logging.getLogger(name)
        # Create dummy classes for testing
        class AutoUpdater:
            def __init__(self): pass
            def check_for_updates(self): return None
            def get_update_summary(self): return {}
        class UpdateInfo:
            def __init__(self): pass

logger = get_logger(__name__)


class AutoUpdaterDialog:
    """GUI dialog for auto-updater management."""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.root = tk.Toplevel(parent) if parent else tk.Tk()
        
        # Initialize auto-updater
        self.updater = AutoUpdater()
        self.updater.set_update_callback(self._handle_update_callback)
        
        # State variables
        self.current_update = None
        self.download_progress = 0
        self.checking_updates = False
        
        # Setup UI
        self._setup_window()
        self._create_widgets()
        self._load_current_status()
        
        # Start background checking if enabled
        if self.updater.config.enabled:
            self.updater.start_background_checking()
    
    def _setup_window(self):
        """Configure the main window."""
        self.root.title("🔄 Auto-updater - Portal de Recibos")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        # Center on parent or screen
        if self.parent:
            self.root.transient(self.parent)
            self.root.grab_set()
            
            # Center on parent
            parent_x = self.parent.winfo_x()
            parent_y = self.parent.winfo_y()
            parent_width = self.parent.winfo_width()
            parent_height = self.parent.winfo_height()
            
            x = parent_x + (parent_width - 800) // 2
            y = parent_y + (parent_height - 700) // 2
            
            self.root.geometry(f"800x700+{x}+{y}")
        
        # Configure styles
        style = ttk.Style()
        if style.theme_use() == 'default':
            style.theme_use('clam')
    
    def _create_widgets(self):
        """Create all GUI widgets."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Header
        self._create_header(main_frame)
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        
        # Create tabs
        self._create_status_tab()
        self._create_updates_tab()
        self._create_backups_tab()
        self._create_settings_tab()
        
        # Button frame
        self._create_button_frame(main_frame)
    
    def _create_header(self, parent):
        """Create header section."""
        header_frame = ttk.Frame(parent)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        header_frame.columnconfigure(1, weight=1)
        
        # Icon and title
        title_label = ttk.Label(header_frame, text="🔄 Sistema de Atualizações Automáticas",
                               font=('Segoe UI', 14, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, sticky=tk.W)
        
        # Version info
        version_text = f"Versão Atual: {self.updater.current_version}"
        self.version_label = ttk.Label(header_frame, text=version_text,
                                      font=('Segoe UI', 9))
        self.version_label.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        
        # Status indicator
        self.status_label = ttk.Label(header_frame, text="Verificando...",
                                     font=('Segoe UI', 9))
        self.status_label.grid(row=1, column=1, sticky=tk.E, pady=(5, 0))
    
    def _create_status_tab(self):
        """Create status overview tab."""
        frame = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(frame, text="📊 Status")
        
        # Current version section
        version_frame = ttk.LabelFrame(frame, text="Informação da Versão", padding="10")
        version_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        
        ttk.Label(version_frame, text="Versão Atual:").grid(row=0, column=0, sticky=tk.W)
        self.current_version_var = tk.StringVar(value=self.updater.current_version)
        ttk.Label(version_frame, textvariable=self.current_version_var,
                 font=('Segoe UI', 9, 'bold')).grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(version_frame, text="Versão Disponível:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.available_version_var = tk.StringVar(value="Verificando...")
        ttk.Label(version_frame, textvariable=self.available_version_var,
                 font=('Segoe UI', 9, 'bold')).grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=(5, 0))
        
        # Update status section
        status_frame = ttk.LabelFrame(frame, text="Estado das Atualizações", padding="10")
        status_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.update_status_text = scrolledtext.ScrolledText(status_frame, height=8, width=70,
                                                          font=('Segoe UI', 9), state=tk.DISABLED)
        self.update_status_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        status_frame.columnconfigure(0, weight=1)
        status_frame.rowconfigure(0, weight=1)
        
        # Check info section
        check_frame = ttk.LabelFrame(frame, text="Verificação Automática", padding="10")
        check_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        ttk.Label(check_frame, text="Última Verificação:").grid(row=0, column=0, sticky=tk.W)
        self.last_check_var = tk.StringVar(value="Nunca")
        ttk.Label(check_frame, textvariable=self.last_check_var).grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(check_frame, text="Próxima Verificação:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.next_check_var = tk.StringVar(value="Não agendada")
        ttk.Label(check_frame, textvariable=self.next_check_var).grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=(5, 0))
    
    def _create_updates_tab(self):
        """Create updates management tab."""
        frame = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(frame, text="🔄 Atualizações")
        
        # Check for updates section
        check_frame = ttk.LabelFrame(frame, text="Verificar Atualizações", padding="10")
        check_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        frame.columnconfigure(0, weight=1)
        
        # Manual check button
        self.check_button = ttk.Button(check_frame, text="🔍 Verificar Agora",
                                      command=self._check_updates_manual)
        self.check_button.grid(row=0, column=0, padx=(0, 10))
        
        # Auto-check status
        self.auto_check_var = tk.BooleanVar(value=self.updater.config.enabled)
        auto_check_cb = ttk.Checkbutton(check_frame, text="Verificação Automática Ativada",
                                       variable=self.auto_check_var,
                                       command=self._toggle_auto_check)
        auto_check_cb.grid(row=0, column=1)
        
        # Update info section
        info_frame = ttk.LabelFrame(frame, text="Informação da Atualização", padding="10")
        info_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.update_info_text = scrolledtext.ScrolledText(info_frame, height=12, width=70,
                                                         font=('Segoe UI', 9), state=tk.DISABLED)
        self.update_info_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        info_frame.columnconfigure(0, weight=1)
        info_frame.rowconfigure(0, weight=1)
        
        # Download progress section
        progress_frame = ttk.LabelFrame(frame, text="Progresso do Download", padding="10")
        progress_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var,
                                          maximum=100, length=400)
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress_label = ttk.Label(progress_frame, text="Pronto")
        self.progress_label.grid(row=0, column=1)
        
        # Action buttons
        action_frame = ttk.Frame(frame)
        action_frame.grid(row=3, column=0, sticky=(tk.W, tk.E))
        
        self.download_button = ttk.Button(action_frame, text="⬇️ Fazer Download",
                                         command=self._download_update, state=tk.DISABLED)
        self.download_button.grid(row=0, column=0, padx=(0, 10))
        
        self.install_button = ttk.Button(action_frame, text="🔧 Instalar Atualização",
                                        command=self._install_update, state=tk.DISABLED)
        self.install_button.grid(row=0, column=1, padx=(0, 10))
        
        self.cancel_button = ttk.Button(action_frame, text="❌ Cancelar",
                                       command=self._cancel_operation, state=tk.DISABLED)
        self.cancel_button.grid(row=0, column=2)
    
    def _create_backups_tab(self):
        """Create backup management tab."""
        frame = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(frame, text="💾 Backups")
        
        # Backup list section
        list_frame = ttk.LabelFrame(frame, text="Backups Disponíveis", padding="10")
        list_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        
        # Treeview for backups
        self.backup_tree = ttk.Treeview(list_frame, columns=('version', 'date', 'size'),
                                       show='tree headings', height=10)
        self.backup_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # Configure columns
        self.backup_tree.heading('#0', text='Arquivo')
        self.backup_tree.heading('version', text='Versão')
        self.backup_tree.heading('date', text='Data')
        self.backup_tree.heading('size', text='Tamanho')
        
        self.backup_tree.column('#0', width=200)
        self.backup_tree.column('version', width=100)
        self.backup_tree.column('date', width=150)
        self.backup_tree.column('size', width=100)
        
        # Scrollbar for treeview
        backup_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL,
                                     command=self.backup_tree.yview)
        backup_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.backup_tree.configure(yscrollcommand=backup_scroll.set)
        
        # Backup actions
        backup_actions_frame = ttk.Frame(frame)
        backup_actions_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        self.create_backup_button = ttk.Button(backup_actions_frame, text="💾 Criar Backup",
                                              command=self._create_backup)
        self.create_backup_button.grid(row=0, column=0, padx=(0, 10))
        
        self.restore_backup_button = ttk.Button(backup_actions_frame, text="🔄 Restaurar",
                                               command=self._restore_backup, state=tk.DISABLED)
        self.restore_backup_button.grid(row=0, column=1, padx=(0, 10))
        
        self.delete_backup_button = ttk.Button(backup_actions_frame, text="🗑️ Eliminar",
                                              command=self._delete_backup, state=tk.DISABLED)
        self.delete_backup_button.grid(row=0, column=2)
        
        # Bind selection event
        self.backup_tree.bind('<<TreeviewSelect>>', self._on_backup_select)
        
        # Load backups
        self._load_backups()
    
    def _create_settings_tab(self):
        """Create settings configuration tab."""
        frame = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(frame, text="⚙️ Configurações")
        
        # Update checking settings
        check_settings_frame = ttk.LabelFrame(frame, text="Verificação de Atualizações", padding="10")
        check_settings_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        frame.columnconfigure(0, weight=1)
        
        # Enable auto-check
        self.enable_auto_var = tk.BooleanVar(value=self.updater.config.enabled)
        ttk.Checkbutton(check_settings_frame, text="Ativar verificação automática de atualizações",
                       variable=self.enable_auto_var).grid(row=0, column=0, columnspan=2, sticky=tk.W)
        
        # Check interval
        ttk.Label(check_settings_frame, text="Intervalo de verificação (horas):").grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
        self.check_interval_var = tk.StringVar(value=str(self.updater.config.check_interval_hours))
        interval_spinbox = ttk.Spinbox(check_settings_frame, from_=1, to=168,
                                      textvariable=self.check_interval_var, width=10)
        interval_spinbox.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=(10, 0))
        
        # Auto-download settings
        download_settings_frame = ttk.LabelFrame(frame, text="Download Automático", padding="10")
        download_settings_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.auto_download_var = tk.BooleanVar(value=self.updater.config.auto_download)
        ttk.Checkbutton(download_settings_frame, text="Fazer download automático de atualizações",
                       variable=self.auto_download_var).grid(row=0, column=0, sticky=tk.W)
        
        self.auto_install_var = tk.BooleanVar(value=self.updater.config.auto_install)
        ttk.Checkbutton(download_settings_frame, text="Instalar automaticamente (não recomendado)",
                       variable=self.auto_install_var).grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        
        # Backup settings
        backup_settings_frame = ttk.LabelFrame(frame, text="Configurações de Backup", padding="10")
        backup_settings_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.backup_enabled_var = tk.BooleanVar(value=self.updater.config.backup_enabled)
        ttk.Checkbutton(backup_settings_frame, text="Criar backup antes de instalar atualizações",
                       variable=self.backup_enabled_var).grid(row=0, column=0, columnspan=2, sticky=tk.W)
        
        ttk.Label(backup_settings_frame, text="Máximo de backups para manter:").grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
        self.max_backups_var = tk.StringVar(value=str(self.updater.config.max_backup_count))
        backup_spinbox = ttk.Spinbox(backup_settings_frame, from_=1, to=10,
                                    textvariable=self.max_backups_var, width=10)
        backup_spinbox.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=(10, 0))
        
        # Advanced settings
        advanced_frame = ttk.LabelFrame(frame, text="Configurações Avançadas", padding="10")
        advanced_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.prerelease_var = tk.BooleanVar(value=self.updater.config.allow_prerelease)
        ttk.Checkbutton(advanced_frame, text="Incluir versões pré-lançamento (beta)",
                       variable=self.prerelease_var).grid(row=0, column=0, sticky=tk.W)
        
        # GitHub repository
        ttk.Label(advanced_frame, text="Repositório GitHub:").grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
        self.github_repo_var = tk.StringVar(value=self.updater.config.github_repo)
        repo_entry = ttk.Entry(advanced_frame, textvariable=self.github_repo_var, width=30)
        repo_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=(10, 0))
        advanced_frame.columnconfigure(1, weight=1)
        
        # Save settings button
        save_frame = ttk.Frame(frame)
        save_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.save_settings_button = ttk.Button(save_frame, text="💾 Guardar Configurações",
                                              command=self._save_settings)
        self.save_settings_button.grid(row=0, column=0)
        
        self.reset_settings_button = ttk.Button(save_frame, text="🔄 Restaurar Padrões",
                                               command=self._reset_settings)
        self.reset_settings_button.grid(row=0, column=1, padx=(10, 0))
    
    def _create_button_frame(self, parent):
        """Create bottom button frame."""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Close button
        ttk.Button(button_frame, text="Fechar", 
                  command=self._close_dialog).pack(side=tk.RIGHT)
        
        # Refresh button
        ttk.Button(button_frame, text="🔄 Atualizar", 
                  command=self._refresh_all).pack(side=tk.RIGHT, padx=(0, 10))
    
    def _load_current_status(self):
        """Load and display current update status."""
        summary = self.updater.get_update_summary()
        
        # Update version labels
        self.available_version_var.set(summary.get('latest_version', 'Desconhecida'))
        
        # Update check info
        last_check = summary.get('last_check', '')
        if last_check:
            try:
                check_date = datetime.fromisoformat(last_check)
                self.last_check_var.set(check_date.strftime('%d/%m/%Y %H:%M'))
            except ValueError:
                self.last_check_var.set("Data inválida")
        else:
            self.last_check_var.set("Nunca")
        
        next_check = summary.get('next_check', '')
        if next_check:
            try:
                next_date = datetime.fromisoformat(next_check)
                self.next_check_var.set(next_date.strftime('%d/%m/%Y %H:%M'))
            except ValueError:
                self.next_check_var.set("Data inválida")
        else:
            self.next_check_var.set("Não agendada")
        
        # Update status text
        status_text = f"""Estado: {'Ativo' if summary.get('enabled') else 'Inativo'}
Atualização disponível: {'Sim' if summary.get('update_available') else 'Não'}
Download em progresso: {'Sim' if summary.get('download_in_progress') else 'Não'}
Instalação em progresso: {'Sim' if summary.get('install_in_progress') else 'Não'}
Download automático: {'Ativado' if summary.get('auto_download') else 'Desativado'}
Instalação automática: {'Ativada' if summary.get('auto_install') else 'Desativada'}
Intervalo de verificação: {summary.get('check_interval_hours', 24)} horas
Backups disponíveis: {summary.get('backup_count', 0)}"""
        
        last_error = summary.get('last_error', '')
        if last_error:
            status_text += f"\\nÚltimo erro: {last_error}"
        
        self._update_text_widget(self.update_status_text, status_text)
        
        # Update status label
        if summary.get('update_available'):
            self.status_label.config(text="🔄 Atualização disponível", foreground='orange')
        elif summary.get('enabled'):
            self.status_label.config(text="✅ Sistema ativo", foreground='green')
        else:
            self.status_label.config(text="⏸️ Sistema inativo", foreground='gray')
    
    def _update_text_widget(self, widget, text):
        """Update text in a disabled text widget."""
        widget.config(state=tk.NORMAL)
        widget.delete(1.0, tk.END)
        widget.insert(1.0, text)
        widget.config(state=tk.DISABLED)
    
    def _check_updates_manual(self):
        """Manually check for updates."""
        if self.checking_updates:
            return
        
        self.checking_updates = True
        self.check_button.config(state=tk.DISABLED, text="🔍 Verificando...")
        
        def check_thread():
            try:
                update_info = self.updater.check_for_updates()
                self.root.after(0, lambda: self._handle_update_check_result(update_info))
            except Exception as e:
                self.root.after(0, lambda: self._handle_update_error(str(e)))
            finally:
                self.root.after(0, self._reset_check_button)
        
        threading.Thread(target=check_thread, daemon=True).start()
    
    def _handle_update_check_result(self, update_info):
        """Handle result of update check."""
        if update_info:
            self.current_update = update_info
            self._display_update_info(update_info)
            self.download_button.config(state=tk.NORMAL)
            
            # Show notification
            messagebox.showinfo("Atualização Disponível",
                              f"Nova versão disponível: {update_info.version}\\n"
                              f"Pode fazer o download na aba 'Atualizações'.")
        else:
            self._update_text_widget(self.update_info_text, 
                                   "Nenhuma atualização disponível.\\n"
                                   "A aplicação está atualizada.")
            self.download_button.config(state=tk.DISABLED)
            messagebox.showinfo("Sem Atualizações", "A aplicação está atualizada.")
        
        self._load_current_status()
    
    def _display_update_info(self, update_info):
        """Display detailed update information."""
        info_text = f"""Nova Versão: {update_info.version}
Data de Lançamento: {update_info.release_date}
Tamanho: {update_info.download_size / (1024*1024):.1f} MB
Crítica: {'Sim' if update_info.is_critical else 'Não'}
Requer Reinício: {'Sim' if update_info.requires_restart else 'Não'}

Notas de Lançamento:
{update_info.changelog}"""
        
        self._update_text_widget(self.update_info_text, info_text)
    
    def _handle_update_error(self, error_message):
        """Handle update check error."""
        self._update_text_widget(self.update_info_text, f"Erro ao verificar atualizações:\\n{error_message}")
        messagebox.showerror("Erro de Verificação", f"Falha ao verificar atualizações:\\n{error_message}")
    
    def _reset_check_button(self):
        """Reset check button state."""
        self.checking_updates = False
        self.check_button.config(state=tk.NORMAL, text="🔍 Verificar Agora")
    
    def _toggle_auto_check(self):
        """Toggle automatic checking."""
        enabled = self.auto_check_var.get()
        self.updater.config.enabled = enabled
        self.updater._save_config(self.updater.config)
        
        if enabled:
            self.updater.start_background_checking()
            self.status_label.config(text="✅ Sistema ativo", foreground='green')
        else:
            self.updater.stop_background_checking()
            self.status_label.config(text="⏸️ Sistema inativo", foreground='gray')
    
    def _download_update(self):
        """Start update download."""
        if not self.current_update:
            return
        
        self.download_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.NORMAL)
        self.progress_label.config(text="A fazer download...")
        
        def download_thread():
            success = self.updater.download_update(self.current_update)
            self.root.after(0, lambda: self._handle_download_complete(success))
        
        threading.Thread(target=download_thread, daemon=True).start()
    
    def _handle_download_complete(self, success):
        """Handle download completion."""
        self.cancel_button.config(state=tk.DISABLED)
        
        if success:
            self.progress_label.config(text="Download concluído")
            self.install_button.config(state=tk.NORMAL)
            messagebox.showinfo("Download Concluído", "Atualização descarregada com sucesso.\\nPode agora instalar.")
        else:
            self.progress_label.config(text="Erro no download")
            self.download_button.config(state=tk.NORMAL)
            messagebox.showerror("Erro de Download", "Falha ao fazer download da atualização.")
        
        self.progress_var.set(0)
    
    def _install_update(self):
        """Install the downloaded update."""
        if not self.current_update:
            return
        
        # Confirm installation
        response = messagebox.askyesno("Confirmar Instalação",
                                     "Tem certeza que deseja instalar a atualização?\\n"
                                     "A aplicação será reiniciada após a instalação.")
        if not response:
            return
        
        self.install_button.config(state=tk.DISABLED)
        self.progress_label.config(text="A instalar...")
        
        def install_thread():
            success = self.updater.install_update(self.current_update)
            self.root.after(0, lambda: self._handle_install_complete(success))
        
        threading.Thread(target=install_thread, daemon=True).start()
    
    def _handle_install_complete(self, success):
        """Handle installation completion."""
        if success:
            messagebox.showinfo("Instalação Concluída",
                              "Atualização instalada com sucesso!\\n"
                              "A aplicação será reiniciada.")
            self.root.quit()
        else:
            self.progress_label.config(text="Erro na instalação")
            self.install_button.config(state=tk.NORMAL)
            messagebox.showerror("Erro de Instalação", "Falha ao instalar a atualização.")
    
    def _cancel_operation(self):
        """Cancel current operation."""
        # In a real implementation, you would stop the download/install thread
        self.cancel_button.config(state=tk.DISABLED)
        self.download_button.config(state=tk.NORMAL)
        self.progress_var.set(0)
        self.progress_label.config(text="Operação cancelada")
    
    def _load_backups(self):
        """Load backup list."""
        # Clear existing items
        for item in self.backup_tree.get_children():
            self.backup_tree.delete(item)
        
        # Add backups
        backups = self.updater.get_available_backups()
        for backup in backups:
            self.backup_tree.insert('', tk.END,
                                  text=backup['filename'],
                                  values=(backup['version'], backup['date'], backup['size']))
    
    def _on_backup_select(self, event):
        """Handle backup selection."""
        selection = self.backup_tree.selection()
        if selection:
            self.restore_backup_button.config(state=tk.NORMAL)
            self.delete_backup_button.config(state=tk.NORMAL)
        else:
            self.restore_backup_button.config(state=tk.DISABLED)
            self.delete_backup_button.config(state=tk.DISABLED)
    
    def _create_backup(self):
        """Create a new backup."""
        response = messagebox.askyesno("Criar Backup",
                                     "Criar backup da aplicação atual?")
        if not response:
            return
        
        success = self.updater.create_backup()
        if success:
            messagebox.showinfo("Backup Criado", "Backup criado com sucesso.")
            self._load_backups()
        else:
            messagebox.showerror("Erro de Backup", "Falha ao criar backup.")
    
    def _restore_backup(self):
        """Restore from selected backup."""
        selection = self.backup_tree.selection()
        if not selection:
            return
        
        item = self.backup_tree.item(selection[0])
        backup_file = item['text']
        
        response = messagebox.askyesno("Confirmar Restauro",
                                     f"Restaurar backup '{backup_file}'?\\n"
                                     "Isto irá substituir a versão atual.")
        if not response:
            return
        
        success = self.updater.rollback_update(backup_file)
        if success:
            messagebox.showinfo("Restauro Concluído",
                              "Backup restaurado com sucesso!\\n"
                              "A aplicação será reiniciada.")
            self.root.quit()
        else:
            messagebox.showerror("Erro de Restauro", "Falha ao restaurar backup.")
    
    def _delete_backup(self):
        """Delete selected backup."""
        selection = self.backup_tree.selection()
        if not selection:
            return
        
        item = self.backup_tree.item(selection[0])
        backup_file = item['text']
        
        response = messagebox.askyesno("Confirmar Eliminação",
                                     f"Eliminar backup '{backup_file}'?\\n"
                                     "Esta ação não pode ser desfeita.")
        if not response:
            return
        
        try:
            backup_path = os.path.join(self.updater.backups_dir, backup_file)
            os.remove(backup_path)
            messagebox.showinfo("Backup Eliminado", "Backup eliminado com sucesso.")
            self._load_backups()
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao eliminar backup:\\n{e}")
    
    def _save_settings(self):
        """Save current settings."""
        try:
            # Update configuration
            self.updater.config.enabled = self.enable_auto_var.get()
            self.updater.config.check_interval_hours = int(self.check_interval_var.get())
            self.updater.config.auto_download = self.auto_download_var.get()
            self.updater.config.auto_install = self.auto_install_var.get()
            self.updater.config.backup_enabled = self.backup_enabled_var.get()
            self.updater.config.max_backup_count = int(self.max_backups_var.get())
            self.updater.config.allow_prerelease = self.prerelease_var.get()
            self.updater.config.github_repo = self.github_repo_var.get()
            
            # Save configuration
            self.updater._save_config(self.updater.config)
            
            # Restart background checking if enabled
            if self.updater.config.enabled:
                self.updater.start_background_checking()
            else:
                self.updater.stop_background_checking()
            
            messagebox.showinfo("Configurações Guardadas", "Configurações guardadas com sucesso.")
            self._load_current_status()
            
        except ValueError as e:
            messagebox.showerror("Erro de Validação", f"Valores inválidos nas configurações:\\n{e}")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao guardar configurações:\\n{e}")
    
    def _reset_settings(self):
        """Reset settings to defaults."""
        response = messagebox.askyesno("Confirmar Restauro",
                                     "Restaurar todas as configurações para os valores padrão?")
        if not response:
            return
        
        # Reset to defaults
        default_config = AutoUpdater().config
        
        self.enable_auto_var.set(default_config.enabled)
        self.check_interval_var.set(str(default_config.check_interval_hours))
        self.auto_download_var.set(default_config.auto_download)
        self.auto_install_var.set(default_config.auto_install)
        self.backup_enabled_var.set(default_config.backup_enabled)
        self.max_backups_var.set(str(default_config.max_backup_count))
        self.prerelease_var.set(default_config.allow_prerelease)
        self.github_repo_var.set(default_config.github_repo)
    
    def _refresh_all(self):
        """Refresh all data."""
        self._load_current_status()
        self._load_backups()
        messagebox.showinfo("Atualizado", "Dados atualizados com sucesso.")
    
    def _handle_update_callback(self, event_type, data):
        """Handle callbacks from auto-updater."""
        if event_type == 'update_available':
            self.root.after(0, lambda: self._handle_update_available_callback(data))
        elif event_type == 'download_progress':
            self.root.after(0, lambda: self._handle_download_progress_callback(data))
        elif event_type == 'update_error':
            self.root.after(0, lambda: self._handle_update_error_callback(data))
        elif event_type == 'restart_required':
            self.root.after(0, lambda: self._handle_restart_required_callback(data))
    
    def _handle_update_available_callback(self, update_info):
        """Handle update available callback."""
        self.current_update = update_info
        self._display_update_info(update_info)
        self.download_button.config(state=tk.NORMAL)
        
        # Show notification
        if self.updater.config.notify_user:
            response = messagebox.askyesno("Nova Atualização Disponível",
                                         f"Nova versão disponível: {update_info.version}\\n"
                                         f"Deseja ver os detalhes?")
            if response:
                self.notebook.select(1)  # Switch to updates tab
    
    def _handle_download_progress_callback(self, progress):
        """Handle download progress callback."""
        self.progress_var.set(progress)
        self.progress_label.config(text=f"{progress:.1f}%")
    
    def _handle_update_error_callback(self, error_message):
        """Handle update error callback."""
        self.progress_label.config(text="Erro")
        if self.updater.config.notify_user:
            messagebox.showerror("Erro de Atualização", error_message)
    
    def _handle_restart_required_callback(self, update_info):
        """Handle restart required callback."""
        messagebox.showwarning("Reinício Necessário",
                             f"Atualização para a versão {update_info.version} instalada.\\n"
                             "Reinicie a aplicação para aplicar as alterações.")
    
    def _close_dialog(self):
        """Close the dialog."""
        # Stop background checking when closing
        self.updater.stop_background_checking()
        
        if self.parent:
            self.root.destroy()
        else:
            self.root.quit()
    
    def show(self):
        """Show the dialog."""
        self.root.mainloop()


def show_auto_updater_dialog(parent=None):
    """Show auto-updater dialog."""
    dialog = AutoUpdaterDialog(parent)
    dialog.show()


if __name__ == "__main__":
    # Demo usage
    import os
    import sys
    
    # Add parent directory to path for imports
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    show_auto_updater_dialog()
