#!/usr/bin/env python3
"""
CSV Template Generator for Portuguese Tax Receipt Automation System

This module provides functionality to generate CSV templates that help users
format their data correctly for receipt processing. It includes various template
types, sample data, and Portuguese localization.

Author: Assistant
Date: August 2025
"""

import csv
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

# Set up logging
logger = logging.getLogger(__name__)

class TemplateType(Enum):
    """Available CSV template types."""
    BASIC = "basic"
    DETAILED = "detailed"

@dataclass
class TemplateField:
    """Represents a field in the CSV template."""
    name: str
    portuguese_name: str
    description: str
    example: str
    required: bool = True
    data_type: str = "string"

@dataclass
class TemplateConfig:
    """Configuration for CSV template generation."""
    template_type: TemplateType
    include_headers: bool = True
    include_samples: bool = False
    include_portuguese: bool = False
    include_descriptions: bool = True
    sample_count: int = 3
    locale: str = "pt"

class CSVTemplateGenerator:
    """
    Generates CSV templates for receipt processing with various configurations.
    
    Features:
    - Multiple template types (basic, detailed, Portuguese)
    - Sample data generation with realistic examples
    - Portuguese localization
    - Field validation and descriptions
    - Business-specific templates
    """
    
    def __init__(self):
        """Initialize the CSV Template Generator."""
        self.templates = self._initialize_templates()
        self.sample_data = self._initialize_sample_data()
        logger.info("CSV Template Generator initialized")
    
    def _initialize_templates(self) -> Dict[TemplateType, List[TemplateField]]:
        """Initialize template field definitions."""
        return {
            TemplateType.BASIC: [
                TemplateField("contractId", "ID_Contrato", "Contract identifier", "123456"),
                TemplateField("fromDate", "Data_Inicio", "Receipt period start date", "2024-07-01"),
                TemplateField("toDate", "Data_Fim", "Receipt period end date", "2024-07-31"),
                TemplateField("paymentDate", "Data_Pagamento", "Payment date", "2024-07-28"),
                TemplateField("receiptType", "Tipo_Recibo", "Type of receipt", "rent"),
                TemplateField("value", "Valor", "Receipt amount", "850.00"),
            ],
            
            TemplateType.DETAILED: [
                TemplateField("contractId", "ID_Contrato", "Contract identifier", "123456"),
                TemplateField("fromDate", "Data_Inicio", "Receipt period start date", "2024-07-01"),
                TemplateField("toDate", "Data_Fim", "Receipt period end date", "2024-07-31"),
                TemplateField("paymentDate", "Data_Pagamento", "Payment date", "2024-07-28"),
                TemplateField("receiptType", "Tipo_Recibo", "Type of receipt", "rent"),
                TemplateField("value", "Valor", "Receipt amount", "850.00"),
                TemplateField("description", "Descricao", "Receipt description", "Monthly rent payment", False),
                TemplateField("reference", "Referencia", "Payment reference", "REF2024070001", False),
            ]
        }
    
    def _initialize_sample_data(self) -> Dict[str, List[Dict[str, str]]]:
        """Initialize sample data for templates."""
        base_date = datetime(2024, 7, 1)
        
        return {
            "residential": [
                {
                    "contractId": "123456", "fromDate": "2024-07-01", "toDate": "2024-07-31",
                    "paymentDate": "2024-07-28", "receiptType": "rent", "value": "850.00", "description": "Monthly rent payment"
                },
                {
                    "contractId": "789012", "fromDate": "2024-07-01", "toDate": "2024-07-31", 
                    "paymentDate": "2024-07-25", "receiptType": "utilities", "value": "120.50", "description": "Utilities payment"
                },
                {
                    "contractId": "345678", "fromDate": "2024-07-01", "toDate": "2024-07-31",
                    "paymentDate": "2024-07-31", "receiptType": "deposit", "value": "1700.00", "description": "Security deposit"
                },
            ],
            
            "portuguese": [
                {
                    "contratoId": "123456", "dataInicio": "01/07/2024", "dataFim": "31/07/2024",
                    "tipoRecibo": "renda", "valor": "850,00", "descricao": "Pagamento mensal de renda"
                },
                {
                    "contratoId": "789012", "dataInicio": "01/07/2024", "dataFim": "31/07/2024",
                    "tipoRecibo": "despesas", "valor": "120,50", "descricao": "Pagamento de condomínio"
                },
                {
                    "contratoId": "345678", "dataInicio": "01/07/2024", "dataFim": "31/07/2024",
                    "tipoRecibo": "caucao", "valor": "1700,00", "descricao": "Caução de arrendamento"
                },
            ],
            
            "business": [
                {
                    "contractId": "BIZ001", "fromDate": "2024-07-01", "toDate": "2024-07-31",
                    "receiptType": "rent", "value": "2500.00", "businessName": "Tech Solutions Lda",
                    "businessNIF": "507123456", "vatRate": "23.00"
                },
                {
                    "contractId": "BIZ002", "fromDate": "2024-07-01", "toDate": "2024-07-31",
                    "receiptType": "rent", "value": "1800.00", "businessName": "Creative Agency SA",
                    "businessNIF": "501987654", "vatRate": "23.00"
                },
            ],
            
            "multi_month": [
                {
                    "contractId": "123456", "fromDate": "2024-07-01", "toDate": "2024-07-31",
                    "receiptType": "rent", "value": "850.00"
                },
                {
                    "contractId": "123456", "fromDate": "2024-08-01", "toDate": "2024-08-31",
                    "receiptType": "rent", "value": "850.00"
                },
                {
                    "contractId": "123456", "fromDate": "2024-09-01", "toDate": "2024-09-30",
                    "receiptType": "rent", "value": "850.00"
                },
            ]
        }
    
    def generate_template(self, 
                         template_type: TemplateType, 
                         output_path: str,
                         config: Optional[TemplateConfig] = None) -> Tuple[bool, str]:
        """
        Generate a CSV template file.
        
        Args:
            template_type: Type of template to generate
            output_path: Path where to save the template
            config: Optional configuration for template generation
            
        Returns:
            Tuple of (success, message)
        """
        try:
            if config is None:
                config = TemplateConfig(template_type=template_type)
            
            # Get template fields
            if template_type not in self.templates:
                return False, f"Unknown template type: {template_type}"
            
            fields = self.templates[template_type]
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                # Determine field names based on configuration
                if config.include_portuguese:
                    field_names = [field.portuguese_name for field in fields]
                else:
                    field_names = [field.name for field in fields]
                
                writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                
                # Write headers (removed subtitle line generation)
                if config.include_headers:
                    writer.writerow(field_names)
                
                # Write sample data if requested
                if config.include_samples:
                    sample_data = self._generate_sample_data(template_type, config.sample_count)
                    
                    for sample in sample_data:
                        row = []
                        for field in fields:
                            # Use appropriate field name based on config
                            field_key = field.portuguese_name if config.include_portuguese else field.name
                            # Try to get value, fallback to example
                            value = sample.get(field_key, sample.get(field.name, field.example))
                            row.append(value)
                        writer.writerow(row)
            
            logger.info(f"CSV template generated: {output_path}")
            return True, f"Template successfully generated: {os.path.basename(output_path)}"
            
        except Exception as e:
            error_msg = f"Failed to generate template: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def _generate_sample_data(self, template_type: TemplateType, count: int) -> List[Dict[str, str]]:
        """Generate sample data for a specific template type."""
        # Use residential sample data for both BASIC and DETAILED templates
        base_samples = self.sample_data.get("residential", [])
        
        # Extend samples if we need more
        samples = []
        for i in range(count):
            if i < len(base_samples):
                samples.append(base_samples[i].copy())
            else:
                # Generate additional samples based on the first one
                if base_samples:
                    new_sample = base_samples[0].copy()
                    # Modify contract ID to make it unique
                    if 'contractId' in new_sample:
                        original_id = new_sample['contractId']
                        if original_id.isdigit():
                            # Numeric ID - add increment
                            base_id = int(original_id)
                            new_sample['contractId'] = str(base_id + i)
                        else:
                            # Non-numeric ID - append increment
                            new_sample['contractId'] = f"{original_id}_{i+1:02d}"
                    samples.append(new_sample)
        
        return samples[:count]
    
    def generate_multiple_templates(self, output_dir: str) -> Tuple[bool, str, Dict[str, bool]]:
        """
        Generate multiple template types in a directory.
        
        Args:
            output_dir: Directory to save templates
            
        Returns:
            Tuple of (overall_success, message, individual_results)
        """
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            results = {}
            templates_to_generate = [
                (TemplateType.BASIC, "basic_template.csv", "Basic CSV template"),
                (TemplateType.DETAILED, "detailed_template.csv", "Detailed CSV template"),
                (TemplateType.DETAILED, "sample_data.csv", "Sample data template"),  # Detailed template with samples
            ]
            
            success_count = 0
            
            for template_type, filename, description in templates_to_generate:
                output_path = os.path.join(output_dir, filename)
                
                # Configure template generation
                if filename == "sample_data.csv":
                    # Special configuration for sample data
                    config = TemplateConfig(
                        template_type=TemplateType.DETAILED,
                        include_samples=True,
                        include_portuguese=False,
                        include_descriptions=True,
                        sample_count=1  # Fixed to 1 sample as requested
                    )
                else:
                    config = TemplateConfig(
                        template_type=template_type,
                        include_samples=False,
                        include_portuguese=False,
                        include_descriptions=True,
                        sample_count=1  # Fixed to 1 sample as requested
                    )
                
                success, message = self.generate_template(template_type, output_path, config)
                results[filename] = success
                
                if success:
                    success_count += 1
                    logger.info(f"Generated {description}: {filename}")
                else:
                    logger.error(f"Failed to generate {description}: {message}")
            
            overall_success = success_count == len(templates_to_generate)
            summary = f"Generated {success_count}/{len(templates_to_generate)} templates successfully"
            
            return overall_success, summary, results
            
        except Exception as e:
            error_msg = f"Failed to generate multiple templates: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, {}
    
    def get_template_info(self, template_type: TemplateType) -> Dict[str, Any]:
        """
        Get information about a specific template type.
        
        Args:
            template_type: Type of template
            
        Returns:
            Dictionary with template information
        """
        if template_type not in self.templates:
            return {"error": f"Unknown template type: {template_type}"}
        
        fields = self.templates[template_type]
        
        return {
            "template_type": template_type.value,
            "field_count": len(fields),
            "required_fields": len([f for f in fields if f.required]),
            "optional_fields": len([f for f in fields if not f.required]),
            "fields": [
                {
                    "name": field.name,
                    "portuguese_name": field.portuguese_name,
                    "description": field.description,
                    "required": field.required,
                    "example": field.example,
                    "data_type": field.data_type
                }
                for field in fields
            ]
        }
    
    def generate_help_file(self, output_path: str) -> Tuple[bool, str]:
        """
        Generate a help file with template information.
        
        Args:
            output_path: Path to save the help file
            
        Returns:
            Tuple of (success, message)
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("# CSV Template Guide for Portuguese Tax Receipt System\n\n")
                f.write("This guide explains the available CSV templates and how to use them.\n\n")
                
                for template_type in TemplateType:
                    info = self.get_template_info(template_type)
                    if "error" in info:
                        continue
                    
                    f.write(f"## {template_type.value.title()} Template\n\n")
                    f.write(f"- **Field Count**: {info['field_count']}\n")
                    f.write(f"- **Required Fields**: {info['required_fields']}\n")
                    f.write(f"- **Optional Fields**: {info['optional_fields']}\n\n")
                    
                    f.write("### Fields:\n\n")
                    for field in info['fields']:
                        required_text = "**Required**" if field['required'] else "*Optional*"
                        f.write(f"- **{field['name']}** ({field['portuguese_name']}) - {required_text}\n")
                        f.write(f"  - Description: {field['description']}\n")
                        f.write(f"  - Example: `{field['example']}`\n\n")
                    
                    f.write("---\n\n")
                
                # Add usage instructions
                f.write("## How to Use Templates\n\n")
                f.write("1. Choose the appropriate template for your needs\n")
                f.write("2. Fill in your data following the examples provided\n")
                f.write("3. Save as CSV with UTF-8 encoding\n")
                f.write("4. Load the CSV in the receipt processing application\n\n")
                
                f.write("## Template Recommendations\n\n")
                f.write("- **Basic**: For simple rent receipts\n")
                f.write("- **Detailed**: For comprehensive receipt information\n")
                f.write("- **Portuguese**: For Portuguese-language data\n")
                f.write("- **Business**: For commercial properties\n")
                f.write("- **Multi-tenant**: For shared properties\n")
                f.write("- **Inheritance**: For inherited properties\n\n")
                
                f.write("## Data Formats\n\n")
                f.write("- **Dates**: Use YYYY-MM-DD format (e.g., 2024-07-01)\n")
                f.write("- **Values**: Use decimal point (e.g., 850.00)\n")
                f.write("- **Receipt Types**: rent, utilities, deposit, maintenance\n")
                f.write("- **Contract IDs**: Numeric identifiers from Portal das Finanças\n")
            
            return True, "Help file generated successfully"
            
        except Exception as e:
            error_msg = f"Failed to generate help file: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

def main():
    """Main function for testing the CSV Template Generator."""
    generator = CSVTemplateGenerator()
    
    # Test template generation
    output_dir = "csv_templates"
    success, message, results = generator.generate_multiple_templates(output_dir)
    
    print(f"Template generation: {message}")
    for filename, result in results.items():
        status = "" if result else ""
        print(f"  {status} {filename}")
    
    # Generate help file
    help_path = os.path.join(output_dir, "CSV_Template_Guide.md")
    help_success, help_message = generator.generate_help_file(help_path)
    print(f"\nHelp file: {help_message}")

if __name__ == "__main__":
    main()
