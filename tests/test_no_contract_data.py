#!/usr/bin/env python3
"""
Test step-by-step value display when no contract data is available.
"""

import sys
import os
import tempfile

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.csv_handler import CSVHandler
from src.web_client import WebClient
from src.receipt_processor import ReceiptProcessor
from src.utils.logger import get_logger

logger = get_logger(__name__)

def test_step_by_step_no_contract_data():
    """Test step-by-step dialog when no contract data is available."""
    print("=" * 70)
    print("STEP-BY-STEP NO CONTRACT DATA TEST")
    print("=" * 70)
    
    # Test CSV with missing values
    csv_content = """contractId,fromDate,toDate,receiptType,paymentDate
999999,2024-07-01,2024-07-31,rent,2024-07-28"""
    
    # Create temporary CSV file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        f.write(csv_content)
        temp_file_path = f.name
    
    try:
        # Load CSV
        csv_handler = CSVHandler()
        success, errors = csv_handler.load_csv(temp_file_path)
        
        if success:
            receipts = csv_handler.get_receipts()
            print(f"✅ Loaded {len(receipts)} receipts from CSV")
            
            # Test step-by-step processing with mock web client (no contract data)
            web_client = WebClient()
            web_client.testing_mode = True
            web_client.authenticated = True
            
            # Empty contract cache - no data available
            web_client._cached_contracts = []
            
            processor = ReceiptProcessor(web_client)
            processor.dry_run = False
            
            # Mock get_receipt_form to return no contract data
            def mock_get_receipt_form(contract_id):
                return True, {
                    'contract_details': {}  # Empty contract details
                }
                
            web_client.get_receipt_form = mock_get_receipt_form
            
            # Track confirmation dialogs
            def mock_confirmation_callback(receipt_data, form_data):
                print(f"\n📋 Step-by-Step Dialog for Contract {receipt_data.contract_id}:")
                print(f"   Value displayed: €{receipt_data.value:.2f}")
                
                if receipt_data.value == 0.0:
                    print(f"   Status: ⚠️  Shows €0.00 (no contract data available)")
                    print(f"   User will see: 'Value: €0.00 (not specified in CSV)' in red")
                else:
                    print(f"   Status: ✅ Shows resolved value")
                
                return 'cancel'  # Cancel to avoid processing
            
            # Process receipts step-by-step
            print(f"\n🔄 Processing receipts in step-by-step mode...")
            results = processor.process_receipts_step_by_step(receipts, mock_confirmation_callback)
            
            print(f"\n📊 Summary:")
            print(f"  This test shows what happens when CSV has no value AND no contract data is available.")
            print(f"  The dialog will clearly indicate to the user that the value was 'not specified in CSV'.")
            print(f"  The actual processing would still use the _prepare_submission_data fallback logic.")
        
    finally:
        # Clean up
        try:
            os.unlink(temp_file_path)
        except:
            pass

if __name__ == "__main__":
    test_step_by_step_no_contract_data()
