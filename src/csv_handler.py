"""
CSV Handler for processing receipt data from CSV files.
"""

import csv
import os
from datetime import datetime
from typing import List, Dict, Tuple
from dataclasses import dataclass

try:
    from .utils.logger import get_logger
except ImportError:
    # Fallback for when imported directly
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
    payment_date: str = ""  # Optional payment date field
    payment_date_defaulted: bool = False  # Track if payment_date was defaulted
    value_defaulted: bool = False  # Track if value was defaulted from contract
    receipt_type_defaulted: bool = False  # Track if receipt_type was defaulted to 'rent'
    row_number: int = 0

class CSVHandler:
    """Handles CSV file operations for receipt data."""
    
    REQUIRED_COLUMNS = ['contractId', 'fromDate', 'toDate']
    OPTIONAL_COLUMNS = ['value', 'paymentDate', 'receiptType']  # Value, paymentDate, and receiptType are optional
    
    # Column aliases for flexibility (alternative column names)
    COLUMN_ALIASES = {
        'contractId': ['contract_id', 'contract', 'contractid', 'contract_number'],
        'fromDate': ['from_date', 'start_date', 'startdate', 'from', 'start'],
        'toDate': ['to_date', 'end_date', 'enddate', 'to', 'end'],
        'receiptType': ['receipt_type', 'type', 'receipttype'],
        'paymentDate': ['payment_date', 'paid_date', 'paymentdate', 'paid', 'payment'],
        'value': ['amount', 'rent', 'price', 'total']
    }
    
    def __init__(self):
        self.receipts: List[ReceiptData] = []
        self.validation_errors: List[str] = []
        self.column_mapping: Dict[str, str] = {}  # Maps CSV columns to standard names
    
    def load_csv(self, file_path: str) -> Tuple[bool, List[str]]:
        """
        Load and validate CSV file. Column order is flexible - uses header names.
        
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
            self.column_mapping.clear()
            
            with open(file_path, 'r', encoding='utf-8') as file:
                # Try to detect dialect
                sample = file.read(1024)
                file.seek(0)
                dialect = csv.Sniffer().sniff(sample)
                
                reader = csv.DictReader(file, dialect=dialect)
                
                # Build column mapping from CSV headers to standard names
                success, mapping_errors = self._build_column_mapping(reader.fieldnames)
                if not success:
                    return False, mapping_errors
                
                logger.info(f"Column mapping: {self.column_mapping}")
                
                # Process each row
                for row_num, row in enumerate(reader, start=2):  # Start at 2 for header
                    try:
                        receipt = self._parse_row(row, row_num)
                        if receipt:
                            # Validate the receipt before adding it
                            temp_errors = []
                            original_errors = self.validation_errors.copy()
                            self.validation_errors = temp_errors
                            
                            self._validate_receipt(receipt)
                            
                            # If validation passed, add the receipt
                            if not temp_errors:
                                self.receipts.append(receipt)
                            
                            # Add any validation errors to the main list
                            original_errors.extend(temp_errors)
                            self.validation_errors = original_errors
                            
                    except Exception as e:
                        self.validation_errors.append(f"Row {row_num}: {str(e)}")
            
            # Final validation summary
            logger.info(f"CSV processing completed:")
            logger.info(f"  Total rows processed: {row_num - 1 if 'row_num' in locals() else 0}")
            logger.info(f"  Valid receipts loaded: {len(self.receipts)}")
            logger.info(f"  Validation errors: {len(self.validation_errors)}")
            
            if self.validation_errors:
                return False, self.validation_errors
            
            logger.info(f"Successfully loaded {len(self.receipts)} receipts from {file_path}")
            return True, []
            
        except Exception as e:
            logger.error(f"Error loading CSV file: {str(e)}")
            return False, [f"Error reading file: {str(e)}"]
    
    def _build_column_mapping(self, csv_columns: List[str]) -> Tuple[bool, List[str]]:
        """
        Build mapping from CSV column names to standard column names.
        Supports column aliases for flexibility.
        
        Args:
            csv_columns: List of column names from CSV header
            
        Returns:
            Tuple of (success, error_messages)
        """
        if not csv_columns:
            return False, ["CSV file has no columns"]
        
        # Normalize CSV column names (lowercase, strip spaces)
        normalized_csv_columns = [col.strip().lower() for col in csv_columns]
        
        # Find mapping for each required and optional column
        for standard_col in self.REQUIRED_COLUMNS + self.OPTIONAL_COLUMNS:
            found = False
            
            # First try exact match (case insensitive)
            standard_col_lower = standard_col.lower()
            if standard_col_lower in normalized_csv_columns:
                original_col = csv_columns[normalized_csv_columns.index(standard_col_lower)]
                self.column_mapping[standard_col] = original_col
                found = True
            else:
                # Try aliases
                aliases = self.COLUMN_ALIASES.get(standard_col, [])
                for alias in aliases:
                    if alias.lower() in normalized_csv_columns:
                        original_col = csv_columns[normalized_csv_columns.index(alias.lower())]
                        self.column_mapping[standard_col] = original_col
                        found = True
                        break
            
            # Check if required column is missing
            if not found and standard_col in self.REQUIRED_COLUMNS:
                all_possible = [standard_col] + self.COLUMN_ALIASES.get(standard_col, [])
                return False, [f"Missing required column '{standard_col}'. Looked for: {', '.join(all_possible)}"]
        
        # Report found columns
        logger.info("Column mapping established:")
        for standard, csv_col in self.column_mapping.items():
            logger.info(f"  {standard} -> '{csv_col}'")
        
        return True, []
    
    def _parse_row(self, row: Dict[str, str], row_num: int) -> ReceiptData:
        """Parse a single CSV row into ReceiptData using flexible column mapping."""
        try:
            # Use column mapping to get values
            def get_mapped_value(standard_col: str) -> str:
                csv_col = self.column_mapping.get(standard_col)
                if csv_col and csv_col in row:
                    return row[csv_col].strip()
                return ''
            
            # Handle optional value with fallback
            value_str = get_mapped_value('value')
            value_defaulted = False
            if value_str:
                # Parse provided value
                value = float(value_str.replace(',', '.'))
            else:
                # Use fallback value of 0.0 - will be filled from contract data later
                value = 0.0
                value_defaulted = True
            
            # Handle payment date (optional - defaults to to_date if not provided)
            payment_date = get_mapped_value('paymentDate')
            payment_date_defaulted = False
            if not payment_date:
                # Default to end date of the rental period if not provided
                payment_date = get_mapped_value('toDate')
                payment_date_defaulted = True
            
            # Handle receipt type (optional - defaults to 'rent' if not provided)
            receipt_type = get_mapped_value('receiptType')
            receipt_type_defaulted = False
            if not receipt_type:
                # Default to 'rent' if not provided
                receipt_type = 'rent'
                receipt_type_defaulted = True
            
            # Validate payment date format
            try:
                datetime.strptime(payment_date, '%Y-%m-%d')
            except ValueError:
                raise ValueError(f"Row {row_num}: paymentDate must be in YYYY-MM-DD format, got '{payment_date}'")
            
            return ReceiptData(
                contract_id=get_mapped_value('contractId'),
                from_date=get_mapped_value('fromDate'),
                to_date=get_mapped_value('toDate'),
                receipt_type=receipt_type,
                value=value,
                payment_date=payment_date,
                payment_date_defaulted=payment_date_defaulted,
                value_defaulted=value_defaulted,
                receipt_type_defaulted=receipt_type_defaulted,
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
            payment_date = datetime.strptime(receipt.payment_date, '%Y-%m-%d')
            current_date = datetime.now()
            
            # Check if from_date is later than to_date
            if from_date > to_date:
                self.validation_errors.append(
                    f"Row {receipt.row_number}: From date ({receipt.from_date}) cannot be later than to date ({receipt.to_date})"
                )
            
            # Check if payment date is in the future
            if payment_date.date() > current_date.date():
                self.validation_errors.append(
                    f"Row {receipt.row_number}: Payment date ({receipt.payment_date}) cannot be in the future"
                )
                
        except ValueError as e:
            self.validation_errors.append(
                f"Row {receipt.row_number}: Invalid date format. Use YYYY-MM-DD. Error: {str(e)}"
            )
        
        # Validate value (allow 0.0 as fallback, but negative values are invalid)
        if receipt.value < 0:
            self.validation_errors.append(
                f"Row {receipt.row_number}: Value cannot be negative (got {receipt.value})"
            )
        
        # Validate receipt type
        if not receipt.receipt_type:
            self.validation_errors.append(
                f"Row {receipt.row_number}: Receipt type cannot be empty"
            )
    
    def get_receipts(self) -> List[ReceiptData]:
        """Get the list of loaded receipts."""
        return self.receipts.copy()
    
    def get_contract_ids(self) -> List[str]:
        """
        Extract unique contract IDs from loaded receipt data.
        
        Returns:
            List of unique contract IDs
        """
        if not self.receipts:
            logger.warning("No receipt data loaded")
            return []
        
        contract_ids = list(set(receipt.contract_id for receipt in self.receipts))
        logger.info(f"Extracted {len(contract_ids)} unique contract IDs from CSV: {contract_ids}")
        return sorted(contract_ids)
    
    def get_contracts_summary(self) -> Dict[str, int]:
        """
        Get summary of contract IDs and their receipt counts.
        
        Returns:
            Dictionary mapping contract IDs to number of receipts
        """
        summary = {}
        for receipt in self.receipts:
            contract_id = receipt.contract_id
            summary[contract_id] = summary.get(contract_id, 0) + 1
        
        logger.info(f"Contract summary: {summary}")
        return summary

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
