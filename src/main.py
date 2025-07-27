"""
Receipts Project - Main Application Entry Point
Automates the issuance of rent receipts for multiple tenants.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sys
import os

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gui.main_window import MainWindow
from utils.logger import setup_logger

def main():
    """Main entry point for the application."""
    # Setup logging
    logger = setup_logger()
    logger.info("Starting Receipts Application")
    
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
