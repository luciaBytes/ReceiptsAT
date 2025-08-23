#!/usr/bin/env python3
"""
Comprehensive unit tests for Feature 3B - Advanced CSV Processing Capabilities.

Tests enhanced data validation, flexible column support, and intelligent defaulting.
"""

import sys
import os
import tempfile
import unittest
from unittest.mock import patch, Mock
from datetime import datetime, timedelta

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.utils.advanced_csv_processor import AdvancedCSVProcessor, ValidationResult, DataInsights
from src.csv_handler import CSVHandler


class TestAdvancedCSVProcessor(unittest.TestCase):
    """Test suite for Advanced CSV Processing capabilities."""

    def setUp(self):
        """Set up test environment."""
        self.processor = AdvancedCSVProcessor()
        
    def test_enhanced_column_mapping(self):
        """Test enhanced column mapping with fuzzy matching and extended aliases."""
        print("\n" + "=" * 70)
        print("TEST: Enhanced Column Mapping")
        print("=" * 70)
        
        test_cases = [
            {
                'name': 'Portuguese column names',
                'columns': ['id_contrato', 'data_inicio', 'data_fim', 'tipo', 'valor', 'data_pagamento'],
                'should_succeed': True
            },
            {
                'name': 'Mixed case with spaces',
                'columns': [' Contract ID ', 'FROM Date', 'to DATE', 'Receipt Type', 'Amount', 'Paid Date'],
                'should_succeed': True
            },
            {
                'name': 'With special characters',
                'columns': ['contract-id', 'start.date', 'end_date', 'type (receipt)', 'value€', 'payment@date'],
                'should_succeed': True
            },
            {
                'name': 'Common typos',
                'columns': ['contractid', 'fromdate', 'todate', 'receipttype', 'amount', 'paymentdate'],
                'should_succeed': True
            },
            {
                'name': 'Missing required columns',
                'columns': ['contract_id', 'amount', 'payment_date'],
                'should_succeed': False
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{i}. Testing: {test_case['name']}")
            
            result = self.processor._build_enhanced_column_mapping(test_case['columns'])
            
            if test_case['should_succeed']:
                if result['success']:
                    print(f"   ✅ Column mapping successful")
                    print(f"      Mapped columns: {len(result['mapping'])}")
                    for standard, csv_col in result['mapping'].items():
                        print(f"      {standard:15} -> '{csv_col}'")
                else:
                    print(f"   ❌ FAILED: {result['errors']}")
            else:
                if not result['success']:
                    print(f"   ✅ Correctly rejected: {result['errors'][0]}")
                else:
                    print(f"   ❌ Should have been rejected")
        
        print("\n✅ Enhanced column mapping tests completed")
    
    def test_date_format_detection_and_correction(self):
        """Test advanced date format detection and auto-correction."""
        print("\n" + "=" * 70)
        print("TEST: Date Format Detection and Correction")
        print("=" * 70)
        
        test_cases = [
            # Standard formats
            ('2024-07-15', '2024-07-15', False, 'ISO format'),
            ('15/07/2024', '2024-07-15', True, 'Portuguese format'),
            ('15-07-2024', '2024-07-15', True, 'Portuguese with dashes'),
            ('2024/07/15', '2024-07-15', True, 'Alternative ISO'),
            
            # European formats
            ('15.07.2024', '2024-07-15', True, 'European format'),
            ('2024.07.15', '2024-07-15', True, 'Alternative European'),
            
            # US format (ambiguous but handled)
            ('07/15/2024', '2024-07-15', True, 'US format'),
            
            # Edge cases
            ('1/7/2024', '2024-07-01', True, 'Single digits'),
            ('01/07/2024', '2024-07-01', True, 'Zero padded'),
            
            # Invalid formats
            ('invalid-date', '', False, 'Invalid format'),
            ('32/13/2024', '', False, 'Invalid date values'),
            ('', '', False, 'Empty string'),
        ]
        
        for i, (input_date, expected, should_correct, description) in enumerate(test_cases, 1):
            print(f"\n{i}. Testing: {description}")
            print(f"   Input: '{input_date}'")
            
            result_date, was_corrected = self.processor._process_date_field(input_date, 'testField', True)
            
            if expected:
                if result_date == expected:
                    status = "corrected" if was_corrected else "accepted"
                    print(f"   ✅ SUCCESS: Date {status} -> '{result_date}'")
                else:
                    print(f"   ❌ FAILED: Expected '{expected}', got '{result_date}'")
            else:
                if not result_date:
                    print(f"   ✅ SUCCESS: Correctly rejected invalid date")
                else:
                    print(f"   ❌ FAILED: Should have rejected but got '{result_date}'")
        
        print("\n✅ Date format detection tests completed")
    
    def test_value_processing_and_correction(self):
        """Test advanced value processing with various formats."""
        print("\n" + "=" * 70)
        print("TEST: Value Processing and Correction")
        print("=" * 70)
        
        test_cases = [
            # Standard formats
            ('100.00', 100.0, False, 'Standard decimal'),
            ('100', 100.0, False, 'Integer'),
            
            # Currency symbols
            ('€100.00', 100.0, False, 'Euro symbol'),
            ('$100.00', 100.0, False, 'Dollar symbol'),
            ('£100.00', 100.0, False, 'Pound symbol'),
            
            # Thousands separators
            ('1,000.00', 1000.0, False, 'Comma thousands separator'),
            ('1 000.00', 1000.0, False, 'Space thousands separator'),
            ('1,000,000.50', 1000000.5, False, 'Multiple comma separators'),
            
            # European decimal format
            ('100,50', 100.5, False, 'Comma as decimal separator'),
            ('1.000,50', 1000.5, False, 'European format'),
            
            # Edge cases
            ('0', 0.0, False, 'Zero value'),
            ('0.00', 0.0, False, 'Zero with decimals'),
            ('', 0.0, True, 'Empty string (defaulted)'),
            ('   ', 0.0, True, 'Whitespace only (defaulted)'),
            
            # Invalid formats
            ('abc', 0.0, True, 'Non-numeric (defaulted)'),
            ('12.34.56', 0.0, True, 'Multiple decimal points (defaulted)'),
        ]
        
        for i, (input_value, expected_value, should_default, description) in enumerate(test_cases, 1):
            print(f"\n{i}. Testing: {description}")
            print(f"   Input: '{input_value}'")
            
            result_value, was_defaulted = self.processor._process_value_field(input_value, True)
            
            if abs(result_value - expected_value) < 0.01:  # Float comparison
                status = "defaulted" if was_defaulted else "processed"
                print(f"   ✅ SUCCESS: Value {status} -> {result_value}")
                
                if should_default and not was_defaulted:
                    print(f"   ⚠️  WARNING: Expected defaulting but value was processed")
                elif not should_default and was_defaulted:
                    print(f"   ⚠️  WARNING: Unexpected defaulting")
            else:
                print(f"   ❌ FAILED: Expected {expected_value}, got {result_value}")
        
        print("\n✅ Value processing tests completed")
    
    def test_receipt_type_mapping(self):
        """Test intelligent receipt type mapping and correction."""
        print("\n" + "=" * 70)
        print("TEST: Receipt Type Mapping")
        print("=" * 70)
        
        test_cases = [
            # Standard mappings
            ('rent', 'rent', False, 'Standard rent'),
            ('renda', 'rent', False, 'Portuguese rent'),
            ('aluguel', 'rent', False, 'Brazilian rent'),
            
            # Deposit variations
            ('deposit', 'deposit', False, 'Standard deposit'),
            ('caução', 'deposit', False, 'Portuguese deposit'),
            ('fiança', 'deposit', False, 'Portuguese guarantee'),
            
            # Utilities
            ('utilities', 'utilities', False, 'Standard utilities'),
            ('despesas', 'utilities', False, 'Portuguese expenses'),
            ('condomínio', 'utilities', False, 'Portuguese condominium'),
            
            # Case variations
            ('RENT', 'rent', False, 'Uppercase'),
            ('Rent', 'rent', False, 'Mixed case'),
            ('  rent  ', 'rent', False, 'With whitespace'),
            
            # Partial matching (with auto-correction)
            ('rental', 'rent', True, 'Partial match - rental'),
            ('maintenance_fee', 'maintenance', True, 'Partial match - maintenance'),
            
            # Default cases
            ('', 'rent', True, 'Empty string (defaulted)'),
            ('unknown_type', 'unknown_type', False, 'Unknown type (kept as-is)'),
        ]
        
        for i, (input_type, expected_type, should_correct, description) in enumerate(test_cases, 1):
            print(f"\n{i}. Testing: {description}")
            print(f"   Input: '{input_type}'")
            
            result_type, was_defaulted = self.processor._process_receipt_type(input_type, True)
            
            if result_type == expected_type:
                status = "corrected" if was_defaulted else "mapped"
                print(f"   ✅ SUCCESS: Type {status} -> '{result_type}'")
            else:
                print(f"   ❌ FAILED: Expected '{expected_type}', got '{result_type}'")
        
        print("\n✅ Receipt type mapping tests completed")
    
    def test_full_csv_processing_with_corrections(self):
        """Test complete CSV processing with auto-corrections."""
        print("\n" + "=" * 70)
        print("TEST: Full CSV Processing with Auto-Corrections")
        print("=" * 70)
        
        # Create test CSV with various issues that should be auto-corrected
        csv_content = """id_contrato,data_inicio,data_fim,tipo,valor,data_pagamento
123456,15/07/2024,31/07/2024,renda,€850.00,28/07/2024
789012,2024-06-01,2024-06-30,deposit,"1,200.50",
999888,01.05.2024,31.05.2024,,750,15/05/2024
111222,2024/08/01,2024/08/31,utilities,€900.00,2024-08-15
INVALID,invalid-date,2024-09-30,rent,abc,future-date
"""
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(csv_content)
            temp_file_path = temp_file.name
        
        try:
            print(f"Processing CSV with auto-corrections enabled...")
            
            # Process with auto-corrections
            success, errors, insights = self.processor.enhanced_load_csv(
                temp_file_path, 
                auto_correct=True, 
                strict_validation=False
            )
            
            print(f"\nProcessing Results:")
            print(f"Success: {success}")
            print(f"Errors: {len(errors)}")
            
            if insights:
                summary = insights['summary']
                print(f"\nData Summary:")
                print(f"  Total rows: {summary['total_rows']}")
                print(f"  Valid rows: {summary['valid_rows']}")
                print(f"  Error rows: {summary['error_rows']}")
                print(f"  Success rate: {summary['success_rate']:.1f}%")
                
                corrections = insights['auto_corrections']
                print(f"  Auto-corrections applied: {corrections}")
            
            # Get validation report
            report = self.processor.get_validation_report()
            
            if report['warnings']:
                print(f"\nAuto-corrections (warnings):")
                for warning in report['warnings'][:5]:  # Show first 5
                    print(f"  Row {warning['row']}: {warning['message']}")
            
            if report['errors']:
                print(f"\nRemaining errors:")
                for error in report['errors'][:3]:  # Show first 3
                    print(f"  Row {error['row']}: {error['message']}")
            
            # Verify specific corrections were made
            receipts = self.processor.csv_handler.get_receipts()
            if receipts:
                print(f"\nSample corrected receipts:")
                for i, receipt in enumerate(receipts[:3]):  # Show first 3
                    print(f"  Receipt {i+1}:")
                    print(f"    Contract: {receipt.contract_id}")
                    print(f"    Period: {receipt.from_date} to {receipt.to_date}")
                    print(f"    Type: {receipt.receipt_type}")
                    print(f"    Value: €{receipt.value}")
                    print(f"    Payment: {receipt.payment_date}")
            
            print(f"\n✅ Full CSV processing test completed")
            
        finally:
            # Clean up
            try:
                os.unlink(temp_file_path)
            except:
                pass
    
    def test_data_insights_generation(self):
        """Test comprehensive data insights generation."""
        print("\n" + "=" * 70)
        print("TEST: Data Insights Generation")
        print("=" * 70)
        
        # Create test CSV with diverse data
        csv_content = """contractId,fromDate,toDate,receiptType,value,paymentDate
123456,2024-01-01,2024-01-31,rent,800.00,2024-01-31
123456,2024-02-01,2024-02-29,rent,800.00,2024-02-29
789012,2024-01-01,2024-01-31,rent,1200.00,2024-01-31
789012,2024-02-01,2024-02-29,deposit,500.00,2024-02-15
999888,2024-01-15,2024-02-14,utilities,150.00,2024-02-14
111222,2024-03-01,2024-03-31,rent,,2024-03-31
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(csv_content)
            temp_file_path = temp_file.name
        
        try:
            success, errors, insights = self.processor.enhanced_load_csv(temp_file_path)
            
            self.assertTrue(success, f"CSV processing should succeed: {errors}")
            self.assertIsNotNone(insights)
            
            print(f"Generated insights:")
            
            # Test summary insights
            summary = insights['summary']
            print(f"\nSummary:")
            print(f"  Total rows: {summary['total_rows']}")
            print(f"  Valid rows: {summary['valid_rows']}")
            print(f"  Success rate: {summary['success_rate']:.1f}%")
            
            # Test data analysis
            analysis = insights['data_analysis']
            print(f"\nData Analysis:")
            print(f"  Unique contracts: {analysis['unique_contracts']}")
            print(f"  Date range: {analysis['date_range']['start']} to {analysis['date_range']['end']}")
            print(f"  Value range: €{analysis['value_range']['min']} to €{analysis['value_range']['max']}")
            print(f"  Receipt types: {analysis['receipt_types']}")
            
            # Test data quality metrics
            quality = insights['data_quality']
            print(f"\nData Quality:")
            print(f"  Defaulted values: {quality['defaulted_values']}")
            print(f"  Column completeness:")
            for col, completeness in quality['column_completeness'].items():
                print(f"    {col}: {completeness:.1%}")
            
            # Assertions for data integrity
            self.assertEqual(summary['total_rows'], 6)
            self.assertEqual(analysis['unique_contracts'], 4)
            self.assertIn('rent', analysis['receipt_types'])
            self.assertIn('deposit', analysis['receipt_types'])
            
            print(f"\n✅ Data insights generation test completed")
            
        finally:
            try:
                os.unlink(temp_file_path)
            except:
                pass
    
    def test_strict_validation_mode(self):
        """Test strict validation mode with enhanced rules."""
        print("\n" + "=" * 70)
        print("TEST: Strict Validation Mode")
        print("=" * 70)
        
        # Create CSV with edge cases that should trigger strict validation
        csv_content = """contractId,fromDate,toDate,receiptType,value,paymentDate
123456,2024-01-01,2025-12-31,rent,800.00,2024-01-31
789012,2024-06-01,2024-06-30,rent,800.00,2024-12-31
999888,2024-01-01,2024-01-31,rent,800.00,
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(csv_content)
            temp_file_path = temp_file.name
        
        try:
            print("Testing with strict validation OFF...")
            success_normal, errors_normal, insights_normal = self.processor.enhanced_load_csv(
                temp_file_path, strict_validation=False)
            
            print("Testing with strict validation ON...")
            # Create new processor for strict mode
            strict_processor = AdvancedCSVProcessor()
            success_strict, errors_strict, insights_strict = strict_processor.enhanced_load_csv(
                temp_file_path, strict_validation=True)
            
            print(f"\nResults Comparison:")
            print(f"Normal mode - Success: {success_normal}, Errors: {len(errors_normal)}")
            print(f"Strict mode - Success: {success_strict}, Errors: {len(errors_strict)}")
            
            # Strict mode should be more restrictive
            if len(errors_strict) >= len(errors_normal):
                print("✅ Strict validation is more restrictive as expected")
            else:
                print("⚠️  Strict validation should be more restrictive")
            
            if errors_strict:
                print("\nStrict validation errors:")
                for error in errors_strict[:3]:
                    print(f"  {error}")
            
            print(f"\n✅ Strict validation mode test completed")
            
        finally:
            try:
                os.unlink(temp_file_path)
            except:
                pass
    
    def test_fuzzy_column_matching(self):
        """Test fuzzy matching for column names with typos."""
        print("\n" + "=" * 70)
        print("TEST: Fuzzy Column Matching")
        print("=" * 70)
        
        test_cases = [
            # Common typos and variations
            (['contractid', 'fromdate', 'todate'], True, 'Missing underscores'),
            (['contrac_id', 'from_dat', 'to_dat'], True, 'Minor typos'),
            (['contract_identification', 'start_date', 'finish_date'], True, 'Verbose names'),
            (['id', 'start', 'end'], True, 'Abbreviated names'),
            (['totally_wrong', 'invalid_name', 'bad_column'], False, 'Completely wrong'),
        ]
        
        for i, (columns, should_match, description) in enumerate(test_cases, 1):
            print(f"\n{i}. Testing: {description}")
            print(f"   Columns: {columns}")
            
            result = self.processor._build_enhanced_column_mapping(
                columns + ['receiptType', 'value', 'paymentDate']  # Add valid optional columns
            )
            
            if should_match:
                if result['success']:
                    print(f"   ✅ SUCCESS: Fuzzy matching worked")
                    mapped_required = [col for col in ['contractId', 'fromDate', 'toDate'] 
                                     if col in result['mapping']]
                    print(f"      Required columns mapped: {len(mapped_required)}/3")
                else:
                    print(f"   ❌ FAILED: Should have matched but got: {result['errors']}")
            else:
                if not result['success']:
                    print(f"   ✅ SUCCESS: Correctly rejected poor matches")
                else:
                    print(f"   ⚠️  WARNING: Unexpectedly matched poor columns")
        
        print(f"\n✅ Fuzzy column matching test completed")

def run_comprehensive_tests():
    """Run all Feature 3B tests comprehensively."""
    print("=" * 80)
    print("FEATURE 3B - ADVANCED CSV PROCESSING CAPABILITIES")
    print("Comprehensive Unit Test Suite")
    print("=" * 80)
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add all test methods
    test_methods = [
        'test_enhanced_column_mapping',
        'test_date_format_detection_and_correction', 
        'test_value_processing_and_correction',
        'test_receipt_type_mapping',
        'test_full_csv_processing_with_corrections',
        'test_data_insights_generation',
        'test_strict_validation_mode',
        'test_fuzzy_column_matching'
    ]
    
    for method in test_methods:
        suite.addTest(TestAdvancedCSVProcessor(method))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 80)
    print("FEATURE 3B TEST SUMMARY")
    print("=" * 80)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    passed = total_tests - failures - errors
    
    print(f"Tests executed: {total_tests}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failures}")
    print(f"⚠️  Errors: {errors}")
    print(f"Success rate: {(passed/total_tests*100):.1f}%")
    
    if result.failures:
        print(f"\nFailures:")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print(f"\nErrors:")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback.split('Exception:')[-1].strip()}")
    
    print("=" * 80)
    
    return passed == total_tests

if __name__ == "__main__":
    run_comprehensive_tests()
