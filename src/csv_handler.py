"""
CSV Handler for processing receipt data from CSV files.
"""

import csv
import os
from datetime import datetime
from typing import List, Dict, Tuple
from dataclasses import dataclass
from utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class ReceiptData:
    """Data class for receipt information."""
    contract_id: str
    from_date: str
    to_date: str
    receipt_type: str
    value: float
    row_number: int = 0

class CSVHandler:
    """Handles CSV file operations for receipt data."""
    
    REQUIRED_COLUMNS = ['contractId', 'fromDate', 'toDate', 'receiptType', 'value']
    
    def __init__(self):
        self.receipts: List[ReceiptData] = []
        self.validation_errors: List[str] = []
    
    def load_csv(self, file_path: str) -> Tuple[bool, List[str]]:
        """
        Load and validate CSV file.
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            Tuple of (success, error_messages)
        """
        if not os.path.exists(file_path):
            return False, ["File does not exist"]
        
        try:
            self.receipts.clear()
            self.validation_errors.clear()
            
            with open(file_path, 'r', encoding='utf-8') as file:
                # Try to detect dialect
                sample = file.read(1024)
                file.seek(0)
                dialect = csv.Sniffer().sniff(sample)
                
                reader = csv.DictReader(file, dialect=dialect)
                
                # Check required columns
                if not all(col in reader.fieldnames for col in self.REQUIRED_COLUMNS):
                    missing = [col for col in self.REQUIRED_COLUMNS if col not in reader.fieldnames]
                    return False, [f"Missing required columns: {', '.join(missing)}"]
                
                # Process each row
                for row_num, row in enumerate(reader, start=2):  # Start at 2 for header
                    try:
                        receipt = self._parse_row(row, row_num)
                        if receipt:
                            self.receipts.append(receipt)
                    except Exception as e:
                        self.validation_errors.append(f"Row {row_num}: {str(e)}")
            
            # Validate all data
            self._validate_data()
            
            if self.validation_errors:
                return False, self.validation_errors
            
            logger.info(f"Successfully loaded {len(self.receipts)} receipts from {file_path}")
            return True, []
            
        except Exception as e:
            logger.error(f"Error loading CSV file: {str(e)}")
            return False, [f"Error reading file: {str(e)}"]
    
    def _parse_row(self, row: Dict[str, str], row_num: int) -> ReceiptData:
        """Parse a single CSV row into ReceiptData."""
        try:
            # Parse value
            value = float(row['value'].replace(',', '.'))
            
            return ReceiptData(
                contract_id=row['contractId'].strip(),
                from_date=row['fromDate'].strip(),
                to_date=row['toDate'].strip(),
                receipt_type=row['receiptType'].strip(),
                value=value,
                row_number=row_num
            )
        except ValueError as e:
            raise ValueError(f"Invalid data format: {str(e)}")
    
    def _validate_data(self):
        """Validate all receipt data."""
        for receipt in self.receipts:
            self._validate_receipt(receipt)
    
    def _validate_receipt(self, receipt: ReceiptData):
        """Validate a single receipt."""
        # Validate contract ID
        if not receipt.contract_id:
            self.validation_errors.append(f"Row {receipt.row_number}: Contract ID cannot be empty")
        
        # Validate dates
        try:
            from_date = datetime.strptime(receipt.from_date, '%Y-%m-%d')
            to_date = datetime.strptime(receipt.to_date, '%Y-%m-%d')
            
            if from_date > to_date:
                self.validation_errors.append(
                    f"Row {receipt.row_number}: From date ({receipt.from_date}) cannot be later than to date ({receipt.to_date})"
                )
            
            # Check if payment date is in the future (assuming payment date is to_date for now)
            if to_date > datetime.now():
                self.validation_errors.append(
                    f"Row {receipt.row_number}: Payment date ({receipt.to_date}) cannot be in the future"
                )
                
        except ValueError:
            self.validation_errors.append(
                f"Row {receipt.row_number}: Invalid date format. Use YYYY-MM-DD"
            )
        
        # Validate value
        if receipt.value <= 0:
            self.validation_errors.append(
                f"Row {receipt.row_number}: Value must be greater than 0"
            )
        
        # Validate receipt type
        if not receipt.receipt_type:
            self.validation_errors.append(
                f"Row {receipt.row_number}: Receipt type cannot be empty"
            )
    
    def get_receipts(self) -> List[ReceiptData]:
        """Get the list of loaded receipts."""
        return self.receipts.copy()
    
    def export_report(self, report_data: List[Dict], file_path: str) -> bool:
        """
        Export report data to CSV.
        
        Args:
            report_data: List of dictionaries containing report data
            file_path: Path to save the report
            
        Returns:
            Success status
        """
        try:
            if not report_data:
                return False
            
            with open(file_path, 'w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=report_data[0].keys())
                writer.writeheader()
                writer.writerows(report_data)
            
            logger.info(f"Report exported to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting report: {str(e)}")
            return False
