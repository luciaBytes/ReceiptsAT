"""
API Monitor GUI Dialog - Monitor Portal das Finanças changes

Provides a user-friendly interface for viewing API monitoring status,
detected changes, and managing monitoring configuration.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
from typing import Dict, List, Any
from datetime import datetime
import json

try:
    from ..utils.api_monitor import PortalAPIMonitor, ChangeDetection
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
    from utils.api_monitor import PortalAPIMonitor, ChangeDetection

try:
    from ..utils.logger import get_logger
except ImportError:
    from utils.logger import get_logger

logger = get_logger(__name__)


class APIMonitorDialog:
    """GUI dialog for API monitoring status and configuration."""
    
    def __init__(self, parent):
        self.parent = parent
        self.monitor = PortalAPIMonitor()
        
        # Create dialog window
        self.window = tk.Toplevel(parent)
        self.window.title("Portal das Finanças - Monitor de API")
        self.window.geometry("900x700")
        self.window.transient(parent)
        self.window.grab_set()
        
        # Center the window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (900 // 2)
        y = (self.window.winfo_screenheight() // 2) - (700 // 2)
        self.window.geometry(f"900x700+{x}+{y}")
        
        self._setup_gui()
        self._load_data()
    
    def _setup_gui(self):
        """Setup the GUI components."""
        # Main frame
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Title and status
        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        title_frame.columnconfigure(1, weight=1)
        
        ttk.Label(title_frame, text=" Monitor de API Portal das Finanças", 
                 font=('TkDefaultFont', 12, 'bold')).grid(row=0, column=0, sticky=tk.W)
        
        self.status_label = ttk.Label(title_frame, text="Status: Carregando...", 
                                     foreground="orange")
        self.status_label.grid(row=0, column=1, sticky=tk.E)
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(button_frame, text=" Verificar Agora", 
                  command=self._start_monitoring_check).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(button_frame, text=" Relatório Completo", 
                  command=self._show_full_report).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="⚙️ Configurações", 
                  command=self._show_config).grid(row=0, column=2, padx=5)
        ttk.Button(button_frame, text="🧹 Limpar Histórico", 
                  command=self._clear_history).grid(row=0, column=3, padx=5)
        
        # Notebook for different views
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Overview tab
        self._create_overview_tab()
        
        # Changes tab
        self._create_changes_tab()
        
        # History tab
        self._create_history_tab()
        
        # Close button
        ttk.Button(main_frame, text="Fechar", 
                  command=self.window.destroy).grid(row=3, column=0, pady=(5, 0))
    
    def _create_overview_tab(self):
        """Create the overview tab."""
        overview_frame = ttk.Frame(self.notebook)
        self.notebook.add(overview_frame, text=" Visão Geral")
        
        # Overview text
        self.overview_text = scrolledtext.ScrolledText(overview_frame, height=20, width=80)
        self.overview_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def _create_changes_tab(self):
        """Create the changes tab."""
        changes_frame = ttk.Frame(self.notebook)
        self.notebook.add(changes_frame, text=" Alterações")
        
        # Changes tree
        columns = ('Timestamp', 'Tipo', 'Severidade', 'Descrição')
        self.changes_tree = ttk.Treeview(changes_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.changes_tree.heading(col, text=col)
            
        # Configure column widths
        self.changes_tree.column('Timestamp', width=150)
        self.changes_tree.column('Tipo', width=80)
        self.changes_tree.column('Severidade', width=80)
        self.changes_tree.column('Descrição', width=400)
        
        # Scrollbar for changes tree
        changes_scrollbar = ttk.Scrollbar(changes_frame, orient=tk.VERTICAL, command=self.changes_tree.yview)
        self.changes_tree.configure(yscrollcommand=changes_scrollbar.set)
        
        # Pack changes tree
        self.changes_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)
        changes_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10), pady=10)
        
        # Bind double-click to show change details
        self.changes_tree.bind('<Double-1>', self._show_change_details)
    
    def _create_history_tab(self):
        """Create the monitoring history tab."""
        history_frame = ttk.Frame(self.notebook)
        self.notebook.add(history_frame, text=" Histórico")
        
        # History text
        self.history_text = scrolledtext.ScrolledText(history_frame, height=20, width=80)
        self.history_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def _load_data(self):
        """Load monitoring data and update display."""
        try:
            # Update status
            if self.monitor.should_run_check():
                self.status_label.config(text="Status: Verificação Necessária", foreground="orange")
            else:
                self.status_label.config(text="Status: Atualizado", foreground="green")
            
            # Load overview
            self._update_overview()
            
            # Load changes
            self._update_changes()
            
            # Load history
            self._update_history()
            
        except Exception as e:
            logger.error(f"Error loading monitoring data: {e}")
            messagebox.showerror("Erro", f"Erro ao carregar dados de monitorização: {e}")
    
    def _update_overview(self):
        """Update the overview display."""
        try:
            report = self.monitor.generate_monitoring_report()
            
            overview_text = f"""
 RELATÓRIO DE MONITORIZAÇÃO - Portal das Finanças
{'=' * 60}

 Estatísticas Gerais:
  • Páginas monitorizadas: {report['total_pages_monitored']}
  • Total de snapshots: {report['total_snapshots_taken']}
  • Total de alterações: {report['total_changes_detected']}
  • Alterações recentes (24h): {report['recent_changes_24h']}
  • Alterações críticas: {report['critical_changes_total']}

🎯 Distribuição por Severidade:
"""
            
            for severity, count in report['severity_breakdown'].items():
                severity_emoji = {
                    'low': '🟢',
                    'medium': '🟡', 
                    'high': '🟠',
                    'critical': '🔴'
                }.get(severity, '⚪')
                overview_text += f"  {severity_emoji} {severity.capitalize()}: {count}\n"
            
            if report['critical_changes']:
                overview_text += f"\n Alterações Críticas Recentes:\n"
                for change in report['critical_changes']:
                    timestamp = change['timestamp'][:19].replace('T', ' ')
                    overview_text += f"  • {timestamp}: {change['description']}\n"
            
            if report['last_check_times']:
                overview_text += f"\n Últimas Verificações:\n"
                for url, timestamp in report['last_check_times'].items():
                    check_time = timestamp[:19].replace('T', ' ')
                    domain = url.split('/')[2] if len(url.split('/')) > 2 else url
                    overview_text += f"  • {domain}: {check_time}\n"
            
            overview_text += f"\n💡 Próxima verificação automática em {self.monitor.config.check_interval_hours} horas\n"
            
            self.overview_text.delete(1.0, tk.END)
            self.overview_text.insert(1.0, overview_text)
            
        except Exception as e:
            logger.error(f"Error updating overview: {e}")
            self.overview_text.delete(1.0, tk.END)
            self.overview_text.insert(1.0, f"Erro ao carregar visão geral: {e}")
    
    def _update_changes(self):
        """Update the changes display."""
        try:
            # Clear existing items
            for item in self.changes_tree.get_children():
                self.changes_tree.delete(item)
            
            # Get recent changes (last 7 days)
            recent_changes = self.monitor.get_recent_changes(24 * 7)
            recent_changes.sort(key=lambda x: x.timestamp, reverse=True)
            
            # Add changes to tree
            for change in recent_changes:
                timestamp = change.timestamp[:19].replace('T', ' ')
                
                # Add severity emoji
                severity_emoji = {
                    'low': '🟢',
                    'medium': '🟡',
                    'high': '🟠', 
                    'critical': '🔴'
                }.get(change.severity, '⚪')
                
                severity_text = f"{severity_emoji} {change.severity.capitalize()}"
                
                self.changes_tree.insert('', tk.END, values=(
                    timestamp,
                    change.change_type.capitalize(),
                    severity_text,
                    change.description
                ), tags=(change.severity,))
            
            # Configure row colors
            self.changes_tree.tag_configure('critical', background='#ffebee')
            self.changes_tree.tag_configure('high', background='#fff3e0')
            self.changes_tree.tag_configure('medium', background='#fffde7')
            self.changes_tree.tag_configure('low', background='#f1f8e9')
            
        except Exception as e:
            logger.error(f"Error updating changes: {e}")
    
    def _update_history(self):
        """Update the history display."""
        try:
            history_text = " HISTÓRICO DE MONITORIZAÇÃO\n"
            history_text += "=" * 50 + "\n\n"
            
            # Get all changes grouped by date
            changes_by_date = {}
            for change in self.monitor.changes:
                try:
                    date = change.timestamp[:10]  # YYYY-MM-DD
                    if date not in changes_by_date:
                        changes_by_date[date] = []
                    changes_by_date[date].append(change)
                except (ValueError, IndexError):
                    continue
            
            # Sort dates (most recent first)
            sorted_dates = sorted(changes_by_date.keys(), reverse=True)
            
            for date in sorted_dates[:14]:  # Last 14 days
                changes = changes_by_date[date]
                history_text += f"📅 {date}\n"
                history_text += f"   Alterações: {len(changes)}\n"
                
                # Group by severity
                severity_count = {}
                for change in changes:
                    severity_count[change.severity] = severity_count.get(change.severity, 0) + 1
                
                for severity, count in severity_count.items():
                    emoji = {'low': '🟢', 'medium': '🟡', 'high': '🟠', 'critical': '🔴'}.get(severity, '⚪')
                    history_text += f"   {emoji} {severity.capitalize()}: {count}\n"
                
                history_text += "\n"
            
            if not sorted_dates:
                history_text += "Nenhum histórico disponível.\n"
            
            self.history_text.delete(1.0, tk.END)
            self.history_text.insert(1.0, history_text)
            
        except Exception as e:
            logger.error(f"Error updating history: {e}")
            self.history_text.delete(1.0, tk.END)
            self.history_text.insert(1.0, f"Erro ao carregar histórico: {e}")
    
    def _start_monitoring_check(self):
        """Start monitoring check in background thread."""
        def run_check():
            try:
                self.status_label.config(text="Status: Verificando...", foreground="blue")
                self.window.update()
                
                snapshots, changes = self.monitor.monitor_all_pages()
                
                # Update display in main thread
                self.window.after(0, lambda: self._monitoring_check_complete(len(snapshots), len(changes)))
                
            except Exception as e:
                logger.error(f"Error during monitoring check: {e}")
                self.window.after(0, lambda: messagebox.showerror("Erro", f"Erro na verificação: {e}"))
                self.window.after(0, lambda: self.status_label.config(text="Status: Erro", foreground="red"))
        
        thread = threading.Thread(target=run_check, daemon=True)
        thread.start()
    
    def _monitoring_check_complete(self, snapshot_count: int, change_count: int):
        """Handle monitoring check completion."""
        self.status_label.config(text="Status: Atualizado", foreground="green")
        
        if change_count > 0:
            messagebox.showinfo("Verificação Completa", 
                              f"Verificação concluída!\n\n"
                              f"• {snapshot_count} snapshots capturados\n"
                              f"• {change_count} alterações detectadas")
        else:
            messagebox.showinfo("Verificação Completa",
                              f"Verificação concluída!\n\n"
                              f"• {snapshot_count} snapshots capturados\n"
                              f"• Nenhuma alteração detectada")
        
        # Refresh display
        self._load_data()
    
    def _show_change_details(self, event):
        """Show detailed information about a selected change."""
        selection = self.changes_tree.selection()
        if not selection:
            return
        
        item = self.changes_tree.item(selection[0])
        values = item['values']
        
        if not values:
            return
        
        # Find the actual change object
        timestamp_str = values[0]
        
        change = None
        for c in self.monitor.changes:
            if c.timestamp.startswith(timestamp_str.replace(' ', 'T')):
                change = c
                break
        
        if not change:
            return
        
        # Create details dialog
        details_window = tk.Toplevel(self.window)
        details_window.title("Detalhes da Alteração")
        details_window.geometry("600x500")
        details_window.transient(self.window)
        
        # Center the window
        details_window.update_idletasks()
        x = (details_window.winfo_screenwidth() // 2) - (300)
        y = (details_window.winfo_screenheight() // 2) - (250)
        details_window.geometry(f"600x500+{x}+{y}")
        
        # Details text
        details_text = scrolledtext.ScrolledText(details_window, wrap=tk.WORD)
        details_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        details_content = f""" DETALHES DA ALTERAÇÃO
{'=' * 50}

 Timestamp: {change.timestamp}
🏷️ Tipo: {change.change_type}
 Severidade: {change.severity}

 Descrição:
{change.description}

 Valor Anterior:
{change.old_value}

🆕 Valor Novo:
{change.new_value}

⚙️ Funcionalidade Afetada:
{', '.join(change.affected_functionality)}

💡 Ação Recomendada:
{change.recommended_action}
"""
        
        details_text.insert(1.0, details_content)
        details_text.config(state=tk.DISABLED)
        
        # Close button
        ttk.Button(details_window, text="Fechar",
                  command=details_window.destroy).pack(pady=10)
    
    def _show_full_report(self):
        """Show full monitoring report in a new window."""
        report_window = tk.Toplevel(self.window)
        report_window.title("Relatório Completo de Monitorização")
        report_window.geometry("800x600")
        report_window.transient(self.window)
        
        # Report text
        report_text = scrolledtext.ScrolledText(report_window, wrap=tk.WORD)
        report_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        try:
            report = self.monitor.generate_monitoring_report()
            full_report = json.dumps(report, indent=2, ensure_ascii=False)
            report_text.insert(1.0, full_report)
        except Exception as e:
            report_text.insert(1.0, f"Erro ao gerar relatório: {e}")
        
        report_text.config(state=tk.DISABLED)
        
        # Close button
        ttk.Button(report_window, text="Fechar",
                  command=report_window.destroy).pack(pady=10)
    
    def _show_config(self):
        """Show monitoring configuration dialog."""
        config_window = tk.Toplevel(self.window)
        config_window.title("Configurações de Monitorização")
        config_window.geometry("500x400")
        config_window.transient(self.window)
        
        # Configuration form
        ttk.Label(config_window, text="⚙️ Configurações", 
                 font=('TkDefaultFont', 12, 'bold')).pack(pady=10)
        
        # Interval setting
        interval_frame = ttk.Frame(config_window)
        interval_frame.pack(fill=tk.X, padx=20, pady=5)
        
        ttk.Label(interval_frame, text="Intervalo de verificação (horas):").pack(side=tk.LEFT)
        interval_var = tk.IntVar(value=self.monitor.config.check_interval_hours)
        interval_spinbox = ttk.Spinbox(interval_frame, from_=1, to=24, width=5, textvariable=interval_var)
        interval_spinbox.pack(side=tk.RIGHT)
        
        # Pages to monitor
        pages_frame = ttk.LabelFrame(config_window, text="Páginas Monitorizadas", padding=10)
        pages_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        pages_text = scrolledtext.ScrolledText(pages_frame, height=8)
        pages_text.pack(fill=tk.BOTH, expand=True)
        pages_text.insert(1.0, '\n'.join(self.monitor.config.critical_pages))
        
        # Buttons
        button_frame = ttk.Frame(config_window)
        button_frame.pack(fill=tk.X, padx=20, pady=10)
        
        def save_config():
            try:
                self.monitor.config.check_interval_hours = interval_var.get()
                pages_content = pages_text.get(1.0, tk.END).strip()
                self.monitor.config.critical_pages = [url.strip() for url in pages_content.split('\n') if url.strip()]
                self.monitor._save_config(self.monitor.config)
                messagebox.showinfo("Sucesso", "Configurações guardadas!")
                config_window.destroy()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao guardar configurações: {e}")
        
        ttk.Button(button_frame, text="Guardar", command=save_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancelar", command=config_window.destroy).pack(side=tk.LEFT)
    
    def _clear_history(self):
        """Clear monitoring history after confirmation."""
        result = messagebox.askyesno("Confirmação", 
                                   "Tem certeza que deseja limpar todo o histórico de monitorização?\n\n"
                                   "Esta ação não pode ser desfeita.")
        
        if result:
            try:
                self.monitor.changes = []
                self.monitor.snapshots = []
                self.monitor._save_changes()
                self.monitor._save_snapshots()
                messagebox.showinfo("Sucesso", "Histórico limpo com sucesso!")
                self._load_data()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao limpar histórico: {e}")


def show_api_monitor_dialog(parent):
    """Show the API monitor dialog."""
    try:
        APIMonitorDialog(parent)
    except Exception as e:
        logger.error(f"Error showing API monitor dialog: {e}")
        messagebox.showerror("Erro", f"Erro ao abrir monitor de API: {e}")


if __name__ == "__main__":
    # Test the dialog
    root = tk.Tk()
    root.withdraw()  # Hide main window
    
    show_api_monitor_dialog(root)
    root.mainloop()
