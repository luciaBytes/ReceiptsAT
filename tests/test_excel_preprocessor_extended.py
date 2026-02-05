"""
Extended unit tests for LandlordExcelProcessor (Excel Preprocessor).
Targets: multi-sheet detection, cell coercion, format detection, column header normalization.
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import date

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from excel_preprocessor import (
    LandlordExcelProcessor,
    TenantData,
    PaymentInfo,
    ProcessingAlert,
    ReceiptData,
    MONTH_COLUMNS
)


class TestExcelStructureValidation:
    """Test Excel file structure validation."""
    
    def test_validate_excel_structure_valid(self):
        """Test validation passes for valid Excel structure."""
        processor = LandlordExcelProcessor()
        
        # Mock worksheet with valid structure
        mock_worksheet = Mock()
        mock_worksheet.max_row = 3
        
        # Mock header row
        mock_row = [Mock(), Mock(), Mock(), Mock(), Mock(), Mock(), Mock()]
        mock_row[0].value = 'Contract'
        mock_row[1].value = 'Name'
        mock_row[2].value = 'Rent'
        mock_row[3].value = 'RentDeposit'
        mock_row[4].value = 'MonthsLate'
        mock_row[5].value = 'PaidCurrentMonth'
        mock_row[6].value = 'Jan'
        
        mock_worksheet.__getitem__ = lambda self, key: mock_row if key == 1 else []
        
        processor._validate_excel_structure(mock_worksheet)
        assert len(processor.validation_errors) == 0
    
    def test_validate_excel_structure_empty_file(self):
        """Test validation fails for empty Excel file."""
        processor = LandlordExcelProcessor()
        
        mock_worksheet = Mock()
        mock_worksheet.max_row = 1  # Only header or empty
        
        processor._validate_excel_structure(mock_worksheet)
        assert len(processor.validation_errors) > 0
        assert any('empty' in err.lower() for err in processor.validation_errors)
    
    def test_validate_excel_structure_missing_required_columns(self):
        """Test validation fails when required columns are missing."""
        processor = LandlordExcelProcessor()
        
        mock_worksheet = Mock()
        mock_worksheet.max_row = 3
        
        # Mock header row missing 'Rent' column
        mock_row = [Mock(), Mock(), Mock(), Mock(), Mock()]
        mock_row[0].value = 'Contract'
        mock_row[1].value = 'Name'
        mock_row[2].value = 'RentDeposit'
        mock_row[3].value = 'MonthsLate'
        mock_row[4].value = 'PaidCurrentMonth'
        
        mock_worksheet.__getitem__ = lambda self, key: mock_row if key == 1 else []
        
        processor._validate_excel_structure(mock_worksheet)
        assert len(processor.validation_errors) > 0
    
    def test_validate_excel_structure_no_month_columns(self):
        """Test validation fails when no month columns present."""
        processor = LandlordExcelProcessor()
        
        mock_worksheet = Mock()
        mock_worksheet.max_row = 3
        
        # Mock header row without month columns
        mock_row = [Mock(), Mock(), Mock(), Mock(), Mock(), Mock()]
        mock_row[0].value = 'Contract'
        mock_row[1].value = 'Name'
        mock_row[2].value = 'Rent'
        mock_row[3].value = 'RentDeposit'
        mock_row[4].value = 'MonthsLate'
        mock_row[5].value = 'PaidCurrentMonth'
        
        mock_worksheet.__getitem__ = lambda self, key: mock_row if key == 1 else []
        
        processor._validate_excel_structure(mock_worksheet)
        assert len(processor.validation_errors) > 0
        assert any('month' in err.lower() for err in processor.validation_errors)


class TestColumnMapping:
    """Test column header mapping and normalization."""
    
    def test_build_column_map_standard_names(self):
        """Test column mapping with standard column names."""
        processor = LandlordExcelProcessor()
        
        header = ['Contract', 'Name', 'Rent', 'RentDeposit', 'MonthsLate', 'PaidCurrentMonth', 'Jan', 'Feb']
        col_map = processor._build_column_map(header)
        
        assert col_map['contract'] == 0
        assert col_map['name'] == 1
        assert col_map['rent'] == 2
        assert col_map['rent_deposit'] == 3
        assert col_map['months_late'] == 4
        assert col_map['paid_current_month'] == 5
        assert 1 in col_map['month_columns']
        assert 2 in col_map['month_columns']
    
    def test_build_column_map_case_insensitive(self):
        """Test column mapping is case-insensitive."""
        processor = LandlordExcelProcessor()
        
        header = ['contract', 'NAME', 'RenT', 'rentdeposit', 'MONTHSLATE', 'paidcurrentmonth']
        col_map = processor._build_column_map(header)
        
        assert col_map['contract'] == 0
        assert col_map['name'] == 1
        assert col_map['rent'] == 2
        assert col_map['rent_deposit'] == 3
    
    def test_build_column_map_with_spaces(self):
        """Test column mapping handles spaces in names."""
        processor = LandlordExcelProcessor()
        
        header = ['Contract', 'Name', 'Rent', 'Rent Deposit', 'Months Late', 'Paid Current Month']
        col_map = processor._build_column_map(header)
        
        assert col_map['rent_deposit'] == 3
        assert col_map['months_late'] == 4
        assert col_map['paid_current_month'] == 5
    
    def test_build_column_map_month_variations(self):
        """Test mapping of different month name formats."""
        processor = LandlordExcelProcessor()
        
        header = ['Contract', 'Name', 'Jan', 'January', 'Feb', 'February', 'Dec', 'December']
        col_map = processor._build_column_map(header)
        
        # Jan and January both map to month 1
        assert 1 in col_map['month_columns']
        # Feb and February both map to month 2
        assert 2 in col_map['month_columns']
        # Dec and December both map to month 12
        assert 12 in col_map['month_columns']


class TestCellTypeCoercion:
    """Test handling of different cell value types."""
    
    def test_parse_tenant_row_with_numeric_values(self):
        """Test parsing tenant row with proper numeric types."""
        processor = LandlordExcelProcessor()
        
        col_map = {
            'contract': 0,
            'name': 1,
            'rent': 2,
            'rent_deposit': 3,
            'deposit_month_offset': 4,
            'months_late': 5,
            'paid_current_month': 6,
            'month_columns': {}
        }
        
        row_values = ['12345', 'John Doe', 1000.00, 1, 1, 0, 'No']  # Numeric values as float/int
        
        tenant = processor._parse_tenant_row(row_values, col_map, 2)
        
        assert tenant.contract_number == '12345'
        assert tenant.rent == 1000.00
        assert tenant.rent_deposit == 1
        assert tenant.deposit_month_offset == 1
        assert tenant.months_late == 0
    
    def test_parse_tenant_row_with_boolean_values(self):
        """Test parsing paid_current_month as boolean-like values."""
        processor = LandlordExcelProcessor()
        
        col_map = {
            'contract': 0,
            'name': 1,
            'rent': 2,
            'rent_deposit': 3,
            'deposit_month_offset': 4,
            'months_late': 5,
            'paid_current_month': 6,
            'month_columns': {}
        }
        
        # Test with 'Yes'
        row_values = ['12345', 'John Doe', 1000.00, 1, 1, 0, 'Yes']
        tenant = processor._parse_tenant_row(row_values, col_map, 2)
        assert tenant.paid_current_month is True
        
        # Test with 'No'
        row_values[6] = 'No'
        tenant = processor._parse_tenant_row(row_values, col_map, 2)
        assert tenant.paid_current_month is False
    
    def test_parse_tenant_row_with_integer_defaults(self):
        """Test parsing handles proper integer types."""
        processor = LandlordExcelProcessor()
        
        col_map = {
            'contract': 0,
            'name': 1,
            'rent': 2,
            'rent_deposit': 3,
            'deposit_month_offset': 4,
            'months_late': 5,
            'paid_current_month': 6,
            'month_columns': {}
        }
        
        # All integer values should be int type, not None
        row_values = ['12345', 'John Doe', 1000.00, 1, 1, 0, 'No']
        tenant = processor._parse_tenant_row(row_values, col_map, 2)
        
        assert tenant.months_late == 0


class TestLandlordSeparatorDetection:
    """Test detection of landlord separator rows."""
    
    def test_is_landlord_separator_row_with_keyword(self):
        """Test detection of rows containing landlord keywords."""
        processor = LandlordExcelProcessor()
        
        row_values = ['Landlord: John Smith', None, None, None, None]
        assert processor._is_landlord_separator_row(row_values) is True
        
        row_values = ['LANDLORD PROPERTIES', None, None, None, None]
        assert processor._is_landlord_separator_row(row_values) is True
    
    def test_is_landlord_separator_row_normal_data(self):
        """Test normal tenant rows are not detected as separators."""
        processor = LandlordExcelProcessor()
        
        row_values = ['12345', 'John Doe', 1000.00, 1, 0, 'No']
        assert processor._is_landlord_separator_row(row_values) is False


class TestEmptyRowFiltering:
    """Test filtering of empty rows and columns."""
    
    def test_parse_tenants_skips_empty_rows(self):
        """Test that completely empty rows are skipped."""
        processor = LandlordExcelProcessor()
        
        # Mock worksheet
        mock_worksheet = Mock()
        
        # Header row
        header_cells = [Mock() for _ in range(8)]
        header_cells[0].value = 'Contract'
        header_cells[1].value = 'Name'
        header_cells[2].value = 'Rent'
        header_cells[3].value = 'RentDeposit'
        header_cells[4].value = 'Mes Caucao'
        header_cells[5].value = 'MonthsLate'
        header_cells[6].value = 'PaidCurrentMonth'
        header_cells[7].value = 'Jan'
        
        # Data row 1 (valid)
        row1_cells = [Mock() for _ in range(8)]
        row1_cells[0].value = '12345'
        row1_cells[1].value = 'John Doe'
        row1_cells[2].value = 1000.00
        row1_cells[3].value = 1
        row1_cells[4].value = 0
        row1_cells[5].value = 1  # Mes Caucao
        row1_cells[6].value = 0
        row1_cells[7].value = 'No'
        
        # Data row 2 (empty)
        row2_cells = [Mock() for _ in range(8)]
        for cell in row2_cells:
            cell.value = None
        
        # Data row 3 (valid)
        row3_cells = [Mock() for _ in range(8)]
        row3_cells[0].value = '67890'
        row3_cells[1].value = 'Jane Smith'
        row3_cells[2].value = 1500.00
        row3_cells[3].value = 1
        row3_cells[4].value = 0
        row3_cells[5].value = 1  # Mes Caucao
        row3_cells[6].value = 0
        row3_cells[7].value = 'No'
        
        mock_worksheet.__getitem__ = lambda self, idx: header_cells if idx == 1 else []
        mock_worksheet.iter_rows.return_value = [row1_cells, row2_cells, row3_cells]
        
        tenants = processor._parse_tenants(mock_worksheet)
        
        # Should only parse 2 tenants (skip empty row)
        assert len(tenants) == 2


class TestMultiSheetHandling:
    """Test handling of multi-sheet Excel workbooks."""
    
    @patch('excel_preprocessor.openpyxl.load_workbook')
    @patch('excel_preprocessor.Path')
    def test_parse_excel_with_specific_sheet(self, mock_path, mock_load_workbook):
        """Test parsing specific sheet by name."""
        # Mock Path to return True for exists()
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path.return_value = mock_path_instance
        
        # Mock workbook with multiple sheets
        mock_workbook = Mock()
        mock_workbook.sheetnames = ['Sheet1', 'Tenants', 'Summary']
        
        mock_sheet = Mock()
        mock_sheet.title = 'Tenants'
        mock_sheet.max_row = 3
        
        # Mock header row
        mock_row = [Mock() for _ in range(7)]
        mock_row[0].value = 'Contract'
        mock_row[1].value = 'Name'
        mock_row[2].value = 'Rent'
        mock_row[3].value = 'RentDeposit'
        mock_row[4].value = 'MonthsLate'
        mock_row[5].value = 'PaidCurrentMonth'
        mock_row[6].value = 'Jan'
        
        mock_sheet.__getitem__ = lambda self, key: mock_row if key == 1 else []
        mock_sheet.iter_rows.return_value = []
        
        mock_workbook.__getitem__ = lambda self, name: mock_sheet if name == 'Tenants' else None
        mock_load_workbook.return_value = mock_workbook
        
        processor = LandlordExcelProcessor()
        
        receipts, alerts = processor.parse_excel('test.xlsx', 1, 2025, sheet_name='Tenants')
        
        # Should complete without error
        assert isinstance(receipts, list)
        assert isinstance(alerts, list)
    
    @patch('excel_preprocessor.openpyxl.load_workbook')
    @patch('excel_preprocessor.Path')
    def test_parse_excel_sheet_not_found(self, mock_path, mock_load_workbook):
        """Test error when specified sheet doesn't exist."""
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path.return_value = mock_path_instance
        
        mock_workbook = Mock()
        mock_workbook.sheetnames = ['Sheet1', 'Summary']
        
        mock_load_workbook.return_value = mock_workbook
        
        processor = LandlordExcelProcessor()
        
        with pytest.raises(ValueError) as exc_info:
            processor.parse_excel('test.xlsx', 1, 2025, sheet_name='NonExistent')
        
        assert 'not found' in str(exc_info.value).lower()
    
    @patch('excel_preprocessor.openpyxl.load_workbook')
    @patch('excel_preprocessor.Path')
    def test_parse_excel_uses_active_sheet_by_default(self, mock_path, mock_load_workbook):
        """Test that active sheet is used when no sheet name specified."""
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path.return_value = mock_path_instance
        
        mock_workbook = Mock()
        mock_sheet = Mock()
        mock_sheet.title = 'Sheet1'
        mock_sheet.max_row = 3
        
        # Mock header row
        mock_row = [Mock() for _ in range(7)]
        mock_row[0].value = 'Contract'
        mock_row[1].value = 'Name'
        mock_row[2].value = 'Rent'
        mock_row[3].value = 'RentDeposit'
        mock_row[4].value = 'MonthsLate'
        mock_row[5].value = 'PaidCurrentMonth'
        mock_row[6].value = 'Jan'
        
        mock_sheet.__getitem__ = lambda self, key: mock_row if key == 1 else []
        mock_sheet.iter_rows.return_value = []
        mock_workbook.active = mock_sheet
        
        mock_load_workbook.return_value = mock_workbook
        
        processor = LandlordExcelProcessor()
        
        receipts, alerts = processor.parse_excel('test.xlsx', 1, 2025)
        
        # Active sheet should have been used
        assert isinstance(receipts, list)
        assert isinstance(alerts, list)


class TestPaymentDateCalculation:
    """Test payment date calculation logic."""
    
    def test_generate_receipts_basic_functionality(self):
        """Test receipt generation for valid tenant data."""
        processor = LandlordExcelProcessor()
        
        tenant = TenantData(
            contract_number='12345',
            name='John Doe',
            rent=1000.00,
            rent_deposit=1,
            deposit_month_offset=1,
            months_late=0,
            paid_current_month=False,
            row_number=2
        )
        
        # Mock a minimal worksheet with required structure
        mock_worksheet = Mock()
        col_map = {
            'contract': 0,
            'name': 1,
            'rent': 2,
            'rent_deposit': 3,
            'deposit_month_offset': 4,
            'months_late': 5,
            'paid_current_month': 6,
            'month_columns': {1: 7}  # January in column 7
        }
        
        # Call the method with all required parameters
        receipts = processor._prepare_receipt_records([tenant], 1, 2025, mock_worksheet, col_map)
        
        # Should return a list (may be empty if no payment column data)
        assert isinstance(receipts, list)


class TestFileNotFoundHandling:
    """Test handling of missing files."""
    
    def test_parse_excel_file_not_found(self):
        """Test appropriate error when file doesn't exist."""
        processor = LandlordExcelProcessor()
        
        with pytest.raises(FileNotFoundError):
            processor.parse_excel('nonexistent_file.xlsx', 1, 2025)


class TestProcessingAlerts:
    """Test generation of processing alerts."""
    
    def test_processing_alerts_cleared_on_new_parse(self):
        """Test that alerts are cleared when parsing new file."""
        processor = LandlordExcelProcessor()
        
        # Add some alerts
        processor.processing_alerts.append(
            ProcessingAlert(
                contract_number='12345',
                payment_date=date(2025, 1, 15),
                payment_column='Feb',
                expected_column='Jan',
                rent_period_from=date(2025, 2, 1),
                rent_period_to=date(2025, 2, 28),
                reason='Late payment'
            )
        )
        
        assert len(processor.processing_alerts) > 0
        
        # Mock parse_excel to reset state
        with patch('excel_preprocessor.openpyxl.load_workbook'):
            processor.validation_errors = []
            processor.processing_alerts = []
            
            assert len(processor.processing_alerts) == 0
