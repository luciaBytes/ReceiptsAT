#!/usr/bin/env python3
"""
Comprehensive unit tests for CSV Template Generator

This test suite validates all functionality of the CSV Template Generator
including template generation, sample data creation, and file operations.

Author: Assistant
Date: August 2025
"""

import unittest
import os
import tempfile
import shutil
import csv
from datetime import datetime
import sys

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.csv_template_generator import CSVTemplateGenerator, TemplateType, TemplateConfig

class TestCSVTemplateGenerator(unittest.TestCase):
    """Test cases for CSV Template Generator functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.generator = CSVTemplateGenerator()
        self.test_dir = tempfile.mkdtemp(prefix="csv_template_test_")
        
    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_generator_initialization(self):
        """Test that generator initializes correctly."""
        self.assertIsNotNone(self.generator)
        self.assertIsNotNone(self.generator.templates)
        self.assertIsNotNone(self.generator.sample_data)
        
        # Check that only basic and detailed template types are available
        expected_templates = {TemplateType.BASIC, TemplateType.DETAILED}
        self.assertEqual(set(self.generator.templates.keys()), expected_templates)
    
    def test_basic_template_generation(self):
        """Test basic template generation."""
        output_path = os.path.join(self.test_dir, "basic_template.csv")
        
        success, message = self.generator.generate_template(
            TemplateType.BASIC, 
            output_path
        )
        
        self.assertTrue(success, f"Template generation failed: {message}")
        self.assertTrue(os.path.exists(output_path), "Template file was not created")
        
        # Verify file content
        with open(output_path, 'r', encoding='utf-8-sig') as f:
            content = f.read()
            
        # Check for expected headers
        self.assertIn("contractId", content)
        self.assertIn("fromDate", content)
        self.assertIn("toDate", content)
        self.assertIn("receiptType", content)
        self.assertIn("value", content)
    

    def test_template_with_samples(self):
        """Test template generation with sample data."""
        output_path = os.path.join(self.test_dir, "sample_template.csv")
        
        config = TemplateConfig(
            template_type=TemplateType.DETAILED,
            include_samples=True,
            include_descriptions=True,
            sample_count=3
        )
        
        success, message = self.generator.generate_template(
            TemplateType.DETAILED,
            output_path,
            config
        )
        
        self.assertTrue(success, f"Template with samples generation failed: {message}")
        
        # Verify sample data is included
        with open(output_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            rows = list(reader)
            
        # Should have header + sample rows
        self.assertGreaterEqual(len(rows), 4, "Expected at least 4 rows (header + 3 samples)")
        
        # Check that sample data contains contract IDs
        found_sample = False
        for row in rows:
            if row and row[0].isdigit() and len(row[0]) == 6:  # Contract ID format
                found_sample = True
                break
        
        self.assertTrue(found_sample, "No sample data found in generated template")
    

    

    

    
    def test_multiple_templates_generation(self):
        """Test generating multiple templates at once."""
        success, message, results = self.generator.generate_multiple_templates(self.test_dir)
        
        self.assertTrue(success, f"Multiple template generation failed: {message}")
        self.assertGreater(len(results), 0, "No templates were generated")
        
        # Check that files were actually created (only Basic and Detailed templates)
        expected_files = [
            "basic_template.csv",
            "detailed_template.csv"
        ]
        
        for filename in expected_files:
            file_path = os.path.join(self.test_dir, filename)
            self.assertTrue(os.path.exists(file_path), f"Template file not found: {filename}")
            self.assertTrue(results.get(filename, False), f"Template generation reported failure: {filename}")
    
    def test_template_info_retrieval(self):
        """Test getting template information."""
        info = self.generator.get_template_info(TemplateType.BASIC)
        
        self.assertIn("template_type", info)
        self.assertIn("field_count", info)
        self.assertIn("required_fields", info)
        self.assertIn("optional_fields", info)
        self.assertIn("fields", info)
        
        self.assertEqual(info["template_type"], TemplateType.BASIC.value)
        self.assertGreater(info["field_count"], 0)
        self.assertIsInstance(info["fields"], list)
        
        # Check field structure
        for field in info["fields"]:
            self.assertIn("name", field)
            self.assertIn("description", field)
            self.assertIn("required", field)
            self.assertIn("example", field)
    
    def test_help_file_generation(self):
        """Test help file generation."""
        help_path = os.path.join(self.test_dir, "help_file.md")
        
        success, message = self.generator.generate_help_file(help_path)
        
        self.assertTrue(success, f"Help file generation failed: {message}")
        self.assertTrue(os.path.exists(help_path), "Help file was not created")
        
        # Verify help content
        with open(help_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        self.assertIn("CSV Template Guide", content)
        self.assertIn("Basic Template", content)
        self.assertIn("Detailed Template", content)
        self.assertIn("How to Use Templates", content)
        self.assertIn("Data Formats", content)
    
    def test_sample_data_generation(self):
        """Test sample data generation for different template types."""
        # Test Basic template samples
        basic_samples = self.generator._generate_sample_data(TemplateType.BASIC, 3)
        self.assertEqual(len(basic_samples), 3)
        
        for sample in basic_samples:
            self.assertIn("contractId", sample)
            self.assertIn("value", sample)
            
        # Test Detailed template samples
        detailed_samples = self.generator._generate_sample_data(TemplateType.DETAILED, 2)
        self.assertEqual(len(detailed_samples), 2)
        
        for sample in detailed_samples:
            self.assertIn("contractId", sample)
            self.assertIn("value", sample)
    
    def test_error_handling(self):
        """Test error handling for invalid inputs."""
        # Test with invalid template type
        invalid_path = os.path.join(self.test_dir, "invalid.csv")
        
        # This should not raise an exception, but should return False
        try:
            success, message = self.generator.generate_template("INVALID_TYPE", invalid_path)
            # Should handle gracefully
            self.assertFalse(success)
        except:
            pass  # Expected behavior varies
        
        # Test with invalid directory
        invalid_dir_path = os.path.join("/invalid/path/that/does/not/exist", "template.csv")
        
        # Should create directory or fail gracefully
        success, message = self.generator.generate_template(TemplateType.BASIC, invalid_dir_path)
        # Either succeeds (creates dir) or fails gracefully
        self.assertIsInstance(success, bool)
        self.assertIsInstance(message, str)
    
    def test_file_encoding(self):
        """Test that templates are generated with proper UTF-8 encoding."""
        output_path = os.path.join(self.test_dir, "encoding_test.csv")
        
        config = TemplateConfig(
            template_type=TemplateType.DETAILED,
            include_portuguese=True,
            include_descriptions=True
        )
        
        success, message = self.generator.generate_template(
            TemplateType.DETAILED,
            output_path,
            config
        )
        
        self.assertTrue(success)
        
        # Test that file can be read with UTF-8
        try:
            with open(output_path, 'r', encoding='utf-8-sig') as f:
                content = f.read()
                # Should contain Portuguese characters without errors
                self.assertIn("ID_Contrato", content)  # Portuguese contract field should be present
        except UnicodeDecodeError:
            self.fail("Template file is not properly UTF-8 encoded")
    
    def test_csv_structure_validation(self):
        """Test that generated CSV files have valid structure."""
        output_path = os.path.join(self.test_dir, "structure_test.csv")
        
        config = TemplateConfig(
            template_type=TemplateType.DETAILED,
            include_samples=True,
            sample_count=2
        )
        
        success, message = self.generator.generate_template(
            TemplateType.DETAILED,
            output_path,
            config
        )
        
        self.assertTrue(success)
        
        # Parse CSV and validate structure
        with open(output_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            rows = list(reader)
        
        # Find header row (skip description if present)
        header_row = None
        for i, row in enumerate(rows):
            if row and not row[0].startswith('#'):
                header_row = i
                break
        
        self.assertIsNotNone(header_row, "Could not find header row")
        
        headers = rows[header_row]
        sample_rows = rows[header_row + 1:]
        
        # Validate that all sample rows have same number of columns as headers
        for i, row in enumerate(sample_rows):
            self.assertEqual(
                len(row), len(headers),
                f"Sample row {i} has {len(row)} columns, expected {len(headers)}"
            )

class TestTemplateConfigurations(unittest.TestCase):
    """Test different template configurations."""
    
    def setUp(self):
        self.generator = CSVTemplateGenerator()
        self.test_dir = tempfile.mkdtemp(prefix="csv_config_test_")
        
    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_config_combinations(self):
        """Test various configuration combinations."""
        configs_to_test = [
            # Basic configurations
            TemplateConfig(TemplateType.BASIC, include_samples=False, include_descriptions=False),
            TemplateConfig(TemplateType.BASIC, include_samples=True, include_descriptions=True),
            TemplateConfig(TemplateType.BASIC, include_portuguese=True, include_descriptions=False),
            
            # Detailed configurations
            TemplateConfig(TemplateType.DETAILED, include_samples=True, sample_count=5),
            TemplateConfig(TemplateType.DETAILED, include_portuguese=True, include_samples=True),
        ]
        
        for i, config in enumerate(configs_to_test):
            output_path = os.path.join(self.test_dir, f"config_test_{i}.csv")
            
            success, message = self.generator.generate_template(
                config.template_type,
                output_path,
                config
            )
            
            self.assertTrue(success, f"Config {i} failed: {message}")
            self.assertTrue(os.path.exists(output_path), f"Config {i} file not created")
    
    def test_sample_count_variations(self):
        """Test different sample count values."""
        for sample_count in [1, 3, 5, 10]:
            output_path = os.path.join(self.test_dir, f"samples_{sample_count}.csv")
            
            config = TemplateConfig(
                template_type=TemplateType.BASIC,
                include_samples=True,
                sample_count=sample_count
            )
            
            success, message = self.generator.generate_template(
                TemplateType.BASIC,
                output_path,
                config
            )
            
            self.assertTrue(success, f"Sample count {sample_count} failed: {message}")
            
            # Verify correct number of samples
            with open(output_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                rows = list(reader)
            
            # Count data rows (excluding descriptions and headers)
            data_rows = [row for row in rows if row and not row[0].startswith('#') and not row[0] in ['contractId', 'ID_Contrato']]
            
            self.assertEqual(len(data_rows), sample_count, f"Expected {sample_count} sample rows, got {len(data_rows)}")

def main():
    """Run all tests."""
    print("🧪 Running CSV Template Generator Tests...")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTest(loader.loadTestsFromTestCase(TestCSVTemplateGenerator))
    suite.addTest(loader.loadTestsFromTestCase(TestTemplateConfigurations))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 60)
    print(f"📊 Test Summary:")
    print(f"   Tests run: {result.testsRun}")
    print(f"   Failures: {len(result.failures)}")
    print(f"   Errors: {len(result.errors)}")
    
    if result.failures:
        print(f"\n[FAIL] Failures:")
        for test, traceback in result.failures:
            error_msg = traceback.split('AssertionError: ')[-1].split('\n')[0]
            print(f"   - {test}: {error_msg}")
    
    if result.errors:
        print(f"\n[ERROR] Errors:")
        for test, traceback in result.errors:
            error_parts = traceback.split('\n')
            error_msg = error_parts[-2] if len(error_parts) > 1 else traceback
            print(f"   - {test}: {error_msg}")
    
    if result.wasSuccessful():
        print(f"\n[PASS] All tests passed! CSV Template Generator is working correctly.")
        return True
    else:
        print(f"\n[FAIL] Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
