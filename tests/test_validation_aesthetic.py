"""
Test the validation dialog aesthetic changes
"""
import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def create_test_validation_results():
    """Create test validation results in the expected format"""
    return {
        'portal_contracts_count': 2,
        'csv_contracts_count': 3,
        'valid_contracts': ['C001', 'C002'],
        'valid_contracts_data': [
            {'numero': 'C001', 'valor': 500.0, 'proprietario': 'Proprietário A', 'inquilino': 'Inquilino A'},
            {'numero': 'C002', 'valor': 750.0, 'proprietario': 'Proprietário B', 'inquilino': 'Inquilino B'}
        ],
        'invalid_contracts': [
            {'numero': 'C003', 'valor': 600.0, 'proprietario': 'Proprietário C', 'inquilino': 'Inquilino C', 'reason': 'Not found in portal'}
        ],
        'missing_from_csv': [],
        'validation_errors': ['Some validation issue example'],
        'portal_contracts': [
            {'id': 'C001', 'value': 500.0, 'landlord': 'Proprietário A', 'tenant': 'Inquilino A'},
            {'id': 'C002', 'value': 750.0, 'landlord': 'Proprietário B', 'tenant': 'Inquilino B'}
        ],
        'csv_contracts': [
            {'id': 'C001', 'value': 500.0, 'landlord': 'Proprietário A', 'tenant': 'Inquilino A'},
            {'id': 'C002', 'value': 750.0, 'landlord': 'Proprietário B', 'tenant': 'Inquilino B'},
            {'id': 'C003', 'value': 600.0, 'landlord': 'Proprietário C', 'tenant': 'Inquilino C'}
        ]
    }

def test_validation_dialog():
    """Test the validation dialog with messagebox aesthetic"""
    # Import here to avoid issues if GUI is not available
    try:
        from gui.main_window import ValidationResultDialog
        from csv_handler import CSVHandler
        
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        
        # Create test data
        validation_results = create_test_validation_results()
        
        # Create a CSV handler for export functionality
        csv_handler = CSVHandler()
        
        print("🎯 Testing ValidationResultDialog with messagebox aesthetic...")
        print("   • Non-copyable text display")
        print("   • Export button positioned right next to OK")
        print("   • Standard messagebox layout and appearance")
        print("   • Same export functionality as main window")
        
        # Create and show the dialog
        dialog = ValidationResultDialog(root, validation_results, csv_handler)
        
        # The dialog will be modal and will block until closed
        print("✅ Dialog created successfully!")
        print("   Check the dialog appearance:")
        print("   - Icon on left side")
        print("   - Message text on right (not selectable)")
        print("   - Export button next to OK button")
        print("   - Clean messagebox aesthetic")
        
        root.mainloop()
        
    except ImportError as e:
        print(f"❌ Could not import GUI components: {e}")
        print("   This is expected if running without display")
    except Exception as e:
        print(f"❌ Error testing dialog: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 80)
    print("VALIDATION DIALOG AESTHETIC TEST")
    print("=" * 80)
    test_validation_dialog()
