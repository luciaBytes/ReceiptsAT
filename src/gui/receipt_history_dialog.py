"""
Receipt History Dialog - GUI for viewing and managing receipt database history.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import threading

try:
    from ..utils.receipt_database import ReceiptDatabase, ReceiptRecord
    from ..utils.logger import get_logger
except ImportError:
    from utils.receipt_database import ReceiptDatabase, ReceiptRecord
    from utils.logger import get_logger

logger = get_logger(__name__)


class ReceiptHistoryDialog:
    """Dialog for viewing and managing receipt history."""
    
    def __init__(self, parent: tk.Tk, database: ReceiptDatabase = None):
        """Initialize the receipt history dialog.
        
        Args:
            parent: Parent window
            database: Optional database instance (creates one if None)
        """
        self.parent = parent
        self.database = database or ReceiptDatabase()
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Receipt History & Database")
        self.dialog.geometry("1200x800")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Variables
        self.receipts: List[ReceiptRecord] = []
        self.filtered_receipts: List[ReceiptRecord] = []
        self.search_var = tk.StringVar()
        self.status_filter_var = tk.StringVar(value="All")
        self.dry_run_filter_var = tk.StringVar(value="All")
        
        # Setup GUI
        self._setup_gui()
        
        # Load initial data
        self._load_receipts()
        
        # Center dialog on parent
        self.dialog.update_idletasks()
        self._center_dialog()
    
    def _setup_gui(self):
        """Setup the GUI components."""
        # Main container with padding
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.dialog.columnconfigure(0, weight=1)
        self.dialog.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Title and statistics
        self._create_header(main_frame)
        
        # Search and filters
        self._create_search_section(main_frame)
        
        # Receipt list
        self._create_receipt_list(main_frame)
        
        # Action buttons
        self._create_action_buttons(main_frame)
    
    def _create_header(self, parent):
        """Create header with title and statistics."""
        header_frame = ttk.Frame(parent)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        header_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(header_frame, text="📋 Receipt History & Database", 
                               font=("TkDefaultFont", 14, "bold"))
        title_label.grid(row=0, column=0, sticky=tk.W)
        
        # Statistics
        self.stats_label = ttk.Label(header_frame, text="Loading statistics...", 
                                    foreground="gray")
        self.stats_label.grid(row=0, column=1, sticky=tk.E)
        
        # Load stats in background
        threading.Thread(target=self._update_statistics, daemon=True).start()
    
    def _create_search_section(self, parent):
        """Create search and filter section."""
        search_frame = ttk.LabelFrame(parent, text="Search & Filters", padding="5")
        search_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        search_frame.columnconfigure(1, weight=1)
        
        # Search box
        ttk.Label(search_frame, text="Search:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=40)
        search_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        search_entry.bind('<KeyRelease>', self._on_search_changed)
        
        # Status filter
        ttk.Label(search_frame, text="Status:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        status_combo = ttk.Combobox(search_frame, textvariable=self.status_filter_var,
                                   values=["All", "Success", "Failed", "Skipped"], width=12)
        status_combo.grid(row=0, column=3, padx=(0, 10))
        status_combo.bind('<<ComboboxSelected>>', self._on_filter_changed)
        
        # Dry run filter
        ttk.Label(search_frame, text="Type:").grid(row=0, column=4, sticky=tk.W, padx=(0, 5))
        dry_run_combo = ttk.Combobox(search_frame, textvariable=self.dry_run_filter_var,
                                    values=["All", "Real Receipts", "Dry Run"], width=12)
        dry_run_combo.grid(row=0, column=5, padx=(0, 10))
        dry_run_combo.bind('<<ComboboxSelected>>', self._on_filter_changed)
        
        # Refresh button
        ttk.Button(search_frame, text="🔄 Refresh", 
                  command=self._refresh_receipts).grid(row=0, column=6)
    
    def _create_receipt_list(self, parent):
        """Create the receipt list with scrollable table."""
        list_frame = ttk.LabelFrame(parent, text="Receipt Records", padding="5")
        list_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # Create treeview with scrollbars
        tree_container = ttk.Frame(list_frame)
        tree_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        tree_container.columnconfigure(0, weight=1)
        tree_container.rowconfigure(0, weight=1)
        
        # Treeview columns
        columns = ('Contract ID', 'Tenant Name', 'Dates', 'Value', 'Status', 
                  'Receipt #', 'Type', 'Timestamp')
        
        self.tree = ttk.Treeview(tree_container, columns=columns, show='headings', height=20)
        
        # Configure columns
        self.tree.heading('Contract ID', text='Contract ID')
        self.tree.column('Contract ID', width=100, anchor=tk.CENTER)
        
        self.tree.heading('Tenant Name', text='Tenant Name')
        self.tree.column('Tenant Name', width=180)
        
        self.tree.heading('Dates', text='Period')
        self.tree.column('Dates', width=120, anchor=tk.CENTER)
        
        self.tree.heading('Value', text='Value (€)')
        self.tree.column('Value', width=80, anchor=tk.E)
        
        self.tree.heading('Status', text='Status')
        self.tree.column('Status', width=80, anchor=tk.CENTER)
        
        self.tree.heading('Receipt #', text='Receipt #')
        self.tree.column('Receipt #', width=100, anchor=tk.CENTER)
        
        self.tree.heading('Type', text='Type')
        self.tree.column('Type', width=70, anchor=tk.CENTER)
        
        self.tree.heading('Timestamp', text='Processed')
        self.tree.column('Timestamp', width=120, anchor=tk.CENTER)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_container, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid layout
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Bind double-click for details
        self.tree.bind('<Double-Button-1>', self._on_receipt_double_click)
        
        # Status colors
        self.tree.tag_configure('success', foreground='darkgreen')
        self.tree.tag_configure('failed', foreground='darkred')
        self.tree.tag_configure('skipped', foreground='orange')
        self.tree.tag_configure('dry_run', background='lightyellow')
    
    def _create_action_buttons(self, parent):
        """Create action buttons at the bottom."""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Left side buttons
        left_frame = ttk.Frame(button_frame)
        left_frame.pack(side=tk.LEFT)
        
        ttk.Button(left_frame, text="📋 View Details", 
                  command=self._view_receipt_details).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(left_frame, text="📊 Statistics", 
                  command=self._show_statistics).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(left_frame, text="📤 Export CSV", 
                  command=self._export_csv).pack(side=tk.LEFT, padx=(0, 5))
        
        # Separator
        separator_frame = ttk.Frame(button_frame, width=20)
        separator_frame.pack(side=tk.LEFT, padx=10)
        
        ttk.Button(left_frame, text="🗑️ Clear All", 
                  command=self._clear_all_receipts).pack(side=tk.LEFT, padx=(0, 5))
        
        # Right side buttons
        right_frame = ttk.Frame(button_frame)
        right_frame.pack(side=tk.RIGHT)
        
        ttk.Button(right_frame, text="Close", 
                  command=self.dialog.destroy).pack(side=tk.RIGHT)
    
    def _center_dialog(self):
        """Center the dialog on the parent window."""
        self.dialog.update_idletasks()
        
        # Get parent window position and size
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        # Get dialog size
        dialog_width = self.dialog.winfo_width()
        dialog_height = self.dialog.winfo_height()
        
        # Calculate position
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
    
    def _load_receipts(self):
        """Load receipts from database."""
        def load_in_background():
            try:
                self.receipts = self.database.get_recent_receipts(limit=1000)
                self.filtered_receipts = self.receipts.copy()
                
                # Update UI in main thread
                self.dialog.after(0, self._update_receipt_list)
                
            except Exception as e:
                logger.error(f"Failed to load receipts: {e}")
                self.dialog.after(0, lambda: messagebox.showerror(
                    "Error", f"Failed to load receipts:\n{str(e)}"))
        
        threading.Thread(target=load_in_background, daemon=True).start()
    
    def _update_receipt_list(self):
        """Update the receipt list display."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add filtered receipts
        for receipt in self.filtered_receipts:
            # Format values for display
            dates = f"{receipt.from_date} to {receipt.to_date}"
            value_str = f"{receipt.value:.2f}"
            timestamp = receipt.timestamp[:19].replace('T', ' ')  # Remove microseconds
            
            # Determine receipt type
            receipt_type = "Dry Run" if receipt.dry_run else "Real"
            
            # Determine tags for styling
            tags = []
            if receipt.status.lower() == 'success':
                tags.append('success')
            elif receipt.status.lower() == 'failed':
                tags.append('failed')
            elif receipt.status.lower() == 'skipped':
                tags.append('skipped')
            
            if receipt.dry_run:
                tags.append('dry_run')
            
            # Insert item
            self.tree.insert('', tk.END, values=(
                receipt.contract_id,
                receipt.tenant_name or "Unknown",
                dates,
                value_str,
                receipt.status,
                receipt.receipt_number or "N/A",
                receipt_type,
                timestamp
            ), tags=tags)
        
        logger.info(f"Updated receipt list with {len(self.filtered_receipts)} records")
    
    def _apply_filters(self):
        """Apply search and filters to receipt list."""
        search_term = self.search_var.get().lower()
        status_filter = self.status_filter_var.get()
        dry_run_filter = self.dry_run_filter_var.get()
        
        self.filtered_receipts = []
        
        for receipt in self.receipts:
            # Text search (searches in contract ID, tenant name, receipt number)
            if search_term:
                searchable_text = f"{receipt.contract_id} {receipt.tenant_name} {receipt.receipt_number}".lower()
                if search_term not in searchable_text:
                    continue
            
            # Status filter
            if status_filter != "All" and receipt.status != status_filter:
                continue
            
            # Dry run filter
            if dry_run_filter == "Real Receipts" and receipt.dry_run:
                continue
            elif dry_run_filter == "Dry Run" and not receipt.dry_run:
                continue
            
            self.filtered_receipts.append(receipt)
        
        self._update_receipt_list()
    
    def _on_search_changed(self, event=None):
        """Handle search text changes."""
        self._apply_filters()
    
    def _on_filter_changed(self, event=None):
        """Handle filter changes."""
        self._apply_filters()
    
    def _refresh_receipts(self):
        """Refresh the receipt list from database."""
        self._load_receipts()
        self._update_statistics()
    
    def _on_receipt_double_click(self, event=None):
        """Handle double-click on receipt item."""
        self._view_receipt_details()
    
    def _view_receipt_details(self):
        """Show detailed information about selected receipt."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a receipt to view details.")
            return
        
        # Get selected receipt
        item = self.tree.item(selection[0])
        values = item['values']
        contract_id = values[0]
        
        # Find the receipt in our data
        selected_receipt = None
        for receipt in self.filtered_receipts:
            if receipt.contract_id == contract_id:
                selected_receipt = receipt
                break
        
        if not selected_receipt:
            messagebox.showerror("Error", "Could not find receipt details.")
            return
        
        # Show details dialog
        ReceiptDetailsDialog(self.dialog, selected_receipt)
    
    def _show_statistics(self):
        """Show statistics dialog."""
        StatisticsDialog(self.dialog, self.database)
    
    def _export_csv(self):
        """Export receipts to CSV file."""
        file_path = filedialog.asksaveasfilename(
            title="Export Receipts to CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        def export_in_background():
            try:
                success = self.database.export_to_csv(file_path)
                
                if success:
                    self.dialog.after(0, lambda: messagebox.showinfo(
                        "Export Successful", f"Receipts exported successfully to:\n{file_path}"))
                else:
                    self.dialog.after(0, lambda: messagebox.showerror(
                        "Export Failed", "Failed to export receipts to CSV."))
            
            except Exception as e:
                logger.error(f"CSV export error: {e}")
                self.dialog.after(0, lambda: messagebox.showerror(
                    "Export Error", f"Error during CSV export:\n{str(e)}"))
        
        threading.Thread(target=export_in_background, daemon=True).start()
    
    def _clear_all_receipts(self):
        """Clear all receipts from database after confirmation."""
        result = messagebox.askyesno(
            "Confirm Clear All",
            "Are you sure you want to delete ALL receipt records?\n\n"
            "This action cannot be undone!",
            icon='warning'
        )
        
        if not result:
            return
        
        def clear_in_background():
            try:
                count = self.database.clear_all_receipts()
                
                # Update UI
                self.dialog.after(0, lambda: [
                    messagebox.showinfo("Clear Complete", f"Deleted {count} receipt records."),
                    self._refresh_receipts()
                ])
            
            except Exception as e:
                logger.error(f"Failed to clear receipts: {e}")
                self.dialog.after(0, lambda: messagebox.showerror(
                    "Clear Failed", f"Error clearing receipts:\n{str(e)}"))
        
        threading.Thread(target=clear_in_background, daemon=True).start()
    
    def _update_statistics(self):
        """Update the statistics display."""
        def get_stats_in_background():
            try:
                stats = self.database.get_statistics()
                
                # Format statistics text
                total = stats.get('total_receipts', 0)
                successful = stats.get('successful_receipts', 0)
                failed = stats.get('failed_receipts', 0)
                total_value = stats.get('total_value', 0)
                
                stats_text = (f"📊 {total} receipts | "
                             f"✅ {successful} successful | "
                             f"❌ {failed} failed | "
                             f"💰 €{total_value:,.2f} total value")
                
                # Update UI in main thread
                self.dialog.after(0, lambda: self.stats_label.config(text=stats_text))
                
            except Exception as e:
                logger.error(f"Failed to get statistics: {e}")
                self.dialog.after(0, lambda: self.stats_label.config(text="Statistics unavailable"))
        
        threading.Thread(target=get_stats_in_background, daemon=True).start()


class ReceiptDetailsDialog:
    """Dialog showing detailed information about a specific receipt."""
    
    def __init__(self, parent: tk.Toplevel, receipt: ReceiptRecord):
        """Initialize the receipt details dialog."""
        self.parent = parent
        self.receipt = receipt
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Receipt Details - Contract {receipt.contract_id}")
        self.dialog.geometry("600x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self._setup_gui()
        self._center_dialog()
    
    def _setup_gui(self):
        """Setup the details GUI."""
        main_frame = ttk.Frame(self.dialog, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.dialog.columnconfigure(0, weight=1)
        self.dialog.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, 
                               text=f"📄 Receipt Details", 
                               font=("TkDefaultFont", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 15))
        
        # Receipt information fields
        fields = [
            ("Contract ID:", self.receipt.contract_id),
            ("Tenant Name:", self.receipt.tenant_name or "Unknown"),
            ("Period:", f"{self.receipt.from_date} to {self.receipt.to_date}"),
            ("Payment Date:", self.receipt.payment_date or "Not set"),
            ("Value:", f"€{self.receipt.value:.2f}"),
            ("Receipt Type:", self.receipt.receipt_type or "Unknown"),
            ("Receipt Number:", self.receipt.receipt_number or "Not issued"),
            ("Status:", self.receipt.status),
            ("Processing Mode:", self.receipt.processing_mode or "Unknown"),
            ("Type:", "Dry Run" if self.receipt.dry_run else "Real Receipt"),
            ("Tenant Count:", str(self.receipt.tenant_count)),
            ("Landlord Count:", str(self.receipt.landlord_count)),
            ("Inheritance:", "Yes" if self.receipt.is_inheritance else "No"),
            ("Timestamp:", self.receipt.timestamp.replace('T', ' ')[:19]),
        ]
        
        row = 1
        for label_text, value in fields:
            # Label
            label = ttk.Label(main_frame, text=label_text, font=("TkDefaultFont", 9, "bold"))
            label.grid(row=row, column=0, sticky=(tk.W, tk.N), padx=(0, 10), pady=2)
            
            # Value (make it selectable)
            value_label = tk.Label(main_frame, text=str(value), 
                                  font=("TkDefaultFont", 9), 
                                  bg=self.dialog.cget('bg'),
                                  anchor='w', justify='left')
            value_label.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=2)
            
            # Make long text selectable
            if len(str(value)) > 30:
                value_label.config(wraplength=300)
            
            row += 1
        
        # Error message (if any)
        if self.receipt.error_message:
            ttk.Label(main_frame, text="Error Message:", 
                     font=("TkDefaultFont", 9, "bold")).grid(
                row=row, column=0, sticky=(tk.W, tk.N), padx=(0, 10), pady=(10, 2))
            
            error_text = tk.Text(main_frame, height=4, wrap=tk.WORD, 
                                font=("TkDefaultFont", 9))
            error_text.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=(10, 2))
            error_text.insert(tk.END, self.receipt.error_message)
            error_text.config(state='disabled')
            
            row += 1
        
        # Close button
        ttk.Button(main_frame, text="Close", 
                  command=self.dialog.destroy).grid(row=row, column=0, columnspan=2, pady=(20, 0))
    
    def _center_dialog(self):
        """Center dialog on parent."""
        self.dialog.update_idletasks()
        
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        dialog_width = self.dialog.winfo_width()
        dialog_height = self.dialog.winfo_height()
        
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")


class StatisticsDialog:
    """Dialog showing comprehensive receipt statistics."""
    
    def __init__(self, parent: tk.Toplevel, database: ReceiptDatabase):
        """Initialize the statistics dialog."""
        self.parent = parent
        self.database = database
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Receipt Database Statistics")
        self.dialog.geometry("700x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self._setup_gui()
        self._load_statistics()
        self._center_dialog()
    
    def _setup_gui(self):
        """Setup the statistics GUI."""
        main_frame = ttk.Frame(self.dialog, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.dialog.columnconfigure(0, weight=1)
        self.dialog.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, 
                               text="📊 Receipt Database Statistics", 
                               font=("TkDefaultFont", 14, "bold"))
        title_label.grid(row=0, column=0, pady=(0, 15))
        
        # Statistics text area
        self.stats_text = tk.Text(main_frame, wrap=tk.WORD, font=("Consolas", 10))
        self.stats_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.stats_text.yview)
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        self.stats_text.config(yscrollcommand=scrollbar.set)
        
        # Close button
        ttk.Button(main_frame, text="Close", 
                  command=self.dialog.destroy).grid(row=2, column=0, pady=(15, 0))
    
    def _load_statistics(self):
        """Load and display statistics."""
        def load_in_background():
            try:
                stats = self.database.get_statistics()
                
                # Format comprehensive statistics
                stats_text = self._format_statistics(stats)
                
                # Update UI in main thread
                self.dialog.after(0, lambda: [
                    self.stats_text.delete(1.0, tk.END),
                    self.stats_text.insert(tk.END, stats_text),
                    self.stats_text.config(state='disabled')
                ])
                
            except Exception as e:
                logger.error(f"Failed to load statistics: {e}")
                self.dialog.after(0, lambda: [
                    self.stats_text.delete(1.0, tk.END),
                    self.stats_text.insert(tk.END, f"Error loading statistics:\n{str(e)}"),
                    self.stats_text.config(state='disabled')
                ])
        
        threading.Thread(target=load_in_background, daemon=True).start()
    
    def _format_statistics(self, stats: Dict[str, Any]) -> str:
        """Format statistics for display."""
        lines = []
        lines.append("═" * 60)
        lines.append("RECEIPT DATABASE STATISTICS")
        lines.append("═" * 60)
        lines.append()
        
        # Overall statistics
        lines.append("📋 OVERALL STATISTICS:")
        lines.append("─" * 40)
        total = stats.get('total_receipts', 0)
        successful = stats.get('successful_receipts', 0)
        failed = stats.get('failed_receipts', 0)
        dry_run = stats.get('dry_run_receipts', 0)
        total_value = stats.get('total_value', 0)
        real_value = stats.get('real_total_value', 0)
        unique_contracts = stats.get('unique_contracts', 0)
        
        lines.append(f"Total Receipts:        {total:,}")
        lines.append(f"Successful:            {successful:,}")
        lines.append(f"Failed:                {failed:,}")
        lines.append(f"Dry Run:               {dry_run:,}")
        lines.append(f"Real Receipts:         {total - dry_run:,}")
        lines.append(f"Unique Contracts:      {unique_contracts:,}")
        lines.append()
        
        # Success rate
        if total > 0:
            success_rate = (successful / total) * 100
            lines.append(f"Success Rate:          {success_rate:.1f}%")
        lines.append()
        
        # Financial statistics
        lines.append("💰 FINANCIAL STATISTICS:")
        lines.append("─" * 40)
        lines.append(f"Total Value (all):     €{total_value:,.2f}")
        lines.append(f"Real Value (issued):   €{real_value:,.2f}")
        
        avg_value = stats.get('average_value', 0)
        if avg_value > 0:
            lines.append(f"Average Value:         €{avg_value:.2f}")
        lines.append()
        
        # Time statistics
        lines.append("⏰ TIME STATISTICS:")
        lines.append("─" * 40)
        earliest = stats.get('earliest_receipt')
        latest = stats.get('latest_receipt')
        active_days = stats.get('active_days', 0)
        
        if earliest:
            lines.append(f"First Receipt:         {earliest[:19].replace('T', ' ')}")
        if latest:
            lines.append(f"Latest Receipt:        {latest[:19].replace('T', ' ')}")
        lines.append(f"Active Days:           {active_days}")
        lines.append()
        
        # Status breakdown
        status_breakdown = stats.get('status_breakdown', {})
        if status_breakdown:
            lines.append("📊 STATUS BREAKDOWN:")
            lines.append("─" * 40)
            for status, count in status_breakdown.items():
                percentage = (count / total * 100) if total > 0 else 0
                lines.append(f"{status:15} {count:>6,} ({percentage:5.1f}%)")
            lines.append()
        
        # Monthly breakdown
        monthly_data = stats.get('monthly_breakdown', [])
        if monthly_data:
            lines.append("📅 MONTHLY BREAKDOWN (Last 12 months):")
            lines.append("─" * 40)
            lines.append(f"{'Month':>7} {'Count':>8} {'Value':>12}")
            lines.append("─" * 40)
            
            for month_data in monthly_data:
                month = month_data['month']
                count = month_data['count']
                value = month_data['total_value'] or 0
                lines.append(f"{month:>7} {count:>8,} €{value:>10,.2f}")
        
        lines.append()
        lines.append("═" * 60)
        lines.append(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return "\n".join(lines)
    
    def _center_dialog(self):
        """Center dialog on parent."""
        self.dialog.update_idletasks()
        
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        dialog_width = self.dialog.winfo_width()
        dialog_height = self.dialog.winfo_height()
        
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
