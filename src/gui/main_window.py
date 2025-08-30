"""
Main window GUI for the receipts application.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
from typing import Dict, Any, List
import os
from datetime import datetime

from csv_handler import CSVHandler
from web_client import WebClient
from receipt_processor import ReceiptProcessor, ProcessingResult
from gui.csv_template_dialog import show_csv_template_dialog
from utils.logger import get_logger
from utils.version import format_version_string, get_version
from utils.multilingual_localization import get_text, switch_language, get_language_button_text

logger = get_logger(__name__)

class MainWindow:
    """Main application window."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(get_text('MAIN_WINDOW_TITLE') + f" v{get_version()}")
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
        self.status_var = tk.StringVar(value=get_text('STATUS_READY'))
        self.session_monitor_id = None  # For tracking session monitoring
        
        # Session state tracking for proper translation updates
        self.current_session_state = "none"  # "none", "active", "expired"
        self.current_connection_state = "ready"  # "ready", "connecting", "connected", "error"
        
        # Setup GUI
        self._setup_gui()
        
        # Thread for background operations
        self.processing_thread = None
        self.stop_requested = False
        
    def _setup_gui(self):
        """Setup the GUI components."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Language selection button in top-right corner of main window
        self.language_button = ttk.Button(main_frame, text=get_language_button_text(), 
                                         command=self._switch_language, width=3)
        self.language_button.grid(row=0, column=1, sticky=(tk.E, tk.N), pady=(0, 10))
        
        # Login section
        self.login_frame = ttk.LabelFrame(main_frame, text=get_text('AUTHENTICATION_SECTION'), padding="5")
        self.login_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        self.login_frame.columnconfigure(1, weight=1)
        
        self.username_label = ttk.Label(self.login_frame, text=get_text('USERNAME_LABEL'))
        self.username_label.grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.username_entry = ttk.Entry(self.login_frame, width=30)
        self.username_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        self.password_label = ttk.Label(self.login_frame, text=get_text('PASSWORD_LABEL'))
        self.password_label.grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        
        # Create password frame to hold entry and toggle button
        password_frame = ttk.Frame(self.login_frame)
        password_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        password_frame.columnconfigure(0, weight=1)
        
        self.password_entry = ttk.Entry(password_frame, show="*", width=25)
        self.password_entry.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Add password visibility toggle button
        self.password_visible = False
        self.toggle_password_btn = ttk.Button(password_frame, text="👁", width=3, 
                                            command=self._toggle_password_visibility)
        self.toggle_password_btn.grid(row=0, column=1, padx=(2, 0))
        
        # Add tooltips to the entry fields
        self._create_tooltip(self.username_entry, 
                           "Enter your Autenticação.Gov credentials:\n" +
                           "• Citizen Card number\n" +
                           "• Email address\n" +
                           "• NIF (Tax ID)")
        
        self._create_tooltip(self.password_entry, 
                           "Enter your Autenticação.Gov account password")
        
        # Add tooltip to password toggle button
        self._create_tooltip(self.toggle_password_btn, 
                           "Click to show/hide password\nKeyboard shortcut: Ctrl+Shift+P")
        
        # Bind keyboard shortcut for password toggle
        self.root.bind('<Control-Shift-P>', lambda e: self._toggle_password_visibility())
        
        # Login and Logout buttons frame 
        buttons_frame = ttk.Frame(self.login_frame)
        buttons_frame.grid(row=0, column=2, rowspan=2, padx=(5, 0))
        
        self.login_button = ttk.Button(buttons_frame, text=get_text('LOGIN_BUTTON'), command=self._login)
        self.login_button.grid(row=0, column=0, pady=(0, 2))
        
        self.logout_button = ttk.Button(buttons_frame, text=get_text('LOGOUT_BUTTON'), command=self._logout, state="disabled")
        self.logout_button.grid(row=1, column=0)
        
        self.connection_status = ttk.Label(self.login_frame, text=get_text('CONNECTION_STATUS_READY'), foreground="blue")
        self.connection_status.grid(row=2, column=0, columnspan=3, pady=(5, 0))
        
        # Add session status information
        self.session_status = ttk.Label(self.login_frame, text=get_text('SESSION_STATUS_NONE'), foreground="gray")
        self.session_status.grid(row=3, column=0, columnspan=3, pady=(2, 0))
        
        # Remove the authentication info label since we have tooltips now
        
        # CSV file section
        self.csv_frame = ttk.LabelFrame(main_frame, text=get_text('CSV_FILE_SECTION'), padding="5")
        self.csv_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        self.csv_frame.columnconfigure(1, weight=1)
        
        self.file_label = ttk.Label(self.csv_frame, text=get_text('FILE_LABEL'))
        self.file_label.grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        ttk.Entry(self.csv_frame, textvariable=self.csv_file_path, state="readonly").grid(
            row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5)
        )
        
        # Make buttons the same width by using a consistent width parameter
        button_width = 18  # Increased to accommodate "Generate Template" text
        self.browse_button = ttk.Button(self.csv_frame, text=get_text('BROWSE_BUTTON'), command=self._browse_csv_file, width=button_width)
        self.browse_button.grid(row=0, column=2)
        
        # CSV Template Generator button - placed below Browse button, same width, text only
        self.generate_template_button = ttk.Button(self.csv_frame, text=get_text('GENERATE_TEMPLATE_BUTTON'), command=self._generate_csv_template, width=button_width)
        self.generate_template_button.grid(row=1, column=2, pady=(5, 0))
        
        # CSV help label
        self.help_label = ttk.Label(
            self.csv_frame, 
            text=get_text('CSV_HELP_TEXT'),
            font=("Segoe UI", 8),
            foreground="gray"
        )
        self.help_label.grid(row=2, column=0, columnspan=3, pady=(5, 0), sticky=tk.W)
        
        # Options section
        self.options_frame = ttk.LabelFrame(main_frame, text=get_text('OPTIONS_SECTION'), padding="5")
        self.options_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Processing mode
        self.mode_label = ttk.Label(self.options_frame, text=get_text('MODE_LABEL'))
        self.mode_label.grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.bulk_mode_radio = ttk.Radiobutton(self.options_frame, text=get_text('BULK_MODE'), variable=self.mode_var, value="bulk")
        self.bulk_mode_radio.grid(row=0, column=1, sticky=tk.W)
        self.step_mode_radio = ttk.Radiobutton(self.options_frame, text=get_text('STEP_BY_STEP_MODE'), variable=self.mode_var, value="step")
        self.step_mode_radio.grid(row=0, column=2, sticky=tk.W, padx=(10, 0))
        
        # Dry run option
        self.testing_mode_checkbox = ttk.Checkbutton(self.options_frame, text=get_text('TESTING_MODE'), variable=self.dry_run_var)
        self.testing_mode_checkbox.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(5, 0))
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=(0, 10))
        
        self.start_button = ttk.Button(button_frame, text=get_text('PROCESS_RECEIPTS_BUTTON'), 
                                      command=self._start_processing, state="disabled")
        self.start_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_button = ttk.Button(button_frame, text=get_text('CANCEL_BUTTON'), 
                                     command=self._stop_processing, state="disabled")
        self.stop_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.validate_button = ttk.Button(button_frame, text=get_text('VALIDATE_CONTRACTS_BUTTON'), 
                                         command=self._validate_contracts, state="disabled")
        self.validate_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.export_results_button = ttk.Button(button_frame, text=get_text('EXPORT_RESULTS_BUTTON'), command=self._export_report)
        self.export_results_button.pack(side=tk.LEFT)
        
        # Progress section
        self.progress_frame = ttk.LabelFrame(main_frame, text=get_text('STATUS_SECTION'), padding="5")
        self.progress_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        self.progress_frame.columnconfigure(0, weight=1)
        
        self.progress_bar = ttk.Progressbar(self.progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        status_label = ttk.Label(self.progress_frame, textvariable=self.status_var)
        status_label.grid(row=1, column=0, sticky=tk.W)
        
        # Log section
        self.log_frame = ttk.LabelFrame(main_frame, text=get_text('LOG_SECTION'), padding="5")
        self.log_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.log_frame.columnconfigure(0, weight=1)
        self.log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(6, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(self.log_frame, height=10, width=80)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Version info at bottom
        version_frame = ttk.Frame(main_frame)
        version_frame.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        
        version_label = ttk.Label(version_frame, text=format_version_string(), 
                                 font=("TkDefaultFont", 8), foreground="gray")
        version_label.pack(side=tk.LEFT)
        
        # Don't test connection on startup - wait for user to click login
    
    def _create_tooltip(self, widget, text):
        """Create a tooltip for a widget."""
        def show_tooltip(event):
            try:
                tooltip = tk.Toplevel()
                tooltip.wm_overrideredirect(True)
                tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
                
                label = tk.Label(tooltip, text=text, background="lightyellow", 
                               relief="solid", borderwidth=1, font=("TkDefaultFont", 8))
                label.pack()
                
                # Store tooltip reference to destroy it later
                widget.tooltip = tooltip
            except tk.TclError:
                # Widget might be destroyed, ignore
                pass
        
        def hide_tooltip(event):
            try:
                if hasattr(widget, 'tooltip'):
                    widget.tooltip.destroy()
                    del widget.tooltip
            except (tk.TclError, AttributeError):
                # Widget might be destroyed, ignore
                pass
        
        widget.bind("<Enter>", show_tooltip)
        widget.bind("<Leave>", hide_tooltip)
    
    def _toggle_password_visibility(self):
        """Toggle password visibility in the password field."""
        if self.password_visible:
            # Hide password
            self.password_entry.config(show="*")
            self.toggle_password_btn.config(text="👁")
            self.password_visible = False
        else:
            # Show password
            self.password_entry.config(show="")
            self.toggle_password_btn.config(text="🙈")
            self.password_visible = True
    
    def _switch_language(self):
        """Switch between Portuguese and English languages."""
        try:
            new_language = switch_language()
            logger.info(f"Language switched to: {new_language}")
            
            # Update the interface with new language
            self._refresh_interface_text()
                
        except Exception as e:
            logger.error(f"Failed to switch language: {e}")
            messagebox.showerror(get_text('ERROR_TITLE'), get_text('LANGUAGE_SWITCH_FAILED_MESSAGE').format(error=str(e)))
    
    def _refresh_interface_text(self):
        """Refresh all interface text elements with current language."""
        try:
            # Update window title
            self.root.title(get_text('MAIN_WINDOW_TITLE') + f" v{get_version()}")
            
            # Update language button text (shows the OTHER language)
            self.language_button.config(text=get_language_button_text())
            
            # Update main button texts
            self.login_button.config(text=get_text('LOGIN_BUTTON'))
            self.logout_button.config(text=get_text('LOGOUT_BUTTON'))
            self.start_button.config(text=get_text('PROCESS_RECEIPTS_BUTTON'))
            self.stop_button.config(text=get_text('CANCEL_BUTTON'))
            self.validate_button.config(text=get_text('VALIDATE_CONTRACTS_BUTTON'))
            
            # Update status labels based on stored state
            if self.current_session_state == "active":
                self.session_status.config(text=get_text('SESSION_STATUS_ACTIVE'))
            elif self.current_session_state == "expired":
                self.session_status.config(text=get_text('SESSION_STATUS_EXPIRED'))
            else:
                self.session_status.config(text=get_text('SESSION_STATUS_NONE'))
                
            if self.current_connection_state == "ready":
                self.connection_status.config(text=get_text('CONNECTION_STATUS_READY'))
            elif self.current_connection_state == "connecting":
                self.connection_status.config(text=get_text('CONNECTION_STATUS_CONNECTING'))
            elif self.current_connection_state == "connected":
                self.connection_status.config(text=get_text('CONNECTION_STATUS_CONNECTED'))
            elif self.current_connection_state == "error":
                self.connection_status.config(text=get_text('CONNECTION_STATUS_ERROR'))
                
            self.status_var.set(get_text('STATUS_READY'))
            
            # Update frame titles
            self.login_frame.config(text=get_text('AUTHENTICATION_SECTION'))
            self.csv_frame.config(text=get_text('CSV_FILE_SECTION'))
            self.options_frame.config(text=get_text('OPTIONS_SECTION'))
            self.progress_frame.config(text=get_text('STATUS_SECTION'))
            self.log_frame.config(text=get_text('LOG_SECTION'))
            
            # Update buttons with new language
            self.browse_button.config(text=get_text('BROWSE_BUTTON'))
            self.generate_template_button.config(text=get_text('GENERATE_TEMPLATE_BUTTON'))
            self.export_results_button.config(text=get_text('EXPORT_RESULTS_BUTTON'))
            
            # Update field labels
            self.username_label.config(text=get_text('USERNAME_LABEL'))
            self.password_label.config(text=get_text('PASSWORD_LABEL'))
            self.file_label.config(text=get_text('FILE_LABEL'))
            self.mode_label.config(text=get_text('MODE_LABEL'))
            
            # Update radio buttons and checkbox
            self.bulk_mode_radio.config(text=get_text('BULK_MODE'))
            self.step_mode_radio.config(text=get_text('STEP_BY_STEP_MODE'))
            self.testing_mode_checkbox.config(text=get_text('TESTING_MODE'))
            
            # Update help text
            self.help_label.config(text=get_text('CSV_HELP_TEXT'))
            
        except Exception as e:
            logger.error(f"Failed to refresh interface text: {e}")
    
    def _start_session_monitoring(self):
        """Start periodic session status monitoring."""
        def check_session():
            if self.web_client.is_authenticated():
                # Test session by trying to get contracts list
                success, _ = self.web_client.get_contracts_list()
                if success:
                    self.root.after(0, lambda: self._update_session_status(True, "Session active"))
                else:
                    self.root.after(0, lambda: self._update_session_status(False, "Session expired"))
            else:
                self.root.after(0, lambda: self._update_session_status(False, "No active session"))
        
        # Check session every 5 minutes
        def schedule_next_check():
            if self.web_client.is_authenticated() and self.session_monitor_id is not None:
                threading.Thread(target=check_session, daemon=True).start()
                self.session_monitor_id = self.root.after(300000, schedule_next_check)  # 5 minutes = 300000ms
        
        # Start the monitoring
        self.session_monitor_id = True  # Mark as active
        schedule_next_check()
    
    def _stop_session_monitoring(self):
        """Stop session monitoring."""
        if self.session_monitor_id:
            if isinstance(self.session_monitor_id, str):  # If it's an actual after() ID
                self.root.after_cancel(self.session_monitor_id)
            self.session_monitor_id = None
    
    def _update_session_status(self, active: bool, message: str):
        """Update session status in GUI."""
        if active:
            self.session_status.config(text=message, foreground="green")
        else:
            self.session_status.config(text=message, foreground="red")
            if "expired" in message.lower():
                self.log("WARNING", "Session expired - please login again")
                # Update authentication status
                self.connection_status.config(text="Session expired", foreground="orange")
                self._update_start_button_state()
    
    def _login(self):
        """Handle login button click."""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror(get_text('ERROR_TITLE'), get_text('ENTER_USERNAME_PASSWORD_MESSAGE'))
            return
        
        def login():
            # Test connection first, then login
            success, message = self.web_client.test_connection()
            if not success:
                self.root.after(0, lambda: self._handle_connection_error(message))
                return

            # Connection successful, proceed with login
            success, message = self.web_client.login(username, password)
            self.root.after(0, lambda: self._handle_login_result(success, message))
        
        self.login_button.config(state="disabled")
        
        # Update state variables
        self.current_connection_state = "connecting"
        
        # Update UI elements
        self.connection_status.config(text="Connecting...", foreground="orange")
        self.log("INFO", "Testing connection and attempting login...")
        threading.Thread(target=login, daemon=True).start()
    
    def _handle_connection_error(self, error_message):
        """Handle connection error."""
        self.login_button.config(state="normal")
        
        # Update state variables
        self.current_connection_state = "error"
        self.current_session_state = "none"
        
        # Update UI elements
        self.connection_status.config(text=f"Connection failed: {error_message}", foreground="red")
        self.session_status.config(text=get_text('SESSION_STATUS_NONE'), foreground="gray")
        self.log("ERROR", f"Connection failed: {error_message}")
        messagebox.showerror(get_text('CONNECTION_FAILED_TITLE'), get_text('CONNECTION_FAILED_MESSAGE').format(error=error_message))
    
    def _handle_login_result(self, success: bool, message: str):
        """Handle login result."""
        self.login_button.config(state="normal")
        
        if success:
            # Update state variables
            self.current_connection_state = "connected" 
            self.current_session_state = "active"
            
            # Update UI elements
            self.connection_status.config(text=get_text('STATUS_AUTHENTICATED'), foreground="green")
            self.session_status.config(text=get_text('SESSION_STATUS_ACTIVE'), foreground="green")
            self.log("INFO", "Login successful")
            
            # Update button states for authenticated user
            self.login_button.config(state="disabled")
            self.logout_button.config(state="normal")
            
            self._update_start_button_state()
            
            # Start periodic session check
            self._start_session_monitoring()
        elif message == "2FA_REQUIRED":
            # Show 2FA dialog for SMS verification
            self.connection_status.config(text="2FA verification required", foreground="orange")
            self.session_status.config(text="Waiting for SMS code", foreground="orange")
            self.log("INFO", "2FA verification required - SMS code needed")
            self._show_2fa_dialog()
        elif message == "2FA_INCORRECT_CODE":
            # Show 2FA dialog with error message for incorrect code
            self.connection_status.config(text="Incorrect SMS code", foreground="red")
            self.session_status.config(text="Waiting for correct SMS code", foreground="orange")
            self.log("ERROR", "2FA verification failed - incorrect SMS code")
            self._show_2fa_dialog("Código SMS incorreto. Por favor, tente novamente.")
        elif message == "2FA_CODE_EXPIRED":
            # Show 2FA dialog with error message for expired code
            self.connection_status.config(text="SMS code expired", foreground="red")
            self.session_status.config(text="Request new SMS code", foreground="orange")
            self.log("ERROR", "2FA verification failed - SMS code expired")
            self._show_2fa_dialog("Código SMS expirado. Por favor, solicite um novo código.")
        elif message == "2FA_NO_SENDS_REMAINING":
            # No more SMS sends available
            self.connection_status.config(text="No SMS sends remaining", foreground="red")
            self.session_status.config(text="Wait or use alternative auth", foreground="red")
            self.log("ERROR", "2FA verification failed - no SMS sends remaining")
            messagebox.showerror(get_text('TWO_FA_ERROR_TITLE'), get_text('SMS_LIMIT_REACHED_MESSAGE'))
        else:
            self.connection_status.config(text="Authentication failed", foreground="red")
            self.session_status.config(text="No active session", foreground="gray")
            self.log("ERROR", f"Login failed: {message}")
            messagebox.showerror(get_text('LOGIN_FAILED_TITLE'), message)
    
    def _logout(self):
        """Handle logout button click."""
        def logout():
            # Call logout method if it exists in web_client
            if hasattr(self.web_client, 'logout'):
                success, message = self.web_client.logout()
                self.root.after(0, lambda: self._handle_logout_result(success, message))
            else:
                # Simple logout by clearing session
                self.web_client.authenticated = False
                self.root.after(0, lambda: self._handle_logout_result(True, "Logged out successfully"))
        
        self.logout_button.config(state="disabled")
        self.connection_status.config(text="Logging out...", foreground="orange")
        self.log("INFO", "Logging out...")
        threading.Thread(target=logout, daemon=True).start()
    
    def _handle_logout_result(self, success: bool, message: str):
        """Handle logout result."""
        if success:
            # Update state variables
            self.current_connection_state = "ready"
            self.current_session_state = "none"
            
            # Update UI elements
            self.connection_status.config(text="Logged out", foreground="gray")
            self.session_status.config(text="No active session", foreground="gray")
            self.log("INFO", "Logout successful")
            
            # Update button states for logged out user
            self.login_button.config(state="normal")
            self.logout_button.config(state="disabled")
            
            # Clear password field for security
            self.password_entry.delete(0, tk.END)
            
            # Update start button state
            self._update_start_button_state()
            
            # Stop session monitoring
            self._stop_session_monitoring()
        else:
            self.logout_button.config(state="normal")
            self.log("ERROR", f"Logout failed: {message}")
            messagebox.showerror(get_text('LOGOUT_FAILED_TITLE'), message)

    def _show_2fa_dialog(self, error_message: str = None):
        """Show 2FA SMS verification dialog."""
        dialog = TwoFactorDialog(self.root, self._handle_2fa_code, error_message)
        dialog.show()
    
    def _handle_2fa_code(self, sms_code: str):
        """Handle SMS code submission for 2FA verification."""
        if not sms_code or not sms_code.strip():
            messagebox.showerror(get_text('ERROR_TITLE'), get_text('ENTER_SMS_CODE_MESSAGE'))
            return
        
        def verify_2fa():
            success, message = self.web_client.login("", "", sms_code.strip())
            self.root.after(0, lambda: self._handle_2fa_result(success, message))
        
        self.connection_status.config(text="Verifying SMS code...", foreground="orange")
        self.log("INFO", "Verifying 2FA SMS code...")
        threading.Thread(target=verify_2fa, daemon=True).start()
    
    def _handle_2fa_result(self, success: bool, message: str):
        """Handle 2FA verification result."""
        if success:
            # Update state variables
            self.current_connection_state = "connected"
            self.current_session_state = "active"
            
            # Update UI elements
            self.connection_status.config(text=get_text('STATUS_AUTHENTICATED'), foreground="green")
            self.session_status.config(text=get_text('SESSION_STATUS_ACTIVE'), foreground="green")
            self.log("INFO", "2FA verification successful")
            
            # Update button states for authenticated user
            self.login_button.config(state="disabled")
            self.logout_button.config(state="normal")
            
            self._update_start_button_state()
            
            # Start periodic session check
            self._start_session_monitoring()
        else:
            self.connection_status.config(text="2FA verification failed", foreground="red")
            self.session_status.config(text="No active session", foreground="gray")
            self.log("ERROR", f"2FA verification failed: {message}")
            messagebox.showerror(get_text('TWO_FA_VERIFICATION_FAILED_TITLE'), get_text('SMS_VERIFICATION_FAILED_MESSAGE').format(message=message))
            
            # Re-enable login button for retry
            self.login_button.config(state="normal")

    def _browse_csv_file(self):
        """Browse for CSV file."""
        file_path = filedialog.askopenfilename(
            title=get_text('SELECT_CSV_FILE_TITLE'),
            filetypes=[(get_text('CSV_FILE_FILTER'), "*.csv"), (get_text('ALL_FILES_FILTER'), "*.*")]
        )
        
        if file_path:
            self.csv_file_path.set(file_path)
            # Update button states immediately after file selection
            self._update_start_button_state()
            # Start validation in background
            self._validate_csv_file(file_path)
    
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
            self._update_start_button_state()
        else:
            self.log("ERROR", "CSV validation failed:")
            for error in errors:
                self.log("ERROR", f"  {error}")
            messagebox.showerror(get_text('CSV_VALIDATION_FAILED_TITLE'), "\n".join(errors[:10]))
    
    def _update_start_button_state(self):
        """Update the state of the start and validate buttons."""
        has_auth = self.web_client.is_authenticated()
        has_csv_file = bool(self.csv_file_path.get())  # Just need a file path
        receipts = self.csv_handler.get_receipts()
        has_valid_receipts = has_csv_file and bool(receipts)  # Need validated receipts
        
        # Debug logging
        self.log("DEBUG", f"Button state check: auth={has_auth}, csv_file={has_csv_file}, receipts_count={len(receipts) if receipts else 0}")
        
        # Check session status more reliably by looking at both authentication and session text
        session_text = self.session_status.cget("text").lower()
        session_ok = has_auth and "expired" not in session_text and "no active" not in session_text
        
        # Enable start button only if fully ready (authenticated, valid CSV with receipts, session OK)
        if has_auth and has_valid_receipts and session_ok:
            self.start_button.config(state="normal")
        else:
            self.start_button.config(state="disabled")
        
        # Enable validate button if authenticated and has CSV file (even without validation)
        # This allows users to validate contracts as soon as they login and select a file
        if has_auth and has_csv_file and session_ok:
            self.validate_button.config(state="normal")
        else:
            self.validate_button.config(state="disabled")
    
    def _validate_contracts(self):
        """Validate CSV contract IDs against Portal das Finanças."""
        if not self.web_client.is_authenticated():
            messagebox.showerror(get_text('ERROR_TITLE'), get_text('PLEASE_LOGIN_FIRST_MESSAGE'))
            return
        
        receipts = self.csv_handler.get_receipts()
        if not receipts:
            messagebox.showerror(get_text('ERROR_TITLE'), get_text('LOAD_VALID_CSV_FIRST_MESSAGE'))
            return
        
        def validate():
            """Run validation in background thread."""
            try:
                self.log("INFO", "Starting contract validation...")
                validation_report = self.processor.validate_contracts(receipts)
                self.root.after(0, lambda: self._show_validation_results(validation_report))
            except Exception as e:
                self.root.after(0, lambda: self._validation_error(str(e)))
        
        # Update UI
        self.validate_button.config(state="disabled")
        self.status_var.set("Validating contracts...")
        self.log("INFO", "Validating contract IDs against Portal das Finanças...")
        
        # Start validation in background thread
        threading.Thread(target=validate, daemon=True).start()
    
    def _show_validation_results(self, validation_report: Dict[str, Any]):
        """Display contract validation results with tenant information."""
        self.validate_button.config(state="normal")
        self.status_var.set("Contract validation completed")
        
        # Log detailed results
        self.log("INFO", "Contract validation completed:")
        self.log("INFO", f"  Active portal contracts: {validation_report['portal_contracts_count']}")
        self.log("INFO", f"  CSV contracts: {validation_report['csv_contracts_count']}")
        self.log("INFO", f"  Valid matches: {len(validation_report['valid_contracts'])}")
        self.log("INFO", f"  Invalid contracts: {len(validation_report['invalid_contracts'])}")
        self.log("INFO", f"  Missing from CSV: {len(validation_report['missing_from_csv'])}")
        
        # Create detailed message for popup WITH TENANT NAMES
        message_parts = []
        message_parts.append(f"📊 VALIDATION SUMMARY (Active Contracts Only):")
        message_parts.append(f"Active portal contracts: {validation_report['portal_contracts_count']}")
        message_parts.append(f"CSV contracts: {validation_report['csv_contracts_count']}")
        message_parts.append(f"Valid matches: {len(validation_report['valid_contracts'])}")
        
        # Show VALID CONTRACTS with tenant names
        if validation_report.get('valid_contracts_data'):
            message_parts.append(f"\n✅ VALID CONTRACTS:")
            for contract in validation_report['valid_contracts_data']:
                contract_id = contract.get('numero') or contract.get('referencia', 'N/A')
                tenant_name = contract.get('nomeLocatario', 'Unknown')
                rent_amount = contract.get('valorRenda', 0)
                property_addr = contract.get('imovelAlternateId', 'N/A')
                status = contract.get('estado', {}).get('label', 'Unknown')
                
                message_parts.append(f"  • {contract_id} → {tenant_name}")
                message_parts.append(f"    €{rent_amount:.2f} - {property_addr} ({status})")
        
        # Show INVALID CONTRACTS (in CSV but not in portal)
        if validation_report['invalid_contracts']:
            message_parts.append(f"\n❌ INVALID CONTRACTS (not found in active portal contracts):")
            for contract in validation_report['invalid_contracts']:
                message_parts.append(f"  • {contract}")
        
        # Show MISSING FROM CSV (active contracts in portal but not in CSV)
        if validation_report.get('missing_from_csv_data'):
            message_parts.append(f"\n⚠️ ACTIVE PORTAL CONTRACTS NOT IN CSV:")
            for contract in validation_report['missing_from_csv_data']:
                contract_id = contract.get('numero') or contract.get('referencia', 'N/A')
                tenant_name = contract.get('nomeLocatario', 'Unknown')
                rent_amount = contract.get('valorRenda', 0)
                property_addr = contract.get('imovelAlternateId', 'N/A')
                
                message_parts.append(f"  • {contract_id} → {tenant_name}")
                message_parts.append(f"    €{rent_amount:.2f} - {property_addr}")
        
        if validation_report['validation_errors']:
            message_parts.append(f"\n🔍 VALIDATION ISSUES:")
            for error in validation_report['validation_errors']:
                message_parts.append(f"  • {error}")
        
        # Show results in message box with export option
        message = "\n".join(message_parts)
        
        # Show results with custom dialog that has export functionality
        ValidationResultDialog(self.root, validation_report, self.csv_handler).show()
    
    def _validation_error(self, error_message: str):
        """Handle validation error."""
        self.validate_button.config(state="normal")
        self.status_var.set("Contract validation failed")
        self.log("ERROR", f"Contract validation error: {error_message}")
        messagebox.showerror(get_text('VALIDATION_ERROR_TITLE'), get_text('CONTRACT_VALIDATION_FAILED_MESSAGE').format(error=error_message))

    def _start_processing(self):
        """Start receipt processing."""
        if self.processing_thread and self.processing_thread.is_alive():
            return
        
        receipts = self.csv_handler.get_receipts()
        if not receipts:
            messagebox.showerror(get_text('ERROR_TITLE'), get_text('NO_VALID_RECEIPTS_MESSAGE'))
            return
        
        # Set dry run mode
        self.processor.set_dry_run(self.dry_run_var.get())
        
        # Reset stop flag
        self.stop_requested = False
        
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
            if self.stop_requested:
                return  # Don't update progress if stopping
            progress = (current / total) * 100
            self.root.after(0, lambda: self._update_progress(progress, message))
            self.root.after(0, lambda: self.log("INFO", f"Progress: {current}/{total} - {message}"))
        
        try:
            results = self.processor.process_receipts_bulk(
                receipts, 
                progress_callback, 
                validate_contracts=True,
                stop_check=lambda: self.stop_requested
            )
            if not self.stop_requested:
                self.root.after(0, lambda: self._processing_completed(results))
            else:
                self.root.after(0, lambda: self._processing_stopped())
        except Exception as e:
            if not self.stop_requested:
                self.root.after(0, lambda: self._processing_error(str(e)))
    
    def _process_step_by_step(self, receipts):
        """Process receipts in step-by-step mode."""
        self.log("INFO", f"Starting step-by-step processing of {len(receipts)} receipts")
        
        def confirmation_callback(receipt_data, form_data):
            if self.stop_requested:
                return 'cancel'
            
            # Use thread-safe approach to show dialog on main thread
            result = [None]
            event = threading.Event()
            
            def show_dialog():
                result[0] = self._show_step_confirmation_dialog(receipt_data, form_data)
                event.set()
            
            # Schedule dialog on main thread
            self.root.after(0, show_dialog)
            
            # Wait for user response
            event.wait()
            return result[0]
        
        try:
            results = self.processor.process_receipts_step_by_step(
                receipts, 
                confirmation_callback,
                stop_check=lambda: self.stop_requested
            )
            if not self.stop_requested:
                self.root.after(0, lambda: self._processing_completed(results))
            else:
                self.root.after(0, lambda: self._processing_stopped())
        except Exception as e:
            if not self.stop_requested:
                self.root.after(0, lambda: self._processing_error(str(e)))
    
    def _update_progress(self, progress: float, message: str):
        """Update progress bar and status."""
        self.progress_var.set(progress)
        self.status_var.set(message)
    
    def _processing_completed(self, results: list):
        """Handle processing completion."""
        successful = sum(1 for r in results if r.success)
        skipped = sum(1 for r in results if not r.success and getattr(r, 'status', '') == 'Skipped')
        failed = sum(1 for r in results if not r.success and getattr(r, 'status', '') != 'Skipped')
        
        self.log("INFO", f"Processing completed. Success: {successful}, Skipped: {skipped}, Failed: {failed}")
        self.progress_var.set(100)
        
        # Create status message
        status_parts = []
        if successful > 0:
            status_parts.append(f"Success: {successful}")
        if skipped > 0:
            status_parts.append(f"Skipped: {skipped}")
        if failed > 0:
            status_parts.append(f"Failed: {failed}")
        
        status_message = f"Completed - {', '.join(status_parts)}"
        self.status_var.set(status_message)
        
        # Update UI
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        
        # Show summary with better breakdown
        summary_parts = []
        if successful > 0:
            summary_parts.append(f"Successful: {successful}")
        if skipped > 0:
            summary_parts.append(f"Skipped (invalid contracts): {skipped}")
        if failed > 0:
            summary_parts.append(f"Failed: {failed}")
        
        summary_message = f"Processing completed.\n{chr(10).join(summary_parts)}"
        
        if failed > 0:
            messagebox.showwarning(get_text('PROCESSING_COMPLETE_TITLE'), summary_message)
        else:
            messagebox.showinfo(get_text('PROCESSING_COMPLETE_TITLE'), summary_message)
    
    def _processing_error(self, error_message: str):
        """Handle processing error."""
        self.log("ERROR", f"Processing error: {error_message}")
        self.status_var.set("Error occurred")
        
        # Check if error is session-related
        if any(keyword in error_message.lower() for keyword in ['session', 'expired', 'authentication', 'login']):
            # Update state variables
            self.current_session_state = "expired"
            self.current_connection_state = "error"
            
            # Update UI elements  
            self.session_status.config(text=get_text('SESSION_STATUS_EXPIRED'), foreground="red")
            self.connection_status.config(text=get_text('SESSION_STATUS_EXPIRED'), foreground="orange")
        
        # Update UI
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        
        messagebox.showerror(get_text('PROCESSING_ERROR_TITLE'), error_message)
    
    def _processing_stopped(self):
        """Handle processing stop."""
        self.log("INFO", "Processing stopped by user")
        self.status_var.set("Stopped")
        self.progress_var.set(0)
        
        # UI is already updated in _stop_processing, but ensure consistency
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
    
    def _stop_processing(self):
        """Stop processing by setting a flag and updating UI."""
        self.log("INFO", "Stop requested")
        self.stop_requested = True
        self.status_var.set("Stopping...")
        
        # Update UI immediately
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        
        # Reset progress
        self.progress_var.set(0)
        self.status_var.set("Ready")
    
    def _export_report(self):
        """Export processing report."""
        results = self.processor.get_results()
        if not results:
            messagebox.showinfo(get_text('INFORMATION_TITLE'), get_text('NO_PROCESSING_RESULTS_EXPORT_MESSAGE'))
            return
        
        file_path = filedialog.asksaveasfilename(
            title=get_text('SAVE_EXPORT_FILE_TITLE'),
            defaultextension=".csv",
            filetypes=[(get_text('CSV_FILE_FILTER'), "*.csv"), (get_text('ALL_FILES_FILTER'), "*.*")]
        )
        
        if file_path:
            report_data = self.processor.generate_report_data()
            success = self.csv_handler.export_report(report_data, file_path)
            
            if success:
                self.log("INFO", f"Report exported to: {file_path}")
                messagebox.showinfo(get_text('EXPORT_SUCCESSFUL_TITLE'), get_text('REPORT_EXPORTED_TO_MESSAGE').format(path=file_path))
            else:
                self.log("ERROR", "Failed to export report")
                messagebox.showerror(get_text('EXPORT_FAILED_TITLE'), get_text('EXPORT_REPORT_FAILED_MESSAGE'))
    
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
    
    def _show_step_confirmation_dialog(self, receipt_data, form_data):
        """Show confirmation dialog for step-by-step processing."""
        # Create a result variable to store the user's choice
        result = ['confirm']  # Default to confirm
        
        # Create a custom dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Step-by-Step Processing")
        dialog.geometry("600x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.geometry("+%d+%d" % (self.root.winfo_rootx() + 100, self.root.winfo_rooty() + 100))
        
        # Main frame
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Receipt information
        info_frame = ttk.LabelFrame(main_frame, text=get_text('RECEIPT_INFORMATION_SECTION'), padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Display receipt details
        ttk.Label(info_frame, text=get_text('CONTRACT_ID_LABEL').format(id=receipt_data.contract_id)).pack(anchor=tk.W)
        ttk.Label(info_frame, text=get_text('PERIOD_LABEL').format(from_date=receipt_data.from_date, to_date=receipt_data.to_date)).pack(anchor=tk.W)
        
        # Show payment date with indication if it was defaulted
        if hasattr(receipt_data, 'payment_date_defaulted') and receipt_data.payment_date_defaulted:
            payment_date_text = get_text('PAYMENT_DATE_DEFAULTED_LABEL').format(date=receipt_data.payment_date)
            payment_label = ttk.Label(info_frame, text=payment_date_text, foreground='orange')
        else:
            payment_date_text = get_text('PAYMENT_DATE_LABEL').format(date=receipt_data.payment_date)
            payment_label = ttk.Label(info_frame, text=payment_date_text)
        payment_label.pack(anchor=tk.W)
        
        # Show value with indication if it was defaulted or missing
        if hasattr(receipt_data, 'value_defaulted') and receipt_data.value_defaulted:
            value_text = get_text('VALUE_DEFAULTED_LABEL').format(value=receipt_data.value)
            value_label = ttk.Label(info_frame, text=value_text, foreground='orange')
        elif receipt_data.value == 0.0:
            value_text = get_text('VALUE_NOT_SPECIFIED_LABEL').format(value=receipt_data.value)
            value_label = ttk.Label(info_frame, text=value_text, foreground='red')
        else:
            value_text = get_text('VALUE_LABEL').format(value=receipt_data.value)
            value_label = ttk.Label(info_frame, text=value_text)
        value_label.pack(anchor=tk.W)
        
        # Show receipt type with indication if it was defaulted
        if hasattr(receipt_data, 'receipt_type_defaulted') and receipt_data.receipt_type_defaulted:
            receipt_type_text = get_text('RECEIPT_TYPE_DEFAULTED_LABEL').format(type=receipt_data.receipt_type)
            receipt_type_label = ttk.Label(info_frame, text=receipt_type_text, foreground='orange')
        else:
            receipt_type_text = get_text('RECEIPT_TYPE_LABEL').format(type=receipt_data.receipt_type)
            receipt_type_label = ttk.Label(info_frame, text=receipt_type_text)
        receipt_type_label.pack(anchor=tk.W)
        
        # Contract information (if available)
        if form_data and not form_data.get('mock'):
            contract_frame = ttk.LabelFrame(main_frame, text=get_text('CONTRACT_INFORMATION_SECTION'), padding="10")
            contract_frame.pack(fill=tk.X, pady=(0, 10))
            
            # Extract tenant info for display
            contract_details = form_data.get('contract_details', {})
            tenants = contract_details.get('locatarios', [])
            landlords = contract_details.get('locadores', [])
            
            if tenants:
                tenant_names = [t.get('nome', 'Unknown') for t in tenants]
                ttk.Label(contract_frame, text=f"Tenants: {', '.join(tenant_names)}").pack(anchor=tk.W)
            
            if landlords:
                landlord_names = [l.get('nome', 'Unknown') for l in landlords]
                ttk.Label(contract_frame, text=f"Landlords: {', '.join(landlord_names)}").pack(anchor=tk.W)
            
            property_address = contract_details.get('property_address', 'Not available')
            ttk.Label(contract_frame, text=f"Property: {property_address}").pack(anchor=tk.W)
        
        # Question frame
        question_frame = ttk.LabelFrame(main_frame, text=get_text('ACTION_SECTION'), padding="10")
        question_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(question_frame, text="Deseja processar este recibo?", font=("TkDefaultFont", 10, "bold")).pack(anchor=tk.W)
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X)
        
        def on_confirm():
            result[0] = 'confirm'
            dialog.destroy()
        
        def on_skip():
            result[0] = 'skip'
            dialog.destroy()
        
        def on_cancel():
            result[0] = 'cancel'
            dialog.destroy()
        
        # Buttons
        confirm_btn = ttk.Button(buttons_frame, text="✓ Confirm & Process", command=on_confirm, width=20)
        confirm_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        skip_btn = ttk.Button(buttons_frame, text="⏭ Skip This Receipt", command=on_skip, width=20)
        skip_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = ttk.Button(buttons_frame, text="✗ Cancel", command=on_cancel, width=20)
        cancel_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # Set focus to confirm button
        confirm_btn.focus_set()
        
        # Handle keyboard shortcuts
        def on_key(event):
            if event.keysym == 'Return':
                on_confirm()
            elif event.keysym == 'Escape':
                on_cancel()
            elif event.char.lower() == 's':
                on_skip()
        
        dialog.bind('<Key>', on_key)
        
        # Handle window close
        def on_close():
            result[0] = 'cancel'
            dialog.destroy()
        
        dialog.protocol("WM_DELETE_WINDOW", on_close)
        
        # Make dialog modal and wait for result
        dialog.wait_window()
        
        return result[0]
    
    def _generate_csv_template(self):
        """Open the CSV template generator dialog."""
        try:
            result = show_csv_template_dialog(self.root)
            if result:
                # Show simple success message without auto-loading option
                if os.path.isfile(result):
                    messagebox.showinfo(
                        "Template Generated",
                        f"CSV template generated successfully!\n\nFile: {os.path.basename(result)}\n\nSaved to: {os.path.dirname(result)}",
                        parent=self.root
                    )
                else:
                    messagebox.showinfo(
                        "Templates Generated",
                        f"CSV templates generated successfully!\n\nFolder: {result}\n\nYou can find various template types in the selected folder.",
                        parent=self.root
                    )
        except Exception as e:
            logger.error(f"Error in CSV template generator: {str(e)}")
            messagebox.showerror(
                "Error",
                f"Failed to open template generator:\n\n{str(e)}",
                parent=self.root
            )
    
    def __del__(self):
        """Cleanup on destruction."""
        if hasattr(self, 'web_client'):
            self.web_client.logout()
            # Update session status on logout
            if hasattr(self, 'session_status'):
                self.session_status.config(text="No active session", foreground="gray")
                self.connection_status.config(text="Not connected", foreground="red")


class ValidationResultDialog:
    """Custom dialog for showing validation results with export functionality using messagebox aesthetic."""
    
    def __init__(self, parent, validation_report: Dict[str, Any], csv_handler):
        self.parent = parent
        self.validation_report = validation_report
        self.csv_handler = csv_handler
        self.dialog = None
        
        # Generate the message content like the original implementation
        self.message = self._generate_message()
        
        # Determine dialog type based on validation results
        self.has_issues = (validation_report.get('invalid_contracts', []) or 
                          validation_report.get('validation_errors', []))
    
    def _generate_message(self):
        """Generate the validation message content."""
        # Format validation report manually since we're using multilingual system now
        lines = []
        
        # Header summary
        lines.append(f"📊 {get_text('VALIDATION_SUMMARY', 
                                   portal_count=self.validation_report.get('portal_contracts_count', 0),
                                   csv_count=self.validation_report.get('csv_contracts_count', 0),
                                   valid_count=len(self.validation_report.get('valid_contracts', [])))}")
        
        # Valid contracts
        if self.validation_report.get('valid_contracts_data'):
            lines.append(f"\n✅ Valid Contracts:")
            for contract in self.validation_report['valid_contracts_data']:
                contract_id = contract.get('numero') or contract.get('referencia', 'N/A')
                tenant_name = contract.get('nomeLocatario', 'Unknown')
                lines.append(f"  • {contract_id} → {tenant_name}")
        
        # Invalid contracts
        if self.validation_report.get('invalid_contracts'):
            lines.append(f"\n❌ Invalid Contracts:")
            for contract in self.validation_report['invalid_contracts']:
                lines.append(f"  • {contract}")
        
        # Validation errors
        if self.validation_report.get('validation_errors'):
            lines.append(f"\n🔍 Validation Issues:")
            for error in self.validation_report['validation_errors']:
                lines.append(f"  • {error}")
        
        return "\n".join(lines)
    
    def show(self):
        """Show the validation results dialog with messagebox aesthetic."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(get_text('VALIDATION_TITLE'))
        self.dialog.resizable(False, False)
        
        # Make dialog modal
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Set icon based on validation results
        if self.has_issues:
            icon_text = "⚠️"
            icon_color = "orange"
        else:
            icon_text = "✅"
            icon_color = "green"
        
        # Create main frame with padding (messagebox style)
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Icon and message frame (horizontal layout like messagebox)
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Icon (left side)
        icon_label = ttk.Label(content_frame, text=icon_text, font=("Arial", 32))
        icon_label.pack(side=tk.LEFT, padx=(0, 15), anchor=tk.N)
        
        # Message frame with scrollbar (right side)
        message_frame = ttk.Frame(content_frame)
        message_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Create text widget with scrollbar for message content
        text_widget = tk.Text(message_frame, wrap=tk.WORD, width=60, height=20,
                             font=("Arial", 9), relief=tk.FLAT, borderwidth=0,
                             state=tk.DISABLED, background=self.dialog.cget('bg'),
                             highlightthickness=0, cursor="arrow")
        
        # Create scrollbar
        scrollbar = ttk.Scrollbar(message_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.config(yscrollcommand=scrollbar.set)
        
        # Pack scrollbar and text widget
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Insert message content into text widget
        text_widget.config(state=tk.NORMAL)
        text_widget.insert(tk.END, self.message)
        text_widget.config(state=tk.DISABLED)  # Make it read-only
        
        # Buttons frame (bottom, right-aligned like messagebox)
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        # Export button (right side, next to OK)
        export_button = ttk.Button(button_frame, text=get_text('EXPORT_REPORT_BUTTON'), 
                                  command=self._export_validation_report)
        export_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        # OK button (rightmost)
        ok_button = ttk.Button(button_frame, text=get_text('OK_BUTTON'), command=self.dialog.destroy)
        ok_button.pack(side=tk.RIGHT)
        
        # Center the dialog on parent
        self.dialog.geometry("+%d+%d" % (
            self.parent.winfo_rootx() + 50,
            self.parent.winfo_rooty() + 50
        ))
        
        # Focus on OK button
        ok_button.focus()
        
        # Bind Enter and Escape keys
        self.dialog.bind('<Return>', lambda e: self.dialog.destroy())
        self.dialog.bind('<Escape>', lambda e: self.dialog.destroy())
    
    def _export_validation_report(self):
        """Export validation results - same functionality as main window export."""
        # Check if there's data to export (same check as main window)
        if not self.validation_report:
            messagebox.showinfo(get_text('NO_DATA_TITLE'), get_text('NO_VALIDATION_RESULTS_EXPORT_MESSAGE'))
            return
        
        # Use same file dialog as main window
        file_path = filedialog.asksaveasfilename(
            title="Save Report",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if file_path:
            # Generate report data in the same format as main window
            report_data = self._generate_validation_report_data()
            
            # Use the SAME export method as main window
            success = self.csv_handler.export_report(report_data, file_path)
            
            if success:
                messagebox.showinfo(get_text('EXPORT_SUCCESSFUL_TITLE'), get_text('REPORT_EXPORTED_TO_MESSAGE').format(path=file_path))
            else:
                messagebox.showerror(get_text('EXPORT_FAILED_TITLE'), get_text('EXPORT_REPORT_FAILED_MESSAGE'))
    
    def _generate_validation_report_data(self):
        """Generate report data for validation results in same format as main window."""
        report_data = []
        
        # Add valid contracts
        if self.validation_report.get('valid_contracts_data'):
            for contract in self.validation_report['valid_contracts_data']:
                contract_id = contract.get('numero') or contract.get('referencia', 'N/A')
                tenant_name = contract.get('nomeLocatario', 'Unknown')
                landlord_name = contract.get('nomeLocador', 'Unknown')
                rent_amount = contract.get('valorRenda', 0)
                property_addr = contract.get('imovelAlternateId', 'N/A')
                status = contract.get('estado', {}).get('label', 'Unknown')
                
                report_data.append({
                    'Contract ID': contract_id,
                    'Validation Status': 'Valid',
                    'In CSV': 'Yes',
                    'In Portal': 'Yes',
                    'Tenant Name': tenant_name,
                    'Landlord Name': landlord_name,
                    'Rent Amount': f"€{rent_amount:.2f}",
                    'Property Address': property_addr,
                    'Contract Status': status,
                    'Notes': 'Contract found in both CSV and Portal (Active)'
                })
        
        # Add invalid contracts
        if self.validation_report.get('invalid_contracts'):
            for contract_id in self.validation_report['invalid_contracts']:
                report_data.append({
                    'Contract ID': contract_id,
                    'Validation Status': 'Invalid',
                    'In CSV': 'Yes',
                    'In Portal': 'No',
                    'Tenant Name': 'Unknown',
                    'Landlord Name': 'Unknown',
                    'Rent Amount': 'N/A',
                    'Property Address': 'N/A',
                    'Contract Status': 'Not Found',
                    'Notes': 'Contract in CSV but not found in active Portal contracts'
                })
        
        # Add missing from CSV
        if self.validation_report.get('missing_from_csv_data'):
            for contract in self.validation_report['missing_from_csv_data']:
                contract_id = contract.get('numero') or contract.get('referencia', 'N/A')
                tenant_name = contract.get('nomeLocatario', 'Unknown')
                landlord_name = contract.get('nomeLocador', 'Unknown')
                rent_amount = contract.get('valorRenda', 0)
                property_addr = contract.get('imovelAlternateId', 'N/A')
                status = contract.get('estado', {}).get('label', 'Unknown')
                
                report_data.append({
                    'Contract ID': contract_id,
                    'Validation Status': 'Missing from CSV',
                    'In CSV': 'No',
                    'In Portal': 'Yes',
                    'Tenant Name': tenant_name,
                    'Landlord Name': landlord_name,
                    'Rent Amount': f"€{rent_amount:.2f}",
                    'Property Address': property_addr,
                    'Contract Status': status,
                    'Notes': 'Active Portal contract not included in CSV file'
                })
        
        return report_data


class TwoFactorDialog:
    """Dialog for SMS 2FA verification."""
    
    def __init__(self, parent, callback, error_message=None):
        self.parent = parent
        self.callback = callback
        self.error_message = error_message
        self.dialog = None
        self.sms_entry = None
    
    def show(self):
        """Show the 2FA verification dialog."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(get_text('TWO_FACTOR_TITLE'))
        self.dialog.geometry("400x200")
        self.dialog.resizable(False, False)
        
        # Make dialog modal
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (
            self.parent.winfo_rootx() + 100,
            self.parent.winfo_rooty() + 100
        ))
        
        # Create main frame
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title and instructions
        title_label = ttk.Label(main_frame, text="Verificacao SMS Necessaria", 
                               font=("Arial", 12, "bold"))
        title_label.pack(pady=(0, 10))
        
        # Show error message if provided
        if self.error_message:
            error_label = ttk.Label(main_frame, text=self.error_message,
                                   font=("Arial", 10), foreground="red",
                                   wraplength=350, justify=tk.CENTER)
            error_label.pack(pady=(0, 10))
        
        info_label = ttk.Label(main_frame, 
                              text=get_text('TWO_FACTOR_MESSAGE'),
                              wraplength=350, justify=tk.CENTER)
        info_label.pack(pady=(0, 15))
        
        # SMS code entry
        code_frame = ttk.Frame(main_frame)
        code_frame.pack(pady=(0, 15))
        
        ttk.Label(code_frame, text=get_text('SMS_CODE_LABEL')).pack(side=tk.LEFT, padx=(0, 10))
        self.sms_entry = ttk.Entry(code_frame, width=15, font=("Arial", 12))
        self.sms_entry.pack(side=tk.LEFT)
        self.sms_entry.focus()
        
        # Bind Enter key to submit
        self.sms_entry.bind('<Return>', lambda e: self._submit_code())
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        verify_button = ttk.Button(button_frame, text=get_text('VERIFY_BUTTON'), command=self._submit_code)
        verify_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        cancel_button = ttk.Button(button_frame, text=get_text('CANCEL_BUTTON'), command=self._cancel)
        cancel_button.pack(side=tk.RIGHT)
        
        # Instructions
        help_label = ttk.Label(main_frame, 
                              text=get_text('TWO_FACTOR_HELP'),
                              font=("Arial", 8), foreground="gray")
        help_label.pack(pady=(10, 0))
    
    def _submit_code(self):
        """Submit the SMS code."""
        sms_code = self.sms_entry.get().strip()
        
        if not sms_code:
            messagebox.showerror(get_text('ERROR_TITLE'), get_text('ENTER_SMS_CODE_MESSAGE'))
            return
        
        if not sms_code.isdigit() or len(sms_code) != 6:
            messagebox.showerror(get_text('ERROR_TITLE'), get_text('SMS_CODE_SIX_DIGITS_MESSAGE'))
            return
        
        self.dialog.destroy()
        self.callback(sms_code)
    
    def _cancel(self):
        """Cancel 2FA verification."""
        self.dialog.destroy()
        # Could call a cancel callback here if needed
