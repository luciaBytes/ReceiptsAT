"""
Advanced CSV Processing Capabilities - Feature 3B

Enhanced data validation, flexible column support, and intelligent defaulting
for complex CSV scenarios in Portuguese tax receipt processing.
"""

import csv
import os
import re
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional, Any, Union
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

try:
    from .logger import get_logger
    from ..csv_handler import ReceiptData, CSVHandler
except ImportError:
    # Fallback for when imported directly
    from utils.logger import get_logger
    from csv_handler import ReceiptData, CSVHandler

logger = get_logger(__name__)

@dataclass
class ValidationResult:
    """Enhanced validation result with detailed analysis."""
    is_valid: bool
    errors: List[str] = None
    warnings: List[str] = None
    suggestions: List[str] = None
    row_number: int = 0
    field_name: str = ""
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.suggestions is None:
            self.suggestions = []

@dataclass 
class DataInsights:
    """Statistical insights about the CSV data."""
    total_rows: int
    valid_rows: int
    error_rows: int
    warning_rows: int
    unique_contracts: int
    date_range: Tuple[str, str]
    value_range: Tuple[float, float]
    receipt_types: Dict[str, int]
    defaulted_values: Dict[str, int]
    column_completeness: Dict[str, float]

class AdvancedCSVProcessor:
    """Advanced CSV processing with enhanced validation and intelligent defaulting."""
    
    # Extended column aliases with more variations
    EXTENDED_COLUMN_ALIASES = {
        'contractId': [
            'contract_id', 'contract', 'contractid', 'contract_number', 'contract_num',
            'id_contrato', 'numero_contrato', 'contrato', 'id_contract', 'contract_ref',
            'ref_contrato', 'referencia_contrato', 'contrato_id', 'num_contrato'
        ],
        'fromDate': [
            'from_date', 'start_date', 'startdate', 'from', 'start', 'begin_date',
            'data_inicio', 'inicio', 'data_de', 'periodo_inicio', 'de_data',
            'start_period', 'begin', 'date_from', 'period_start', 'initial_date'
        ],
        'toDate': [
            'to_date', 'end_date', 'enddate', 'to', 'end', 'final_date',
            'data_fim', 'fim', 'data_ate', 'periodo_fim', 'ate_data',
            'end_period', 'finish', 'date_to', 'period_end', 'final'
        ],
        'receiptType': [
            'receipt_type', 'type', 'receipttype', 'tipo', 'tipo_recibo',
            'categoria', 'category', 'kind', 'tipo_documento', 'document_type'
        ],
        'paymentDate': [
            'payment_date', 'paid_date', 'paymentdate', 'paid', 'payment',
            'data_pagamento', 'pagamento', 'data_recebimento', 'recebimento',
            'pay_date', 'received_date', 'settlement_date', 'data_liquidacao'
        ],
        'value': [
            'amount', 'rent', 'price', 'total', 'valor', 'quantia', 'montante',
            'renda', 'preco', 'custo', 'cost', 'sum', 'soma', 'valor_renda'
        ]
    }
    
    # Date format patterns with Portuguese support
    DATE_FORMATS = [
        '%Y-%m-%d',          # ISO format (preferred)
        '%d/%m/%Y',          # Portuguese format
        '%d-%m-%Y',          # Alternative Portuguese
        '%Y/%m/%d',          # Alternative ISO
        '%m/%d/%Y',          # US format
        '%d.%m.%Y',          # European format
        '%Y.%m.%d',          # Alternative European
    ]
    
    # Receipt type mappings and aliases
    RECEIPT_TYPE_MAPPINGS = {
        'rent': ['rent', 'renda', 'aluguel', 'arrendamento', 'locacao', 'rental'],
        'deposit': ['deposit', 'caucao', 'caução', 'fianca', 'fiança', 'deposito', 'depósito', 'garantia'],
        'utilities': ['utilities', 'despesas', 'encargos', 'condominio', 'condomínio'],
        'maintenance': ['maintenance', 'manutencao', 'manutenção', 'reparacao', 'reparação', 'obras'],
        'other': ['other', 'outro', 'varios', 'vários', 'diversos', 'extra']
    }
    
    def __init__(self, csv_handler: Optional[CSVHandler] = None):
        """Initialize with optional existing CSV handler."""
        self.csv_handler = csv_handler or CSVHandler()
        self.validation_results: List[ValidationResult] = []
        self.data_insights: Optional[DataInsights] = None
        self.auto_corrections: Dict[int, Dict[str, Any]] = {}  # Row -> field corrections
        
    def enhanced_load_csv(self, file_path: str, 
                         auto_correct: bool = True,
                         strict_validation: bool = False) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        Enhanced CSV loading with advanced validation and correction capabilities.
        
        Args:
            file_path: Path to CSV file
            auto_correct: Apply automatic corrections where possible
            strict_validation: Use strict validation rules
            
        Returns:
            Tuple of (success, errors, insights_dict)
        """
        try:
            # Reset state
            self.validation_results.clear()
            self.auto_corrections.clear()
            
            # Validate file existence and format
            file_validation = self._validate_file(file_path)
            if not file_validation.is_valid:
                return False, file_validation.errors, {}
            
            # Detect encoding and dialect
            encoding_info = self._detect_file_encoding(file_path)
            dialect_info = self._detect_csv_dialect(file_path, encoding_info['encoding'])
            
            logger.info(f"CSV file analysis:")
            logger.info(f"  Encoding: {encoding_info['encoding']} (confidence: {encoding_info['confidence']:.2f})")
            logger.info(f"  Dialect: delimiter='{dialect_info.delimiter}', quotechar='{dialect_info.quotechar}'")
            
            # Load and process CSV with enhanced column mapping
            success, errors = self._enhanced_csv_load(file_path, encoding_info['encoding'], 
                                                    dialect_info, auto_correct, strict_validation)
            
            if success:
                # Generate data insights
                self.data_insights = self._generate_data_insights()
                insights_dict = self._insights_to_dict()
                
                logger.info(f"CSV processing completed successfully:")
                logger.info(f"  Total rows: {self.data_insights.total_rows}")
                logger.info(f"  Valid rows: {self.data_insights.valid_rows}")
                logger.info(f"  Errors: {self.data_insights.error_rows}")
                logger.info(f"  Warnings: {self.data_insights.warning_rows}")
                
                return True, [], insights_dict
            else:
                return False, errors, {}
                
        except Exception as e:
            logger.error(f"Enhanced CSV loading failed: {str(e)}")
            return False, [f"Processing error: {str(e)}"], {}
    
    def _validate_file(self, file_path: str) -> ValidationResult:
        """Validate file existence, size, and basic format."""
        result = ValidationResult(is_valid=True)
        
        # Check file existence
        if not os.path.exists(file_path):
            result.is_valid = False
            result.errors.append("File does not exist")
            return result
        
        # Check file size (warn if too large)
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            result.is_valid = False
            result.errors.append("File is empty")
        elif file_size > 10 * 1024 * 1024:  # 10MB
            result.warnings.append(f"Large file detected ({file_size / 1024 / 1024:.1f}MB) - processing may be slow")
        
        # Check file extension
        _, ext = os.path.splitext(file_path)
        if ext.lower() not in ['.csv', '.txt']:
            result.warnings.append(f"Unusual file extension '{ext}' - expected .csv")
        
        return result
    
    def _detect_file_encoding(self, file_path: str) -> Dict[str, Any]:
        """Detect file encoding with fallback options."""
        try:
            import chardet
            
            try:
                with open(file_path, 'rb') as file:
                    raw_data = file.read(8192)  # Read first 8KB
                    detection = chardet.detect(raw_data)
                    
                encoding = detection['encoding'] or 'utf-8'
                confidence = detection['confidence'] or 0.0
                
                # Test the detected encoding
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        file.read(1024)  # Try to read a bit
                except UnicodeDecodeError:
                    encoding = 'utf-8'  # Fallback
                    confidence = 0.5
                    
            except Exception:
                # chardet failed, use fallback
                encoding = 'utf-8'
                confidence = 0.7
                
        except ImportError:
            # chardet not available, use simple encoding detection
            encoding, confidence = self._simple_encoding_detection(file_path)
            
        return {'encoding': encoding, 'confidence': confidence}
    
    def _simple_encoding_detection(self, file_path: str) -> Tuple[str, float]:
        """Simple encoding detection without chardet."""
        # Try common encodings in order of preference
        encodings_to_try = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
        
        for encoding in encodings_to_try:
            try:
                with open(file_path, 'r', encoding=encoding) as file:
                    file.read()  # Try to read entire file
                return encoding, 0.8  # Good confidence if successful
            except UnicodeDecodeError:
                continue
            except Exception:
                continue
        
        # If all fail, default to utf-8 with low confidence
        return 'utf-8', 0.5
    
    def _detect_csv_dialect(self, file_path: str, encoding: str) -> csv.Dialect:
        """Detect CSV dialect (delimiter, quote character, etc.)."""
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                sample = file.read(2048)
                sniffer = csv.Sniffer()
                dialect = sniffer.sniff(sample, delimiters=',;\t|')
                return dialect
        except Exception:
            # Return default dialect
            return csv.excel
    
    def _enhanced_csv_load(self, file_path: str, encoding: str, dialect: csv.Dialect,
                          auto_correct: bool, strict_validation: bool) -> Tuple[bool, List[str]]:
        """Enhanced CSV loading with advanced processing."""
        
        with open(file_path, 'r', encoding=encoding) as file:
            reader = csv.DictReader(file, dialect=dialect)
            
            # Enhanced column mapping
            column_mapping = self._build_enhanced_column_mapping(list(reader.fieldnames))
            if not column_mapping['success']:
                return False, column_mapping['errors']
            
            self.csv_handler.column_mapping = column_mapping['mapping']
            logger.info("Enhanced column mapping established:")
            for standard, csv_col in column_mapping['mapping'].items():
                logger.info(f"  {standard:15} -> '{csv_col}'")
            
            # Process rows with enhanced validation
            file.seek(0)
            reader = csv.DictReader(file, dialect=dialect)
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    receipt, validation = self._process_enhanced_row(
                        row, row_num, auto_correct, strict_validation)
                    
                    if validation.is_valid:
                        self.csv_handler.receipts.append(receipt)
                    
                    self.validation_results.append(validation)
                    
                    # Store corrections if made
                    if auto_correct and validation.is_valid and hasattr(validation, 'corrections'):
                        self.auto_corrections[row_num] = getattr(validation, 'corrections', {})
                        
                except Exception as e:
                    error_validation = ValidationResult(
                        is_valid=False,
                        errors=[f"Row processing failed: {str(e)}"],
                        row_number=row_num
                    )
                    self.validation_results.append(error_validation)
            
            # Compile final errors
            errors = []
            for result in self.validation_results:
                if not result.is_valid:
                    for error in result.errors:
                        errors.append(f"Row {result.row_number}: {error}")
            
            return len(errors) == 0, errors
    
    def _build_enhanced_column_mapping(self, csv_columns: List[str]) -> Dict[str, Any]:
        """Build enhanced column mapping with fuzzy matching."""
        if not csv_columns:
            return {'success': False, 'errors': ["CSV file has no columns"]}
        
        # Normalize column names
        normalized_columns = {}
        for i, col in enumerate(csv_columns):
            clean_col = col.strip().lower()
            clean_col = re.sub(r'[^\w\s]', '', clean_col)  # Remove special chars
            clean_col = re.sub(r'\s+', '_', clean_col)     # Replace spaces with underscore
            normalized_columns[clean_col] = col
        
        mapping = {}
        missing_required = []
        
        for standard_col in self.csv_handler.REQUIRED_COLUMNS + self.csv_handler.OPTIONAL_COLUMNS:
            found = False
            
            # Try exact match first
            standard_lower = standard_col.lower()
            if standard_lower in normalized_columns:
                mapping[standard_col] = normalized_columns[standard_lower]
                found = True
            else:
                # Try extended aliases
                aliases = self.EXTENDED_COLUMN_ALIASES.get(standard_col, [])
                for alias in aliases:
                    alias_normalized = re.sub(r'[^\w\s]', '', alias.lower())
                    alias_normalized = re.sub(r'\s+', '_', alias_normalized)
                    
                    if alias_normalized in normalized_columns:
                        mapping[standard_col] = normalized_columns[alias_normalized]
                        found = True
                        break
                
                # Try fuzzy matching for common typos
                if not found:
                    fuzzy_match = self._fuzzy_match_column(standard_col, list(normalized_columns.keys()))
                    if fuzzy_match:
                        mapping[standard_col] = normalized_columns[fuzzy_match]
                        found = True
                        logger.info(f"Fuzzy match: '{standard_col}' -> '{fuzzy_match}'")
            
            # Check if required column is missing
            if not found and standard_col in self.csv_handler.REQUIRED_COLUMNS:
                missing_required.append(standard_col)
        
        if missing_required:
            return {
                'success': False,
                'errors': [f"Missing required columns: {', '.join(missing_required)}"]
            }
        
        return {'success': True, 'mapping': mapping, 'fuzzy_matches': []}
    
    def _fuzzy_match_column(self, target: str, candidates: List[str], threshold: float = 0.6) -> Optional[str]:
        """Improved fuzzy matching for column names."""
        target_lower = target.lower()
        target_clean = re.sub(r'[^\w]', '', target_lower)
        
        # Simple character-based similarity
        best_match = None
        best_score = 0.0
        
        for candidate in candidates:
            candidate_lower = candidate.lower()
            candidate_clean = re.sub(r'[^\w]', '', candidate_lower)
            
            # Calculate multiple similarity metrics
            scores = []
            
            # 1. Character overlap similarity
            common_chars = set(target_clean) & set(candidate_clean)
            total_chars = set(target_clean) | set(candidate_clean)
            if total_chars:
                char_similarity = len(common_chars) / len(total_chars)
                scores.append(char_similarity)
            
            # 2. Substring similarity
            substring_score = 0.0
            if target_clean in candidate_clean or candidate_clean in target_clean:
                substring_score = 0.8
            elif len(target_clean) >= 3 and len(candidate_clean) >= 3:
                # Check for partial matches
                min_len = min(len(target_clean), len(candidate_clean))
                if min_len >= 3:
                    # Check start/end similarity
                    if target_clean[:3] == candidate_clean[:3]:
                        substring_score += 0.3
                    if len(target_clean) >= 4 and len(candidate_clean) >= 4:
                        if target_clean[-3:] == candidate_clean[-3:]:
                            substring_score += 0.3
            scores.append(substring_score)
            
            # 3. Length similarity (penalize very different lengths)
            len_diff = abs(len(target_clean) - len(candidate_clean))
            max_len = max(len(target_clean), len(candidate_clean))
            if max_len > 0:
                len_similarity = 1.0 - (len_diff / max_len)
                scores.append(len_similarity * 0.3)  # Lower weight
            
            # 4. Special case: abbreviated names
            if len(target_clean) <= 3 or len(candidate_clean) <= 3:
                # Check if shorter is prefix of longer
                shorter = target_clean if len(target_clean) <= len(candidate_clean) else candidate_clean
                longer = candidate_clean if len(target_clean) <= len(candidate_clean) else target_clean
                
                if longer.startswith(shorter):
                    scores.append(0.7)
            
            # Calculate final similarity score
            if scores:
                similarity = max(scores)  # Take the best score
                
                # Additional boost for exact word matches
                target_words = target_lower.split()
                candidate_words = candidate_lower.split()
                
                word_matches = 0
                for t_word in target_words:
                    for c_word in candidate_words:
                        if t_word == c_word or t_word in c_word or c_word in t_word:
                            word_matches += 1
                            break
                
                if word_matches > 0:
                    word_bonus = (word_matches / max(len(target_words), len(candidate_words))) * 0.3
                    similarity += word_bonus
                
                if similarity > best_score and similarity >= threshold:
                    best_score = similarity
                    best_match = candidate
        
        return best_match
    
    def _process_enhanced_row(self, row: Dict[str, str], row_num: int,
                             auto_correct: bool, strict_validation: bool) -> Tuple[ReceiptData, ValidationResult]:
        """Process a single row with enhanced validation and correction."""
        validation = ValidationResult(is_valid=True, row_number=row_num)
        corrections = {}
        
        # Get mapped values
        def get_mapped_value(standard_col: str) -> str:
            csv_col = self.csv_handler.column_mapping.get(standard_col)
            if csv_col and csv_col in row:
                return row[csv_col].strip()
            return ''
        
        try:
            # Process contract ID with validation
            contract_id = get_mapped_value('contractId')
            if not contract_id:
                validation.is_valid = False
                validation.errors.append("Contract ID cannot be empty")
            elif not self._validate_contract_id(contract_id):
                if auto_correct:
                    corrected_id = self._correct_contract_id(contract_id)
                    if corrected_id != contract_id:
                        corrections['contractId'] = corrected_id
                        contract_id = corrected_id
                        validation.warnings.append(f"Contract ID auto-corrected: '{row[self.csv_handler.column_mapping['contractId']]}' -> '{corrected_id}'")
                else:
                    validation.errors.append(f"Invalid contract ID format: '{contract_id}'")
                    validation.is_valid = False
            
            # Process dates with enhanced validation and correction
            from_date_str = get_mapped_value('fromDate')
            to_date_str = get_mapped_value('toDate')
            
            from_date, from_corrected = self._process_date_field(from_date_str, 'fromDate', auto_correct)
            to_date, to_corrected = self._process_date_field(to_date_str, 'toDate', auto_correct)
            
            if from_corrected:
                corrections['fromDate'] = from_date
                validation.warnings.append(f"From date auto-corrected: '{from_date_str}' -> '{from_date}'")
            
            if to_corrected:
                corrections['toDate'] = to_date
                validation.warnings.append(f"To date auto-corrected: '{to_date_str}' -> '{to_date}'")
            
            if not from_date:
                validation.is_valid = False
                validation.errors.append("From date is required and must be valid")
            
            if not to_date:
                validation.is_valid = False
                validation.errors.append("To date is required and must be valid")
            
            # Date logic validation
            if from_date and to_date:
                from_dt = datetime.strptime(from_date, '%Y-%m-%d')
                to_dt = datetime.strptime(to_date, '%Y-%m-%d')
                
                if from_dt > to_dt:
                    validation.is_valid = False
                    validation.errors.append(f"From date ({from_date}) cannot be later than to date ({to_date})")
                elif strict_validation:
                    # Additional strict validations
                    if (to_dt - from_dt).days > 366:  # More than a year
                        validation.warnings.append(f"Date range is very long ({(to_dt - from_dt).days} days)")
            
            # Process value with enhanced handling
            value_str = get_mapped_value('value')
            value, value_defaulted = self._process_value_field(value_str, auto_correct)
            
            if value < 0:
                validation.is_valid = False
                validation.errors.append(f"Value cannot be negative: {value}")
            
            # Process receipt type with intelligent mapping
            receipt_type_str = get_mapped_value('receiptType')
            receipt_type, receipt_type_defaulted = self._process_receipt_type(receipt_type_str, auto_correct)
            
            if receipt_type_defaulted and auto_correct:
                validation.warnings.append(f"Receipt type defaulted to: '{receipt_type}'")
            
            # Process payment date with intelligent defaulting
            payment_date_str = get_mapped_value('paymentDate')
            payment_date, payment_date_defaulted = self._process_payment_date(
                payment_date_str, to_date, auto_correct)
            
            if payment_date_defaulted and auto_correct:
                validation.warnings.append(f"Payment date defaulted to: '{payment_date}'")
            
            # Payment date validation
            if payment_date:
                try:
                    payment_dt = datetime.strptime(payment_date, '%Y-%m-%d')
                    current_dt = datetime.now()
                    
                    if payment_dt.date() > current_dt.date():
                        if strict_validation:
                            validation.is_valid = False
                            validation.errors.append(f"Payment date ({payment_date}) cannot be in the future")
                        else:
                            validation.warnings.append(f"Payment date ({payment_date}) is in the future")
                except ValueError:
                    validation.is_valid = False
                    validation.errors.append(f"Invalid payment date format: '{payment_date}'")
            
            # Create receipt data
            receipt = ReceiptData(
                contract_id=contract_id,
                from_date=from_date,
                to_date=to_date,
                receipt_type=receipt_type,
                value=value,
                payment_date=payment_date,
                payment_date_defaulted=payment_date_defaulted,
                value_defaulted=value_defaulted,
                receipt_type_defaulted=receipt_type_defaulted,
                row_number=row_num
            )
            
            # Store corrections
            if corrections:
                setattr(validation, 'corrections', corrections)
            
            return receipt, validation
            
        except Exception as e:
            validation.is_valid = False
            validation.errors.append(f"Row processing error: {str(e)}")
            
            # Return minimal receipt data for error cases
            receipt = ReceiptData(
                contract_id="",
                from_date="",
                to_date="",
                receipt_type="rent",
                value=0.0,
                payment_date="",
                row_number=row_num
            )
            
            return receipt, validation
    
    def _validate_contract_id(self, contract_id: str) -> bool:
        """Validate contract ID format."""
        if not contract_id:
            return False
        
        # Remove whitespace
        clean_id = contract_id.strip()
        
        # Check if it's numeric (most common)
        if clean_id.isdigit():
            return len(clean_id) >= 3  # At least 3 digits
        
        # Check for alphanumeric patterns
        if re.match(r'^[A-Za-z0-9]+$', clean_id):
            return len(clean_id) >= 3
        
        return False
    
    def _correct_contract_id(self, contract_id: str) -> str:
        """Auto-correct common contract ID issues."""
        if not contract_id:
            return contract_id
        
        # Remove whitespace and special characters
        cleaned = re.sub(r'[^\w]', '', contract_id.strip())
        
        # Convert to uppercase if contains letters
        if re.search(r'[a-zA-Z]', cleaned):
            cleaned = cleaned.upper()
        
        return cleaned
    
    def _process_date_field(self, date_str: str, field_name: str, auto_correct: bool) -> Tuple[str, bool]:
        """Process date field with multiple format support and correction."""
        if not date_str:
            return "", False
        
        date_str = date_str.strip()
        
        # Try each supported date format
        for date_format in self.DATE_FORMATS:
            try:
                parsed_date = datetime.strptime(date_str, date_format)
                iso_format = parsed_date.strftime('%Y-%m-%d')
                
                # Return corrected format if different from input
                corrected = (iso_format != date_str)
                return iso_format, corrected
                
            except ValueError:
                continue
        
        # If auto-correction is enabled, try to fix common issues
        if auto_correct:
            corrected_date = self._attempt_date_correction(date_str)
            if corrected_date:
                return corrected_date, True
        
        return "", False
    
    def _attempt_date_correction(self, date_str: str) -> Optional[str]:
        """Attempt to correct common date format issues."""
        # Remove extra whitespace and common separators
        cleaned = re.sub(r'\s+', '', date_str)
        
        # Try to extract date components using regex
        patterns = [
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',      # DD/MM/YYYY or DD-MM-YYYY
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',      # YYYY/MM/DD or YYYY-MM-DD
            r'(\d{1,2})\.(\d{1,2})\.(\d{4})',          # DD.MM.YYYY
            r'(\d{4})\.(\d{1,2})\.(\d{1,2})',          # YYYY.MM.DD
        ]
        
        for pattern in patterns:
            match = re.match(pattern, cleaned)
            if match:
                parts = match.groups()
                
                # Determine if it's DD/MM/YYYY or YYYY/MM/DD based on first number
                if len(parts[0]) == 4:  # Year first
                    year, month, day = parts
                else:  # Day first (assume Portuguese format)
                    day, month, year = parts
                
                try:
                    # Validate and format
                    date_obj = datetime(int(year), int(month), int(day))
                    return date_obj.strftime('%Y-%m-%d')
                except ValueError:
                    continue
        
        return None
    
    def _process_value_field(self, value_str: str, auto_correct: bool) -> Tuple[float, bool]:
        """Process value field with correction and validation."""
        if not value_str or value_str.strip() == "":
            return 0.0, True  # Will be filled from contract data
        
        value_str = value_str.strip()
        
        # Remove common currency symbols and formatting
        cleaned_value = value_str
        cleaned_value = re.sub(r'[€$£¥]', '', cleaned_value)  # Currency symbols
        
        # Handle decimal separators intelligently
        if '.' in cleaned_value and ',' in cleaned_value:
            # Both present - determine which is decimal separator based on position
            last_dot = cleaned_value.rfind('.')
            last_comma = cleaned_value.rfind(',')
            
            if last_comma > last_dot:
                # Comma comes after dot, comma is likely decimal separator
                # Example: 1.000,50 (European format)
                cleaned_value = cleaned_value.replace('.', '')  # Remove thousands separator
                cleaned_value = cleaned_value.replace(',', '.')  # Make comma decimal
            else:
                # Dot comes after comma, dot is likely decimal separator
                # Example: 1,000.50 (US format)
                cleaned_value = cleaned_value.replace(',', '')  # Remove thousands separator
                
        elif ',' in cleaned_value and '.' not in cleaned_value:
            # Only comma present - could be thousands separator or decimal
            comma_parts = cleaned_value.split(',')
            
            if len(comma_parts) == 2 and len(comma_parts[1]) <= 2 and comma_parts[1].isdigit():
                # Likely decimal separator (e.g., "100,50")
                cleaned_value = cleaned_value.replace(',', '.')
            elif len(comma_parts) > 2 or (len(comma_parts) == 2 and len(comma_parts[1]) > 2):
                # Likely thousands separator (e.g., "1,000" or "1,000,000")
                cleaned_value = cleaned_value.replace(',', '')
            else:
                # Ambiguous, assume decimal separator for small numbers
                if len(comma_parts) == 2 and len(comma_parts[1]) <= 2:
                    cleaned_value = cleaned_value.replace(',', '.')
                else:
                    cleaned_value = cleaned_value.replace(',', '')
        
        # Remove any remaining spaces
        cleaned_value = re.sub(r'\s+', '', cleaned_value)
        
        try:
            value = float(cleaned_value)
            return value, False
        except ValueError:
            # Try using Decimal for more robust parsing
            try:
                from decimal import Decimal, InvalidOperation
                value = float(Decimal(cleaned_value))
                return value, False
            except (ValueError, InvalidOperation):
                return 0.0, True  # Default to 0, will be filled later
    
    def _process_receipt_type(self, receipt_type_str: str, auto_correct: bool) -> Tuple[str, bool]:
        """Process receipt type with intelligent mapping."""
        if not receipt_type_str:
            return "rent", True  # Default to rent
        
        receipt_type_str = receipt_type_str.strip().lower()
        
        # Try to map to standard receipt types
        for standard_type, aliases in self.RECEIPT_TYPE_MAPPINGS.items():
            if receipt_type_str in aliases:
                return standard_type, False
        
        # If auto-correct is enabled, try partial matching
        if auto_correct:
            for standard_type, aliases in self.RECEIPT_TYPE_MAPPINGS.items():
                for alias in aliases:
                    if receipt_type_str in alias or alias in receipt_type_str:
                        return standard_type, True
        
        # Return original if no mapping found
        return receipt_type_str, False
    
    def _process_payment_date(self, payment_date_str: str, to_date: str, auto_correct: bool) -> Tuple[str, bool]:
        """Process payment date with intelligent defaulting."""
        if not payment_date_str:
            if auto_correct and to_date:
                return to_date, True  # Default to end date
            return "", True
        
        # Use the same date processing logic
        payment_date, corrected = self._process_date_field(payment_date_str, 'paymentDate', auto_correct)
        
        # If no valid date found and auto_correct is on, use to_date
        if not payment_date and auto_correct and to_date:
            return to_date, True
        
        return payment_date, corrected
    
    def _generate_data_insights(self) -> DataInsights:
        """Generate comprehensive insights about the processed data."""
        if not self.validation_results:
            return DataInsights(0, 0, 0, 0, 0, ("", ""), (0.0, 0.0), {}, {}, {})
        
        valid_receipts = [r for r in self.csv_handler.receipts if r]
        total_rows = len(self.validation_results)
        valid_rows = len([r for r in self.validation_results if r.is_valid])
        error_rows = len([r for r in self.validation_results if not r.is_valid])
        warning_rows = len([r for r in self.validation_results if r.warnings])
        
        # Contract analysis
        unique_contracts = len(set(r.contract_id for r in valid_receipts))
        
        # Date range analysis
        if valid_receipts:
            all_dates = []
            for receipt in valid_receipts:
                if receipt.from_date:
                    all_dates.append(receipt.from_date)
                if receipt.to_date:
                    all_dates.append(receipt.to_date)
            
            if all_dates:
                date_range = (min(all_dates), max(all_dates))
            else:
                date_range = ("", "")
        else:
            date_range = ("", "")
        
        # Value range analysis
        values = [r.value for r in valid_receipts if r.value > 0]
        if values:
            value_range = (min(values), max(values))
        else:
            value_range = (0.0, 0.0)
        
        # Receipt type distribution
        receipt_types = {}
        for receipt in valid_receipts:
            receipt_type = receipt.receipt_type or 'unknown'
            receipt_types[receipt_type] = receipt_types.get(receipt_type, 0) + 1
        
        # Defaulted values analysis
        defaulted_values = {
            'payment_date': len([r for r in valid_receipts if r.payment_date_defaulted]),
            'value': len([r for r in valid_receipts if r.value_defaulted]),
            'receipt_type': len([r for r in valid_receipts if r.receipt_type_defaulted])
        }
        
        # Column completeness analysis
        column_completeness = {}
        if self.csv_handler.column_mapping:
            for standard_col in self.csv_handler.column_mapping:
                non_empty = 0
                for receipt in valid_receipts:
                    value = getattr(receipt, self._standard_col_to_attr(standard_col), '')
                    if value and str(value).strip():
                        non_empty += 1
                
                if valid_rows > 0:
                    column_completeness[standard_col] = non_empty / valid_rows
                else:
                    column_completeness[standard_col] = 0.0
        
        return DataInsights(
            total_rows=total_rows,
            valid_rows=valid_rows,
            error_rows=error_rows,
            warning_rows=warning_rows,
            unique_contracts=unique_contracts,
            date_range=date_range,
            value_range=value_range,
            receipt_types=receipt_types,
            defaulted_values=defaulted_values,
            column_completeness=column_completeness
        )
    
    def _standard_col_to_attr(self, standard_col: str) -> str:
        """Map standard column name to ReceiptData attribute name."""
        mapping = {
            'contractId': 'contract_id',
            'fromDate': 'from_date', 
            'toDate': 'to_date',
            'receiptType': 'receipt_type',
            'paymentDate': 'payment_date',
            'value': 'value'
        }
        return mapping.get(standard_col, standard_col.lower())
    
    def _insights_to_dict(self) -> Dict[str, Any]:
        """Convert insights to dictionary for easy consumption."""
        if not self.data_insights:
            return {}
        
        insights = self.data_insights
        return {
            'summary': {
                'total_rows': insights.total_rows,
                'valid_rows': insights.valid_rows,
                'error_rows': insights.error_rows,
                'warning_rows': insights.warning_rows,
                'success_rate': insights.valid_rows / max(insights.total_rows, 1) * 100
            },
            'data_analysis': {
                'unique_contracts': insights.unique_contracts,
                'date_range': {
                    'start': insights.date_range[0],
                    'end': insights.date_range[1]
                },
                'value_range': {
                    'min': insights.value_range[0],
                    'max': insights.value_range[1]
                },
                'receipt_types': insights.receipt_types
            },
            'data_quality': {
                'defaulted_values': insights.defaulted_values,
                'column_completeness': insights.column_completeness
            },
            'auto_corrections': len(self.auto_corrections)
        }
    
    def get_validation_report(self) -> Dict[str, Any]:
        """Get comprehensive validation report."""
        report = {
            'summary': {
                'total_rows': len(self.validation_results),
                'valid_rows': len([r for r in self.validation_results if r.is_valid]),
                'error_rows': len([r for r in self.validation_results if not r.is_valid]),
                'warning_rows': len([r for r in self.validation_results if r.warnings])
            },
            'errors': [],
            'warnings': [],
            'suggestions': [],
            'auto_corrections': self.auto_corrections
        }
        
        for result in self.validation_results:
            if result.errors:
                for error in result.errors:
                    report['errors'].append({
                        'row': result.row_number,
                        'field': result.field_name,
                        'message': error
                    })
            
            if result.warnings:
                for warning in result.warnings:
                    report['warnings'].append({
                        'row': result.row_number,
                        'field': result.field_name,
                        'message': warning
                    })
            
            if result.suggestions:
                for suggestion in result.suggestions:
                    report['suggestions'].append({
                        'row': result.row_number,
                        'field': result.field_name,
                        'message': suggestion
                    })
        
        return report
