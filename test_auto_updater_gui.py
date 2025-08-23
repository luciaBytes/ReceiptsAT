"""Test script for auto-updater GUI."""

import sys
import os
import tkinter as tk

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from src.gui.auto_updater_dialog import show_auto_updater_dialog
    
    print("🔄 Testing Auto-updater GUI")
    print("=" * 30)
    
    # Create test window
    root = tk.Tk()
    root.withdraw()  # Hide main window
    
    print("✅ GUI components imported successfully")
    print("✅ Opening auto-updater dialog...")
    
    # Show auto-updater dialog
    show_auto_updater_dialog(root)
    
    print("🎉 Auto-updater GUI test completed!")
    
except Exception as e:
    print(f"❌ Error testing auto-updater GUI: {e}")
    import traceback
    traceback.print_exc()
