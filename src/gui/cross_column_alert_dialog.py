"""
Cross-column payment alert dialog.

Displays alerts for payments found in unexpected month columns
(late payments, early payments, etc.)
"""

import tkinter as tk
from tkinter import ttk
from typing import List

try:
    from excel_preprocessor import ProcessingAlert
    from utils.logger import get_logger
except ImportError:
    from src.excel_preprocessor import ProcessingAlert
    from src.utils.logger import get_logger

logger = get_logger(__name__)


class CrossColumnAlertDialog(tk.Toplevel):
    """
    Dialog to display cross-column payment alerts.
    
    Shows user when payments are found in unexpected month columns,
    which may indicate late payments or other anomalies.
    """
    
    def __init__(self, parent, alerts: List[ProcessingAlert]):
        """
        Initialize alert dialog.
        
        Args:
            parent: Parent window
            alerts: List of ProcessingAlert objects
        """
        super().__init__(parent)
        
        self.alerts = alerts
        self.result = False
        
        self.title("Cross-Column Payment Alerts")
        self.geometry("700x500")
        self.resizable(True, True)
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        
        self._setup_gui()
        
        # Center dialog
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
    
    def _setup_gui(self):
        """Setup dialog GUI."""
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        icon_label = ttk.Label(header_frame, text="⚠️", font=("Segoe UI", 24))
        icon_label.pack(side=tk.LEFT, padx=(0, 10))
        
        header_text_frame = ttk.Frame(header_frame)
        header_text_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        title_label = ttk.Label(header_text_frame, 
                               text="Cross-Column Payments Detected",
                               font=("Segoe UI", 12, "bold"))
        title_label.pack(anchor=tk.W)
        
        subtitle_label = ttk.Label(
            header_text_frame,
            text=f"Found {len(self.alerts)} payments in unexpected month columns",
            font=("Segoe UI", 9),
            foreground="gray"
        )
        subtitle_label.pack(anchor=tk.W)
        
        # Explanation
        explanation_frame = ttk.Frame(main_frame, relief="solid", borderwidth=1, padding="5")
        explanation_frame.pack(fill=tk.X, pady=(0, 10))
        
        explanation_text = (
            "The following payments were found in different month columns than expected.\n"
            "This typically indicates late or early payments. Review the details below\n"
            "to ensure rent periods are calculated correctly."
        )
        ttk.Label(explanation_frame, text=explanation_text, foreground="blue").pack(anchor=tk.W)
        
        # Alert list
        list_frame = ttk.LabelFrame(main_frame, text="Alert Details", padding="5")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Create Treeview
        tree_frame = ttk.Frame(list_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Treeview
        columns = ("Contract", "Payment Date", "Payment Column", "Expected Column", "Rent Period")
        self.alert_tree = ttk.Treeview(tree_frame, columns=columns, show="headings",
                                      yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        vsb.config(command=self.alert_tree.yview)
        hsb.config(command=self.alert_tree.xview)
        
        # Configure columns
        self.alert_tree.heading("Contract", text="Contract")
        self.alert_tree.heading("Payment Date", text="Payment Date")
        self.alert_tree.heading("Payment Column", text="Found In")
        self.alert_tree.heading("Expected Column", text="Expected In")
        self.alert_tree.heading("Rent Period", text="Rent Period")
        
        self.alert_tree.column("Contract", width=100)
        self.alert_tree.column("Payment Date", width=100)
        self.alert_tree.column("Payment Column", width=90)
        self.alert_tree.column("Expected Column", width=90)
        self.alert_tree.column("Rent Period", width=200)
        
        self.alert_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Populate alerts
        for alert in self.alerts:
            rent_period = f"{alert.rent_period_from.strftime('%Y-%m-%d')} to {alert.rent_period_to.strftime('%Y-%m-%d')}"
            values = (
                alert.contract_number,
                alert.payment_date.strftime("%Y-%m-%d"),
                alert.payment_column,
                alert.expected_column,
                rent_period
            )
            self.alert_tree.insert("", tk.END, values=values)
        
        # Bind selection to show reason
        self.alert_tree.bind("<<TreeviewSelect>>", self._on_alert_selected)
        
        # Reason display
        reason_frame = ttk.LabelFrame(main_frame, text="Alert Reason", padding="5")
        reason_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.reason_text = tk.Text(reason_frame, height=3, wrap=tk.WORD, 
                                   font=("Segoe UI", 9), state="disabled")
        self.reason_text.pack(fill=tk.X)
        
        # Show first alert reason
        if self.alerts:
            self._show_reason(self.alerts[0].reason)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="OK", command=self._on_ok, width=15).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Auto-select first item
        if self.alert_tree.get_children():
            first_item = self.alert_tree.get_children()[0]
            self.alert_tree.selection_set(first_item)
            self.alert_tree.focus(first_item)
    
    def _on_alert_selected(self, event):
        """Handle alert selection in tree."""
        selection = self.alert_tree.selection()
        if not selection:
            return
        
        # Get selected alert index
        item = selection[0]
        index = self.alert_tree.index(item)
        
        if 0 <= index < len(self.alerts):
            alert = self.alerts[index]
            self._show_reason(alert.reason)
    
    def _show_reason(self, reason: str):
        """Display alert reason in text widget."""
        self.reason_text.config(state="normal")
        self.reason_text.delete("1.0", tk.END)
        self.reason_text.insert("1.0", reason)
        self.reason_text.config(state="disabled")
    
    def _on_ok(self):
        """Handle OK button click."""
        self.result = True
        logger.debug(f"User acknowledged {len(self.alerts)} cross-column alerts")
        self.destroy()
    
    def show(self) -> bool:
        """
        Show dialog and wait for user response.
        
        Returns:
            True if user clicked OK
        """
        self.wait_window()
        return self.result


def show_cross_column_alerts(parent, alerts: List[ProcessingAlert]) -> bool:
    """
    Convenience function to show cross-column alert dialog.
    
    Args:
        parent: Parent window
        alerts: List of ProcessingAlert objects
    
    Returns:
        True if user acknowledged alerts
    """
    if not alerts:
        return True
    
    dialog = CrossColumnAlertDialog(parent, alerts)
    return dialog.show()
