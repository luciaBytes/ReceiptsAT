"""
Receipts Project - Main Application Entry Point
Automates the issuance of rent receipts for multiple tenants.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sys
import os
import platform

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gui.main_window import MainWindow
from utils.logger import setup_logger

def enable_console_logging():
    """Enable console window for Windows GUI applications"""
    if platform.system() == "Windows":
        try:
            import ctypes
            # Allocate a console for the GUI application
            ctypes.windll.kernel32.AllocConsole()
            # Redirect stdout, stderr to the console
            sys.stdout = open('CONOUT$', 'w')
            sys.stderr = open('CONOUT$', 'w')
            sys.stdin = open('CONIN$', 'r')
            print("Console logging enabled!")
        except Exception as e:
            print(f"Could not enable console: {e}")

def main():
    """Main entry point for the application."""
    # Check if debug mode is requested via command line or environment variable
    debug_mode = (
        '--debug' in sys.argv or 
        '--console' in sys.argv or 
        os.getenv('RECEIPTS_DEBUG', '').lower() in ('1', 'true', 'yes')
    )
    
    if debug_mode:
        print("Debug mode enabled - showing console")
        enable_console_logging()
    
    # Setup logging
    logger = setup_logger()
    logger.info("Starting Receipts Application")
    
    if debug_mode:
        logger.info("🐛 DEBUG MODE: Console logging enabled")
    
    try:
        # Create and run the main application
        root = tk.Tk()
        app = MainWindow(root)
        root.mainloop()
        
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        messagebox.showerror("Error", f"Application error: {str(e)}")
    
    logger.info("Application closed")

if __name__ == "__main__":
    main()
