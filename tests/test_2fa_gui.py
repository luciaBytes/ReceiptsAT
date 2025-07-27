#!/usr/bin/env python3
"""
Test the 2FA GUI integration by creating a simple test application.
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.web_client import WebClient

def test_2fa_gui():
    """Test 2FA GUI integration."""
    print("Testing 2FA GUI Integration...")
    
    # Create a simple test window
    root = tk.Tk()
    root.title("2FA Test")
    root.geometry("400x300")
    
    web_client = WebClient(testing_mode=True)
    
    # Create simple login interface
    frame = ttk.Frame(root, padding="20")
    frame.pack(fill=tk.BOTH, expand=True)
    
    ttk.Label(frame, text="2FA Authentication Test", font=("Arial", 14, "bold")).pack(pady=(0, 20))
    
    ttk.Label(frame, text="Test Credentials:").pack(anchor=tk.W)
    ttk.Label(frame, text="• Normal login: demo / demo").pack(anchor=tk.W)
    ttk.Label(frame, text="• 2FA login: 2fa / demo").pack(anchor=tk.W, pady=(0, 10))
    
    # Username and password
    login_frame = ttk.Frame(frame)
    login_frame.pack(fill=tk.X, pady=(0, 10))
    
    ttk.Label(login_frame, text="Username:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
    username_entry = ttk.Entry(login_frame, width=20)
    username_entry.grid(row=0, column=1, sticky=tk.W)
    username_entry.insert(0, "2fa")  # Default to 2FA test
    
    ttk.Label(login_frame, text="Password:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
    password_entry = ttk.Entry(login_frame, width=20, show="*")
    password_entry.grid(row=1, column=1, sticky=tk.W, pady=(5, 0))
    password_entry.insert(0, "demo")
    
    # Status label
    status_label = ttk.Label(frame, text="Ready to test", foreground="blue")
    status_label.pack(pady=(10, 0))
    
    def handle_login():
        username = username_entry.get()
        password = password_entry.get()
        
        status_label.config(text="Authenticating...", foreground="orange")
        root.update()
        
        success, message = web_client.login(username, password)
        
        if success:
            status_label.config(text="Authentication successful!", foreground="green")
            messagebox.showinfo("Success", "Login successful!")
        elif message == "2FA_REQUIRED":
            status_label.config(text="2FA verification required", foreground="orange")
            show_2fa_dialog()
        else:
            status_label.config(text="Authentication failed", foreground="red")
            messagebox.showerror("Error", f"Login failed: {message}")
    
    def show_2fa_dialog():
        """Show 2FA verification dialog."""
        dialog = tk.Toplevel(root)
        dialog.title("SMS Verification")
        dialog.geometry("350x200")
        dialog.resizable(False, False)
        dialog.transient(root)
        dialog.grab_set()
        
        # Center dialog
        dialog.geometry("+%d+%d" % (
            root.winfo_rootx() + 50,
            root.winfo_rooty() + 50
        ))
        
        dialog_frame = ttk.Frame(dialog, padding="20")
        dialog_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(dialog_frame, text="SMS Verification", font=("Arial", 12, "bold")).pack(pady=(0, 10))
        ttk.Label(dialog_frame, text="Enter the SMS verification code:").pack(pady=(0, 10))
        
        code_entry = ttk.Entry(dialog_frame, width=15, font=("Arial", 12))
        code_entry.pack(pady=(0, 10))
        code_entry.focus()
        
        ttk.Label(dialog_frame, text="Test codes: 123456, 000000, 111111", 
                 font=("Arial", 9), foreground="gray").pack(pady=(0, 10))
        
        def verify_code():
            sms_code = code_entry.get().strip()
            if not sms_code:
                messagebox.showerror("Error", "Please enter the SMS code")
                return
            
            dialog.destroy()
            
            success, message = web_client.login("", "", sms_code)
            if success:
                status_label.config(text="2FA verification successful!", foreground="green")
                messagebox.showinfo("Success", "2FA verification successful!")
            else:
                status_label.config(text="2FA verification failed", foreground="red")
                messagebox.showerror("Error", f"2FA verification failed: {message}")
        
        def cancel():
            dialog.destroy()
            status_label.config(text="2FA verification cancelled", foreground="gray")
        
        button_frame = ttk.Frame(dialog_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Verify", command=verify_code).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=cancel).pack(side=tk.RIGHT)
        
        code_entry.bind('<Return>', lambda e: verify_code())
    
    # Login button
    ttk.Button(frame, text="Login", command=handle_login).pack(pady=(10, 0))
    
    # Instructions
    ttk.Label(frame, text="\nTest Instructions:\n"
                         "1. Click Login with the pre-filled 2FA credentials\n"
                         "2. You should see a 2FA dialog appear\n"
                         "3. Enter one of the test codes (123456, 000000, 111111)\n"
                         "4. Click Verify to complete authentication",
             font=("Arial", 9), foreground="gray").pack(pady=(20, 0))
    
    print("✅ 2FA GUI test window created")
    print("📱 Use credentials '2fa' / 'demo' to trigger 2FA")
    print("🔑 Test SMS codes: 123456, 000000, 111111")
    
    # Don't run the main loop in this test - just show it's working
    root.update()
    root.after(2000, root.destroy)  # Close after 2 seconds
    root.mainloop()

if __name__ == "__main__":
    test_2fa_gui()
