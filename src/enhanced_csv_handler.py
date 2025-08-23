"""
Enhanced CSV Handler with Feature 3B - Advanced CSV Processing Capabilities.

Extends the existing CSV handler with advanced data validation, flexible column support,
and intelligent defaulting for complex CSV scenarios.
"""

import os
from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime

try:
    from .utils.advanced_csv_processor import AdvancedCSVProcessor
    from .utils.logger import get_logger
    from .csv_handler import CSVHandler, ReceiptData
except ImportError:
    # Fallback for when imported directly
    from utils.advanced_csv_processor import AdvancedCSVProcessor
    from utils.logger import get_logger
    from csv_handler import CSVHandler, ReceiptData

logger = get_logger(__name__)


class EnhancedCSVHandler(CSVHandler):
    """Enhanced CSV handler with advanced processing capabilities."""
    
    def __init__(self):
        """Initialize with advanced processing capabilities."""
        super().__init__()
        self.advanced_processor = AdvancedCSVProcessor(self)
        self.processing_insights: Optional[Dict[str, Any]] = None
        self.auto_corrections: Dict[int, Dict[str, Any]] = {}
        
    def load_csv_advanced(self, file_path: str, 
                         auto_correct: bool = True,
                         strict_validation: bool = False) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        Load CSV with advanced processing capabilities.
        
        Args:
            file_path: Path to CSV file
            auto_correct: Enable automatic corrections
            strict_validation: Use strict validation rules
            
        Returns:
            Tuple of (success, errors, processing_insights)
        """
        logger.info(f"Loading CSV with advanced processing: {file_path}")
        logger.info(f"  Auto-correct: {auto_correct}")
        logger.info(f"  Strict validation: {strict_validation}")
        
        # Use advanced processor
        success, errors, insights = self.advanced_processor.enhanced_load_csv(
            file_path, auto_correct, strict_validation)
        
        if success:
            # Update our state from the advanced processor
            self.receipts = self.advanced_processor.csv_handler.receipts
            self.validation_errors = []
            self.column_mapping = self.advanced_processor.csv_handler.column_mapping
            self.processing_insights = insights
            self.auto_corrections = self.advanced_processor.auto_corrections
            
            logger.info("Advanced CSV processing completed successfully")
            logger.info(f"  Loaded receipts: {len(self.receipts)}")
            logger.info(f"  Auto-corrections: {len(self.auto_corrections)}")
            
        else:
            self.validation_errors = errors
            logger.error("Advanced CSV processing failed")
            for error in errors[:5]:  # Log first 5 errors
                logger.error(f"  {error}")
        
        return success, errors, insights
    
    def get_processing_insights(self) -> Optional[Dict[str, Any]]:
        """Get detailed processing insights."""
        return self.processing_insights
    
    def get_auto_corrections(self) -> Dict[int, Dict[str, Any]]:
        """Get auto-corrections that were applied."""
        return self.auto_corrections
    
    def get_validation_report(self) -> Dict[str, Any]:
        """Get comprehensive validation report."""
        if hasattr(self.advanced_processor, 'get_validation_report'):
            return self.advanced_processor.get_validation_report()
        else:
            return {
                'summary': {'total_rows': 0, 'valid_rows': 0, 'error_rows': 0, 'warning_rows': 0},
                'errors': [],
                'warnings': [],
                'suggestions': [],
                'auto_corrections': {}
            }
    
    def get_data_quality_score(self) -> float:
        """Calculate overall data quality score (0-100)."""
        if not self.processing_insights:
            return 0.0
        
        summary = self.processing_insights.get('summary', {})
        total_rows = summary.get('total_rows', 0)
        
        if total_rows == 0:
            return 0.0
        
        # Base score from success rate
        success_rate = summary.get('success_rate', 0)
        quality_score = success_rate
        
        # Adjust based on data completeness
        quality_data = self.processing_insights.get('data_quality', {})
        column_completeness = quality_data.get('column_completeness', {})
        
        if column_completeness:
            avg_completeness = sum(column_completeness.values()) / len(column_completeness)
            quality_score = (quality_score + avg_completeness * 100) / 2
        
        # Penalize for too many auto-corrections (indicates data quality issues)
        auto_corrections = self.processing_insights.get('auto_corrections', 0)
        if total_rows > 0:
            correction_rate = auto_corrections / total_rows
            if correction_rate > 0.1:  # More than 10% corrections
                quality_score *= (1 - min(correction_rate, 0.5))  # Reduce by up to 50%
        
        return min(100.0, max(0.0, quality_score))
    
    def export_processing_report(self, file_path: str) -> bool:
        """
        Export comprehensive processing report to CSV.
        
        Args:
            file_path: Path to save the report
            
        Returns:
            Success status
        """
        try:
            if not self.processing_insights:
                logger.warning("No processing insights available for export")
                return False
            
            # Prepare report data
            report_data = []
            
            # Summary section
            summary = self.processing_insights.get('summary', {})
            report_data.append({
                'Section': 'Summary',
                'Metric': 'Total Rows',
                'Value': summary.get('total_rows', 0),
                'Details': ''
            })
            report_data.append({
                'Section': 'Summary',
                'Metric': 'Valid Rows',
                'Value': summary.get('valid_rows', 0),
                'Details': ''
            })
            report_data.append({
                'Section': 'Summary',
                'Metric': 'Error Rows',
                'Value': summary.get('error_rows', 0),
                'Details': ''
            })
            report_data.append({
                'Section': 'Summary',
                'Metric': 'Success Rate',
                'Value': f"{summary.get('success_rate', 0):.1f}%",
                'Details': ''
            })
            report_data.append({
                'Section': 'Summary',
                'Metric': 'Data Quality Score',
                'Value': f"{self.get_data_quality_score():.1f}%",
                'Details': 'Overall quality assessment'
            })
            
            # Data analysis section
            analysis = self.processing_insights.get('data_analysis', {})
            report_data.append({
                'Section': 'Data Analysis',
                'Metric': 'Unique Contracts',
                'Value': analysis.get('unique_contracts', 0),
                'Details': ''
            })
            
            date_range = analysis.get('date_range', {})
            if date_range.get('start') and date_range.get('end'):
                report_data.append({
                    'Section': 'Data Analysis',
                    'Metric': 'Date Range',
                    'Value': f"{date_range['start']} to {date_range['end']}",
                    'Details': 'Period covered by receipts'
                })
            
            value_range = analysis.get('value_range', {})
            if value_range.get('min') is not None and value_range.get('max') is not None:
                report_data.append({
                    'Section': 'Data Analysis',
                    'Metric': 'Value Range',
                    'Value': f"€{value_range['min']:.2f} - €{value_range['max']:.2f}",
                    'Details': 'Min and max receipt values'
                })
            
            # Receipt types
            receipt_types = analysis.get('receipt_types', {})
            for receipt_type, count in receipt_types.items():
                report_data.append({
                    'Section': 'Receipt Types',
                    'Metric': receipt_type.title(),
                    'Value': count,
                    'Details': f'Number of {receipt_type} receipts'
                })
            
            # Data quality metrics
            quality_data = self.processing_insights.get('data_quality', {})
            defaulted_values = quality_data.get('defaulted_values', {})
            for field, count in defaulted_values.items():
                if count > 0:
                    report_data.append({
                        'Section': 'Data Quality',
                        'Metric': f'Defaulted {field.replace("_", " ").title()}',
                        'Value': count,
                        'Details': f'Fields that used default values'
                    })
            
            # Column completeness
            column_completeness = quality_data.get('column_completeness', {})
            for column, completeness in column_completeness.items():
                report_data.append({
                    'Section': 'Column Completeness',
                    'Metric': column,
                    'Value': f"{completeness:.1%}",
                    'Details': 'Percentage of non-empty values'
                })
            
            # Auto-corrections
            auto_corrections = self.processing_insights.get('auto_corrections', 0)
            if auto_corrections > 0:
                report_data.append({
                    'Section': 'Processing',
                    'Metric': 'Auto-Corrections',
                    'Value': auto_corrections,
                    'Details': 'Number of automatic corrections applied'
                })
            
            # Export using parent class method
            return self.export_report(report_data, file_path)
            
        except Exception as e:
            logger.error(f"Error exporting processing report: {str(e)}")
            return False
    
    def get_correction_summary(self) -> List[Dict[str, Any]]:
        """Get summary of all corrections that were applied."""
        if not self.auto_corrections:
            return []
        
        corrections_summary = []
        
        for row_num, corrections in self.auto_corrections.items():
            for field, corrected_value in corrections.items():
                corrections_summary.append({
                    'row': row_num,
                    'field': field,
                    'corrected_value': corrected_value,
                    'correction_type': 'auto-correction'
                })
        
        return corrections_summary
    
    def suggest_csv_improvements(self) -> List[str]:
        """Suggest improvements for better CSV processing."""
        suggestions = []
        
        if not self.processing_insights:
            return ["Process a CSV file first to get improvement suggestions"]
        
        # Analyze data quality
        quality_score = self.get_data_quality_score()
        
        if quality_score < 80:
            suggestions.append("Consider reviewing your CSV data quality - several issues were found")
        
        # Check for many auto-corrections
        auto_corrections = self.processing_insights.get('auto_corrections', 0)
        summary = self.processing_insights.get('summary', {})
        total_rows = summary.get('total_rows', 0)
        
        if total_rows > 0 and auto_corrections / total_rows > 0.2:
            suggestions.append("Many automatic corrections were needed - consider standardizing your CSV format")
        
        # Check column completeness
        quality_data = self.processing_insights.get('data_quality', {})
        column_completeness = quality_data.get('column_completeness', {})
        
        for column, completeness in column_completeness.items():
            if completeness < 0.5:  # Less than 50% complete
                suggestions.append(f"Column '{column}' has many missing values ({completeness:.1%} complete)")
        
        # Check defaulted values
        defaulted_values = quality_data.get('defaulted_values', {})
        for field, count in defaulted_values.items():
            if total_rows > 0 and count / total_rows > 0.3:  # More than 30% defaulted
                suggestions.append(f"Many {field.replace('_', ' ')} values were defaulted - consider including this data")
        
        # Date range suggestions
        analysis = self.processing_insights.get('data_analysis', {})
        date_range = analysis.get('date_range', {})
        
        if date_range.get('start') and date_range.get('end'):
            try:
                start_date = datetime.strptime(date_range['start'], '%Y-%m-%d')
                end_date = datetime.strptime(date_range['end'], '%Y-%m-%d')
                
                if (end_date - start_date).days > 730:  # More than 2 years
                    suggestions.append("CSV contains a very long date range - consider processing in smaller batches")
            except ValueError:
                pass
        
        if not suggestions:
            suggestions.append("Your CSV data quality looks good! No major improvements needed.")
        
        return suggestions
    
    # Override parent method to use advanced processing by default
    def load_csv(self, file_path: str) -> Tuple[bool, List[str]]:
        """
        Load CSV with basic compatibility, using advanced processing internally.
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            Tuple of (success, error_messages) for compatibility
        """
        success, errors, _ = self.load_csv_advanced(file_path, auto_correct=True, strict_validation=False)
        return success, errors
