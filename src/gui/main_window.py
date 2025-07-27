"""
Main window GUI for the receipts application.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
from typing import Dict, Any

from csv_handler import CSVHandler
from web_client import WebClient
from receipt_processor import ReceiptProcessor, ProcessingResult
from utils.logger import get_logger

logger = get_logger(__name__)

class MainWindow:
    """Main application window."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Receipts Processor")
        self.root.geometry("800x600")
        
        # Initialize components
        self.csv_handler = CSVHandler()
        self.web_client = WebClient()
        self.processor = ReceiptProcessor(self.web_client)
        
        # Variables
        self.csv_file_path = tk.StringVar()
        self.mode_var = tk.StringVar(value="bulk")
        self.dry_run_var = tk.BooleanVar(value=False)
        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar(value="Ready")
        
        # Setup GUI
        self._setup_gui()
        
        # Thread for background operations
        self.processing_thread = None
        
    def _setup_gui(self):
        """Setup the GUI components."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Login section
        login_frame = ttk.LabelFrame(main_frame, text="Authentication", padding="5")
        login_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        login_frame.columnconfigure(1, weight=1)
        
        ttk.Label(login_frame, text="Username:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.username_entry = ttk.Entry(login_frame, width=30)
        self.username_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        ttk.Label(login_frame, text="Password:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        self.password_entry = ttk.Entry(login_frame, show="*", width=30)
        self.password_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        self.login_button = ttk.Button(login_frame, text="Login", command=self._login)
        self.login_button.grid(row=0, column=2, rowspan=2, padx=(5, 0))
        
        self.connection_status = ttk.Label(login_frame, text="Not connected", foreground="red")
        self.connection_status.grid(row=2, column=0, columnspan=3, pady=(5, 0))
        
        # CSV file section
        csv_frame = ttk.LabelFrame(main_frame, text="CSV File", padding="5")
        csv_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        csv_frame.columnconfigure(1, weight=1)
        
        ttk.Label(csv_frame, text="File:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        ttk.Entry(csv_frame, textvariable=self.csv_file_path, state="readonly").grid(
            row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5)
        )
        ttk.Button(csv_frame, text="Browse", command=self._browse_csv_file).grid(row=0, column=2)
        
        # Options section
        options_frame = ttk.LabelFrame(main_frame, text="Options", padding="5")
        options_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Processing mode
        ttk.Label(options_frame, text="Mode:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        ttk.Radiobutton(options_frame, text="Bulk", variable=self.mode_var, value="bulk").grid(
            row=0, column=1, sticky=tk.W
        )
        ttk.Radiobutton(options_frame, text="Step-by-step", variable=self.mode_var, value="step").grid(
            row=0, column=2, sticky=tk.W, padx=(10, 0)
        )
        
        # Dry run option
        ttk.Checkbutton(options_frame, text="Dry run (test mode)", variable=self.dry_run_var).grid(
            row=1, column=0, columnspan=3, sticky=tk.W, pady=(5, 0)
        )
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=(0, 10))
        
        self.start_button = ttk.Button(button_frame, text="Start Processing", 
                                      command=self._start_processing, state="disabled")
        self.start_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_button = ttk.Button(button_frame, text="Stop", 
                                     command=self._stop_processing, state="disabled")
        self.stop_button.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(button_frame, text="Export Report", command=self._export_report).pack(side=tk.LEFT)
        
        # Progress section
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="5")
        progress_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        status_label = ttk.Label(progress_frame, textvariable=self.status_var)
        status_label.grid(row=1, column=0, sticky=tk.W)
        
        # Log section
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="5")
        log_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(5, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, width=80)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Test connection on startup
        self._test_connection()
    
    def _test_connection(self):
        """Test connection to the platform."""
        def test():
            success, message = self.web_client.test_connection()
            self.root.after(0, lambda: self._update_connection_status(success, message))
        
        threading.Thread(target=test, daemon=True).start()
    
    def _update_connection_status(self, success: bool, message: str):
        """Update connection status in GUI."""
        if success:
            self.connection_status.config(text="Connected", foreground="green")
        else:
            self.connection_status.config(text=f"Connection failed: {message}", foreground="red")
    
    def _login(self):
        """Handle login button click."""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter username and password")
            return
        
        def login():
            success, message = self.web_client.login(username, password)
            self.root.after(0, lambda: self._handle_login_result(success, message))
        
        self.login_button.config(state="disabled")
        self.log("INFO", "Attempting login...")
        threading.Thread(target=login, daemon=True).start()
    
    def _handle_login_result(self, success: bool, message: str):
        """Handle login result."""
        self.login_button.config(state="normal")
        
        if success:
            self.connection_status.config(text="Authenticated", foreground="green")
            self.log("INFO", "Login successful")
            self._update_start_button_state()
        else:
            self.connection_status.config(text="Authentication failed", foreground="red")
            self.log("ERROR", f"Login failed: {message}")
            messagebox.showerror("Login Failed", message)
    
    def _browse_csv_file(self):
        """Browse for CSV file."""
        file_path = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if file_path:
            self.csv_file_path.set(file_path)
            self._validate_csv_file(file_path)
            self._update_start_button_state()
    
    def _validate_csv_file(self, file_path: str):
        """Validate the selected CSV file."""
        def validate():
            success, errors = self.csv_handler.load_csv(file_path)
            self.root.after(0, lambda: self._handle_csv_validation(success, errors))
        
        self.log("INFO", f"Validating CSV file: {file_path}")
        threading.Thread(target=validate, daemon=True).start()
    
    def _handle_csv_validation(self, success: bool, errors: list):
        """Handle CSV validation result."""
        if success:
            receipts = self.csv_handler.get_receipts()
            self.log("INFO", f"CSV file validated successfully. {len(receipts)} receipts loaded.")
        else:
            self.log("ERROR", "CSV validation failed:")
            for error in errors:
                self.log("ERROR", f"  {error}")
            messagebox.showerror("CSV Validation Failed", "\n".join(errors[:10]))
    
    def _update_start_button_state(self):
        """Update the state of the start button."""
        if (self.web_client.is_authenticated() and 
            self.csv_file_path.get() and 
            self.csv_handler.get_receipts()):
            self.start_button.config(state="normal")
        else:
            self.start_button.config(state="disabled")
    
    def _start_processing(self):
        """Start receipt processing."""
        if self.processing_thread and self.processing_thread.is_alive():
            return
        
        receipts = self.csv_handler.get_receipts()
        if not receipts:
            messagebox.showerror("Error", "No valid receipts to process")
            return
        
        # Set dry run mode
        self.processor.set_dry_run(self.dry_run_var.get())
        
        # Update UI
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.progress_var.set(0)
        
        # Start processing in background thread
        mode = self.mode_var.get()
        if mode == "bulk":
            self.processing_thread = threading.Thread(
                target=self._process_bulk, args=(receipts,), daemon=True
            )
        else:
            self.processing_thread = threading.Thread(
                target=self._process_step_by_step, args=(receipts,), daemon=True
            )
        
        self.processing_thread.start()
    
    def _process_bulk(self, receipts):
        """Process receipts in bulk mode."""
        self.log("INFO", f"Starting bulk processing of {len(receipts)} receipts")
        
        def progress_callback(current, total, message):
            progress = (current / total) * 100
            self.root.after(0, lambda: self._update_progress(progress, message))
            self.root.after(0, lambda: self.log("INFO", f"Progress: {current}/{total} - {message}"))
        
        try:
            results = self.processor.process_receipts_bulk(receipts, progress_callback)
            self.root.after(0, lambda: self._processing_completed(results))
        except Exception as e:
            self.root.after(0, lambda: self._processing_error(str(e)))
    
    def _process_step_by_step(self, receipts):
        """Process receipts in step-by-step mode."""
        self.log("INFO", f"Starting step-by-step processing of {len(receipts)} receipts")
        
        def confirmation_callback(receipt_data, form_data):
            # This would normally show a confirmation dialog
            # For now, just auto-confirm
            return 'confirm'
        
        try:
            results = self.processor.process_receipts_step_by_step(receipts, confirmation_callback)
            self.root.after(0, lambda: self._processing_completed(results))
        except Exception as e:
            self.root.after(0, lambda: self._processing_error(str(e)))
    
    def _update_progress(self, progress: float, message: str):
        """Update progress bar and status."""
        self.progress_var.set(progress)
        self.status_var.set(message)
    
    def _processing_completed(self, results: list):
        """Handle processing completion."""
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        
        self.log("INFO", f"Processing completed. Success: {successful}, Failed: {failed}")
        self.progress_var.set(100)
        self.status_var.set(f"Completed - Success: {successful}, Failed: {failed}")
        
        # Update UI
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        
        # Show summary
        messagebox.showinfo("Processing Complete", 
                          f"Processing completed.\nSuccessful: {successful}\nFailed: {failed}")
    
    def _processing_error(self, error_message: str):
        """Handle processing error."""
        self.log("ERROR", f"Processing error: {error_message}")
        self.status_var.set("Error occurred")
        
        # Update UI
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        
        messagebox.showerror("Processing Error", error_message)
    
    def _stop_processing(self):
        """Stop processing (placeholder - actual implementation would need thread interruption)."""
        self.log("INFO", "Stop requested")
        self.status_var.set("Stopping...")
        # In a real implementation, you'd need to implement proper thread cancellation
    
    def _export_report(self):
        """Export processing report."""
        results = self.processor.get_results()
        if not results:
            messagebox.showinfo("No Data", "No processing results to export")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Save Report",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if file_path:
            report_data = self.processor.generate_report_data()
            success = self.csv_handler.export_report(report_data, file_path)
            
            if success:
                self.log("INFO", f"Report exported to: {file_path}")
                messagebox.showinfo("Export Successful", f"Report exported to:\n{file_path}")
            else:
                self.log("ERROR", "Failed to export report")
                messagebox.showerror("Export Failed", "Failed to export report")
    
    def log(self, level: str, message: str):
        """Add a log entry to the GUI."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        
        # Also log to the logger
        if level == "INFO":
            logger.info(message)
        elif level == "ERROR":
            logger.error(message)
        elif level == "WARNING":
            logger.warning(message)
    
    def __del__(self):
        """Cleanup on destruction."""
        if hasattr(self, 'web_client'):
            self.web_client.logout()
