"""
Receipt Verification and Export Module
Verifies receipts exist in Portal das Finanças and exports detailed reports.
"""

import csv
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass

try:
    from .web_client import WebClient
    from .receipt_processor import ProcessingResult
except ImportError:
    from web_client import WebClient
    from receipt_processor import ProcessingResult

try:
    from .utils.logger import get_logger
except ImportError:
    from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class VerifiedReceipt:
    """Data structure for verified receipt information."""
    contract_id: str
    contract_name: str
    tenant_name: str
    rent_date_from: str
    rent_date_to: str
    payment_date: str
    rent_value: float
    issue_date: str
    receipt_number: str
    verification_status: str  # 'Verified', 'Not Found', 'Error'
    error_message: str = ""


class ReceiptVerifier:
    """Verifies receipts in portal and exports reports."""
    
    def __init__(self, web_client: WebClient):
        """
        Initialize the receipt verifier.
        
        Args:
            web_client: Authenticated WebClient instance
        """
        self.web_client = web_client
        self.verified_receipts: List[VerifiedReceipt] = []
    
    def verify_processing_results(self, 
                                 processing_results: List[ProcessingResult]) -> List[VerifiedReceipt]:
        """
        Verify all successfully processed receipts exist in the portal.
        
        Args:
            processing_results: List of processing results from receipt processor
            
        Returns:
            List of verified receipt data
        """
        logger.info("=" * 80)
        logger.info("STARTING RECEIPT VERIFICATION")
        logger.info("=" * 80)
        
        self.verified_receipts.clear()
        
        # Filter only successful results that have receipt numbers
        successful_results = [
            r for r in processing_results 
            if r.success and r.receipt_number and r.receipt_number != "UNKNOWN"
        ]
        
        logger.info(f"Total results: {len(processing_results)}")
        logger.info(f"Successful with receipt numbers: {len(successful_results)}")
        
        if not successful_results:
            logger.warning("No successful receipts to verify")
            return self.verified_receipts
        
        # Verify each receipt in the portal
        for i, result in enumerate(successful_results, 1):
            logger.info(f"Verifying receipt {i}/{len(successful_results)}: "
                       f"Contract {result.contract_id}, Receipt #{result.receipt_number}")
            
            verified_receipt = self._verify_single_receipt(result)
            self.verified_receipts.append(verified_receipt)
        
        # Log summary
        verified_count = sum(1 for r in self.verified_receipts if r.verification_status == "Verified")
        not_found_count = sum(1 for r in self.verified_receipts if r.verification_status == "Not Found")
        error_count = sum(1 for r in self.verified_receipts if r.verification_status == "Error")
        
        logger.info("=" * 80)
        logger.info("VERIFICATION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"✅ Verified: {verified_count}")
        logger.info(f"❌ Not Found: {not_found_count}")
        logger.info(f"⚠️  Errors: {error_count}")
        logger.info("=" * 80)
        
        return self.verified_receipts
    
    def _verify_single_receipt(self, result: ProcessingResult) -> VerifiedReceipt:
        """
        Verify a single receipt exists in the portal.
        
        Args:
            result: Processing result to verify
            
        Returns:
            VerifiedReceipt object with verification status
        """
        # Initialize verified receipt with data from processing result
        verified = VerifiedReceipt(
            contract_id=result.contract_id,
            contract_name=f"Contract {result.contract_id}",  # Will be updated if available
            tenant_name=result.tenant_name or "Unknown",
            rent_date_from=result.from_date,
            rent_date_to=result.to_date,
            payment_date=result.payment_date,
            rent_value=result.value,
            issue_date=result.timestamp or datetime.now().isoformat(),
            receipt_number=result.receipt_number,
            verification_status="Unknown"
        )
        
        try:
            # Call portal to verify receipt exists
            success, receipt_details = self.web_client.verify_receipt_in_portal(
                result.contract_id, 
                result.receipt_number
            )
            
            if success and receipt_details:
                # Receipt exists in portal
                verified.verification_status = "Verified"
                
                # Update with additional details from portal if available
                if 'contract_name' in receipt_details:
                    verified.contract_name = receipt_details['contract_name']
                if 'tenant_name' in receipt_details:
                    verified.tenant_name = receipt_details['tenant_name']
                if 'issue_date' in receipt_details:
                    verified.issue_date = receipt_details['issue_date']
                    
                logger.info(f"  ✅ Verified: Receipt {result.receipt_number} exists in portal")
                
            elif success and not receipt_details:
                # Receipt not found in portal
                verified.verification_status = "Not Found"
                verified.error_message = "Receipt number not found in portal"
                logger.warning(f"  ❌ Not Found: Receipt {result.receipt_number} not in portal")
                
            else:
                # Error during verification
                verified.verification_status = "Error"
                verified.error_message = receipt_details.get('error', 'Unknown error') if isinstance(receipt_details, dict) else "Verification failed"
                logger.error(f"  ⚠️  Error: Could not verify receipt {result.receipt_number}: {verified.error_message}")
                
        except Exception as e:
            verified.verification_status = "Error"
            verified.error_message = f"Exception during verification: {str(e)}"
            logger.error(f"  ⚠️  Exception verifying receipt {result.receipt_number}: {str(e)}")
        
        return verified
    
    def export_to_csv(self, output_path: str) -> Tuple[bool, str]:
        """
        Export verified receipts to CSV file.
        
        Args:
            output_path: Path to output CSV file
            
        Returns:
            Tuple of (success, message)
        """
        if not self.verified_receipts:
            return False, "No verified receipts to export"
        
        try:
            logger.info(f"Exporting {len(self.verified_receipts)} verified receipts to: {output_path}")
            
            # Define CSV headers
            headers = [
                'Contract ID',
                'Contract Name',
                'Tenant Name',
                'Rent Period From',
                'Rent Period To',
                'Payment Date',
                'Rent Value (€)',
                'Receipt Issue Date',
                'Receipt Number',
                'Verification Status',
                'Error Message'
            ]
            
            # Write to CSV
            with open(output_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow(headers)
                
                # Write data rows
                for receipt in self.verified_receipts:
                    writer.writerow([
                        receipt.contract_id,
                        receipt.contract_name,
                        receipt.tenant_name,
                        receipt.rent_date_from,
                        receipt.rent_date_to,
                        receipt.payment_date,
                        f"{receipt.rent_value:.2f}",
                        receipt.issue_date,
                        receipt.receipt_number,
                        receipt.verification_status,
                        receipt.error_message
                    ])
            
            logger.info(f"✅ Successfully exported {len(self.verified_receipts)} receipts to CSV")
            return True, f"Successfully exported {len(self.verified_receipts)} receipts to {output_path}"
            
        except Exception as e:
            error_msg = f"Failed to export CSV: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg
    
    def get_summary_stats(self) -> Dict[str, int]:
        """
        Get summary statistics of verified receipts.
        
        Returns:
            Dictionary with counts of different verification statuses
        """
        if not self.verified_receipts:
            return {
                'total': 0,
                'verified': 0,
                'not_found': 0,
                'error': 0
            }
        
        return {
            'total': len(self.verified_receipts),
            'verified': sum(1 for r in self.verified_receipts if r.verification_status == "Verified"),
            'not_found': sum(1 for r in self.verified_receipts if r.verification_status == "Not Found"),
            'error': sum(1 for r in self.verified_receipts if r.verification_status == "Error")
        }
