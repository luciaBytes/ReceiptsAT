"""
Receipt processor - handles the main business logic for issuing receipts.
"""

from typing import List, Dict, Any, Callable
from dataclasses import dataclass
from datetime import datetime
import time

from csv_handler import ReceiptData
from web_client import WebClient
from utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class ProcessingResult:
    """Result of processing a single receipt."""
    contract_id: str
    tenant_name: str = ""
    success: bool = False
    receipt_number: str = ""
    from_date: str = ""
    to_date: str = ""
    payment_date: str = ""
    value: float = 0.0
    error_message: str = ""
    timestamp: str = ""

class ReceiptProcessor:
    """Main processor for handling receipt issuance."""
    
    def __init__(self, web_client: WebClient):
        self.web_client = web_client
        self.results: List[ProcessingResult] = []
        self.dry_run = False
    
    def set_dry_run(self, dry_run: bool):
        """Enable or disable dry run mode."""
        self.dry_run = dry_run
        logger.info(f"Dry run mode: {'enabled' if dry_run else 'disabled'}")
    
    def process_receipts_bulk(self, receipts: List[ReceiptData], 
                            progress_callback: Callable[[int, int, str], None] = None) -> List[ProcessingResult]:
        """
        Process all receipts in bulk mode.
        
        Args:
            receipts: List of receipts to process
            progress_callback: Optional callback for progress updates (current, total, message)
            
        Returns:
            List of processing results
        """
        logger.info(f"Starting bulk processing of {len(receipts)} receipts")
        self.results.clear()
        
        for i, receipt in enumerate(receipts):
            if progress_callback:
                progress_callback(i + 1, len(receipts), f"Processing contract {receipt.contract_id}")
            
            result = self._process_single_receipt(receipt)
            self.results.append(result)
            
            # Small delay to avoid overwhelming the server
            if not self.dry_run:
                time.sleep(1)
        
        logger.info(f"Bulk processing completed. Success: {self._count_successful()}, Failed: {self._count_failed()}")
        return self.results.copy()
    
    def process_receipts_step_by_step(self, receipts: List[ReceiptData],
                                    confirmation_callback: Callable[[ReceiptData, Dict], str]) -> List[ProcessingResult]:
        """
        Process receipts in step-by-step mode with user confirmation.
        
        Args:
            receipts: List of receipts to process
            confirmation_callback: Callback for user confirmation (receipt_data, form_data) -> action
                                  Returns: 'confirm', 'skip', 'cancel', or 'edit:new_data'
            
        Returns:
            List of processing results
        """
        logger.info(f"Starting step-by-step processing of {len(receipts)} receipts")
        self.results.clear()
        
        for receipt in receipts:
            # Get form data first
            success, form_data = self.web_client.get_receipt_form(receipt.contract_id)
            
            if not success:
                result = ProcessingResult(
                    contract_id=receipt.contract_id,
                    success=False,
                    error_message="Failed to get form data",
                    timestamp=datetime.now().isoformat()
                )
                self.results.append(result)
                continue
            
            # Ask user for confirmation
            action = confirmation_callback(receipt, form_data or {})
            
            if action == 'cancel':
                logger.info("Processing cancelled by user")
                break
            elif action == 'skip':
                result = ProcessingResult(
                    contract_id=receipt.contract_id,
                    success=False,
                    error_message="Skipped by user",
                    timestamp=datetime.now().isoformat()
                )
                self.results.append(result)
                continue
            elif action.startswith('edit:'):
                # Handle edited data (would need to parse the edited data)
                # For now, just process normally
                pass
            
            # Process the receipt
            if action in ['confirm', 'edit']:
                result = self._process_single_receipt(receipt, form_data)
                self.results.append(result)
        
        logger.info(f"Step-by-step processing completed. Success: {self._count_successful()}, Failed: {self._count_failed()}")
        return self.results.copy()
    
    def _process_single_receipt(self, receipt: ReceiptData, form_data: Dict = None) -> ProcessingResult:
        """
        Process a single receipt.
        
        Args:
            receipt: Receipt data to process
            form_data: Optional form data from the platform
            
        Returns:
            Processing result
        """
        logger.info(f"Processing receipt for contract {receipt.contract_id}")
        
        result = ProcessingResult(
            contract_id=receipt.contract_id,
            from_date=receipt.from_date,
            to_date=receipt.to_date,
            value=receipt.value,
            timestamp=datetime.now().isoformat()
        )
        
        if self.dry_run:
            # Simulate successful processing in dry run
            result.success = True
            result.receipt_number = "DRY-RUN-001"
            result.tenant_name = "Test Tenant"
            result.payment_date = receipt.to_date
            logger.info(f"Dry run: Simulated successful processing for contract {receipt.contract_id}")
            return result
        
        try:
            # Get form data if not provided
            if form_data is None:
                success, form_data = self.web_client.get_receipt_form(receipt.contract_id)
                if not success:
                    result.error_message = "Failed to get form data"
                    return result
            
            # Extract tenant information from form data
            if form_data:
                result.tenant_name = self._extract_tenant_name(form_data)
            
            # Prepare receipt data for submission
            submission_data = self._prepare_submission_data(receipt, form_data)
            
            # Submit the receipt
            success, response = self.web_client.issue_receipt(submission_data)
            
            if success and response:
                result.success = True
                result.receipt_number = response.get('receiptNumber', 'Unknown')
                result.payment_date = receipt.to_date
                logger.info(f"Successfully processed receipt for contract {receipt.contract_id}")
            else:
                result.error_message = response.get('errorMessage') if response else "Unknown error"
                logger.error(f"Failed to process receipt for contract {receipt.contract_id}: {result.error_message}")
        
        except Exception as e:
            result.error_message = str(e)
            logger.error(f"Exception processing receipt for contract {receipt.contract_id}: {str(e)}")
        
        return result
    
    def _extract_tenant_name(self, form_data: Dict) -> str:
        """Extract tenant name from form data."""
        try:
            locatarios = form_data.get('locatarios', [])
            if locatarios and len(locatarios) > 0:
                return locatarios[0].get('nome', '').strip()
        except:
            pass
        return "Unknown Tenant"
    
    def _prepare_submission_data(self, receipt: ReceiptData, form_data: Dict) -> Dict:
        """
        Prepare data for submission to the platform.
        
        Args:
            receipt: Receipt data from CSV
            form_data: Form data from platform
            
        Returns:
            Data ready for submission
        """
        # Start with form data and update with CSV values
        submission_data = form_data.copy() if form_data else {}
        
        # Update with CSV data
        submission_data.update({
            'dataInicio': receipt.from_date,
            'dataFim': receipt.to_date,
            'dataRecebimento': receipt.to_date,  # Assuming payment date is the same as to_date
            'valor': receipt.value,
            'tipoImportancia': {'codigo': 'RENDAC'}  # Default to rent
        })
        
        return submission_data
    
    def _count_successful(self) -> int:
        """Count successful results."""
        return sum(1 for result in self.results if result.success)
    
    def _count_failed(self) -> int:
        """Count failed results."""
        return sum(1 for result in self.results if not result.success)
    
    def get_results(self) -> List[ProcessingResult]:
        """Get processing results."""
        return self.results.copy()
    
    def generate_report_data(self) -> List[Dict[str, Any]]:
        """Generate report data for export."""
        report_data = []
        
        for result in self.results:
            report_data.append({
                'Contract ID': result.contract_id,
                'Tenant Name': result.tenant_name,
                'Status': 'Success' if result.success else 'Failed',
                'Receipt Number': result.receipt_number,
                'From Date': result.from_date,
                'To Date': result.to_date,
                'Payment Date': result.payment_date,
                'Value': result.value,
                'Error Message': result.error_message,
                'Timestamp': result.timestamp
            })
        
        return report_data
