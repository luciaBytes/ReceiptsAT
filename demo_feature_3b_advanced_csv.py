#!/usr/bin/env python3
"""
Feature 3B Demonstration - Advanced CSV Processing Capabilities

This demonstration showcases the enhanced data validation, flexible column support,
and intelligent defaulting capabilities of the new advanced CSV processor.
"""

import sys
import os
import tempfile
from datetime import datetime

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.utils.advanced_csv_processor import AdvancedCSVProcessor
from src.enhanced_csv_handler import EnhancedCSVHandler


def demonstrate_feature_3b():
    """Comprehensive demonstration of Feature 3B capabilities."""
    print("=" * 80)
    print("FEATURE 3B DEMONSTRATION")
    print("Advanced CSV Processing Capabilities")
    print("=" * 80)
    
    # Create a complex CSV with various formats and issues to demonstrate capabilities
    complex_csv_content = """id_contrato,data_inicio,data_fim,tipo,quantia,data_pagamento
123456,15/07/2024,31/07/2024,renda,€850.00,28/07/2024
789012,2024-06-01,2024-06-30,caução,"1,200.50",
999888,01.05.2024,31.05.2024,,750,15/05/2024
111222,2024/08/01,2024/08/31,despesas,€900.00,2024-08-15
333444,1/3/2024,31/3/2024,fiança,1.500,50,
555666,2024.02.01,2024.02.29,arrendamento,€1 200.00,2024-02-28
777888,2024-09-01,2024-09-30,rent,0,2024-09-15
"""
    
    print(f"1. DEMONSTRATING COMPLEX CSV PROCESSING")
    print("-" * 50)
    print("Sample CSV with various formatting challenges:")
    print("• Mixed date formats (Portuguese DD/MM/YYYY, ISO, European DD.MM.YYYY)")
    print("• Portuguese column names (id_contrato, data_inicio, etc.)")
    print("• Mixed receipt types (renda, caução, despesas, fiança, arrendamento)")
    print("• Various value formats (€850.00, 1,200.50, 1.500,50, €1 200.00)")
    print("• Missing values that need intelligent defaulting")
    print("• Invalid entries that need correction")
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as temp_file:
        temp_file.write(complex_csv_content)
        temp_file_path = temp_file.name
    
    try:
        # Initialize enhanced CSV handler
        handler = EnhancedCSVHandler()
        
        # Process with advanced capabilities
        print(f"\n2. PROCESSING WITH ADVANCED CAPABILITIES")
        print("-" * 50)
        success, errors, insights = handler.load_csv_advanced(
            temp_file_path, 
            auto_correct=True,
            strict_validation=False
        )
        
        if success:
            print("✅ CSV processing completed successfully!")
            
            # Show processing insights
            if insights:
                print(f"\n3. PROCESSING INSIGHTS")
                print("-" * 50)
                
                summary = insights['summary']
                print(f"Summary Statistics:")
                print(f"  📊 Total rows processed: {summary['total_rows']}")
                print(f"  ✅ Valid rows: {summary['valid_rows']}")
                print(f"  ❌ Error rows: {summary['error_rows']}")
                print(f"  ⚠️  Warning rows: {summary['warning_rows']}")
                print(f"  📈 Success rate: {summary['success_rate']:.1f}%")
                
                data_analysis = insights['data_analysis']
                print(f"\nData Analysis:")
                print(f"  🏠 Unique contracts: {data_analysis['unique_contracts']}")
                print(f"  📅 Date range: {data_analysis['date_range']['start']} to {data_analysis['date_range']['end']}")
                print(f"  💰 Value range: €{data_analysis['value_range']['min']:.2f} - €{data_analysis['value_range']['max']:.2f}")
                print(f"  📝 Receipt types: {data_analysis['receipt_types']}")
                
                data_quality = insights['data_quality']
                print(f"\nData Quality Metrics:")
                print(f"  🔧 Auto-corrections applied: {insights['auto_corrections']}")
                print(f"  📋 Defaulted values: {data_quality['defaulted_values']}")
                print(f"  📊 Column completeness:")
                for col, completeness in data_quality['column_completeness'].items():
                    print(f"    {col}: {completeness:.1%}")
                
                # Show data quality score
                quality_score = handler.get_data_quality_score()
                print(f"\n  🎯 Overall Data Quality Score: {quality_score:.1f}/100")
            
            # Show processed receipts
            receipts = handler.get_receipts()
            print(f"\n4. PROCESSED RECEIPTS")
            print("-" * 50)
            
            for i, receipt in enumerate(receipts, 1):
                print(f"Receipt {i}:")
                print(f"  📋 Contract: {receipt.contract_id}")
                print(f"  📅 Period: {receipt.from_date} to {receipt.to_date}")
                print(f"  📝 Type: {receipt.receipt_type} {'(defaulted)' if receipt.receipt_type_defaulted else ''}")
                print(f"  💰 Value: €{receipt.value:.2f} {'(defaulted)' if receipt.value_defaulted else ''}")
                print(f"  💳 Payment: {receipt.payment_date} {'(defaulted)' if receipt.payment_date_defaulted else ''}")
                print()
            
            # Show validation report with corrections
            report = handler.get_validation_report()
            if report['warnings']:
                print(f"5. AUTO-CORRECTIONS APPLIED")
                print("-" * 50)
                for warning in report['warnings']:
                    print(f"  Row {warning['row']}: {warning['message']}")
            
            if report['errors']:
                print(f"\n6. REMAINING ISSUES")
                print("-" * 50)
                for error in report['errors']:
                    print(f"  Row {error['row']}: {error['message']}")
            
            # Show improvement suggestions
            suggestions = handler.suggest_csv_improvements()
            print(f"\n7. IMPROVEMENT SUGGESTIONS")
            print("-" * 50)
            for suggestion in suggestions:
                print(f"  💡 {suggestion}")
                
        else:
            print("❌ CSV processing failed:")
            for error in errors:
                print(f"  • {error}")
    
    finally:
        # Clean up
        try:
            os.unlink(temp_file_path)
        except:
            pass
    
    # Demonstrate column mapping flexibility
    print(f"\n8. COLUMN MAPPING FLEXIBILITY DEMO")
    print("-" * 50)
    
    # Test various column name variations
    test_variations = [
        "Standard English: contractId,fromDate,toDate,receiptType,value,paymentDate",
        "Portuguese: id_contrato,data_inicio,data_fim,tipo_recibo,valor,data_pagamento", 
        "Mixed Case: Contract_ID,From_Date,To_Date,Receipt_Type,Amount,Payment_Date",
        "With Typos: contractid,fromdat,todat,receipttype,amnt,paymentdat",
        "Abbreviated: id,start,end,type,rent,paid"
    ]
    
    processor = AdvancedCSVProcessor()
    
    for variation in test_variations:
        description, columns_str = variation.split(": ")
        columns = [col.strip() for col in columns_str.split(",")]
        
        result = processor._build_enhanced_column_mapping(columns)
        
        if result['success']:
            print(f"✅ {description}: Successfully mapped {len(result['mapping'])} columns")
        else:
            print(f"❌ {description}: {result['errors'][0]}")
    
    # Demonstrate value parsing capabilities
    print(f"\n9. VALUE PARSING CAPABILITIES")
    print("-" * 50)
    
    test_values = [
        "€100.00", "1,000.50", "1.000,50", "$1,234.56", "£999.99",
        "1 234.50", "100,50", "1.234", "0", "", "abc"
    ]
    
    print("Value parsing demonstrations:")
    for value_str in test_values:
        parsed_value, was_defaulted = processor._process_value_field(value_str, True)
        status = "defaulted" if was_defaulted else "parsed"
        print(f"  '{value_str}' -> €{parsed_value:.2f} ({status})")
    
    # Demonstrate date format support
    print(f"\n10. DATE FORMAT SUPPORT")
    print("-" * 50)
    
    test_dates = [
        "2024-07-15", "15/07/2024", "15-07-2024", "15.07.2024",
        "2024/07/15", "7/15/2024", "1/7/2024", "invalid-date"
    ]
    
    print("Date format demonstrations:")
    for date_str in test_dates:
        parsed_date, was_corrected = processor._process_date_field(date_str, 'testField', True)
        status = "corrected" if was_corrected else "accepted"
        result = parsed_date if parsed_date else "INVALID"
        print(f"  '{date_str}' -> {result} ({status})")
    
    print(f"\n" + "=" * 80)
    print("FEATURE 3B DEMONSTRATION COMPLETE")
    print("=" * 80)
    print("\n🎉 Key Capabilities Demonstrated:")
    print("✅ Flexible column mapping with fuzzy matching")
    print("✅ Multiple date format support with auto-correction")
    print("✅ Intelligent value parsing (currencies, separators)")
    print("✅ Smart receipt type mapping (Portuguese/English)")
    print("✅ Comprehensive data validation and insights")
    print("✅ Auto-correction with detailed reporting")
    print("✅ Data quality scoring and improvement suggestions")
    print("\n📈 This advanced CSV processor significantly enhances the system's ability")
    print("   to handle real-world CSV files with diverse formats and quality issues!")


if __name__ == "__main__":
    demonstrate_feature_3b()
