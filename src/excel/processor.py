"""
Excel file processing module for TNS Booking Uploader Bot.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import traceback
from dataclasses import dataclass

from ..utils.logger import get_logger
from ..utils.validators import Validator

logger = get_logger()


@dataclass
class ProcessingResult:
    """Result of Excel file processing."""
    success: bool
    data: Optional[List[Dict[str, Any]]] = None
    row_count: int = 0
    valid_rows: int = 0
    invalid_rows: int = 0
    errors: List[str] = None
    error_message: Optional[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class ExcelProcessor:
    """Handles Excel file processing and data validation."""
    
    def __init__(self):
        """Initialize the Excel processor."""
        pass
    
    def process_file(self, file_path: str) -> ProcessingResult:
        """Process an Excel file and validate its contents."""
        try:
            # Validate file
            if not Validator.is_valid_excel_file(file_path):
                return ProcessingResult(success=False, error_message="Invalid Excel file")

            # Read Excel file
            df = self._read_excel_file(file_path)
            if df is None:
                return ProcessingResult(success=False, error_message="Failed to read Excel file")

            # Validate column structure
            if not Validator.validate_column_structure(df.columns.tolist()):
                return ProcessingResult(
                    success=False,
                    error_message="Invalid column structure. Expected: Date, Time, Driver, From, To, Reason, Shift"
                )

            # Process and validate data
            processed_data, validation_results = self._process_data(df)

            return ProcessingResult(
                success=True,
                data=processed_data,
                row_count=len(df),
                valid_rows=validation_results['valid_count'],
                invalid_rows=validation_results['invalid_count'],
                errors=validation_results['errors']
            )

        except Exception as e:
            error_msg = f"Error processing Excel file: {str(e)}"
            logger.error(error_msg)
            logger.error(f"Traceback: {traceback.format_exc()}")
            return ProcessingResult(success=False, error_message=error_msg)
    
    def _read_excel_file(self, file_path: str) -> Optional[pd.DataFrame]:
        """Read Excel file using pandas."""
        try:
            return pd.read_excel(file_path)
        except Exception as e:
            logger.error(f"Error reading Excel file: {str(e)}")
            return None
    
    def _process_data(self, df: pd.DataFrame) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Process and validate DataFrame data."""
        processed_data = []
        validation_results = {
            'valid_count': 0,
            'invalid_count': 0,
            'errors': []
        }
        
        try:
            # Normalize column names (strip whitespace, handle case)
            df.columns = df.columns.str.strip()
            
            # Process each row
            for index, row in df.iterrows():
                try:
                    # Convert row to dictionary
                    row_data = {
                        'Date': row.get('Date', ''),
                        'Time': row.get('Time', ''),
                        'Driver': row.get('Driver', ''),
                        'From': row.get('From', ''),
                        'To': row.get('To', ''),
                        'Reason': row.get('Reason', ''),
                        'Shift': row.get('Shift', '')
                    }
                    
                    # Validate row data
                    is_valid, row_errors = Validator.validate_row_data(row_data)
                    
                    # Add row metadata
                    row_data['row_number'] = index + 2  # +2 because Excel is 1-indexed and has header
                    row_data['is_valid'] = is_valid
                    row_data['errors'] = row_errors
                    
                    processed_data.append(row_data)
                    
                    # Update validation counts
                    if is_valid:
                        validation_results['valid_count'] += 1
                    else:
                        validation_results['invalid_count'] += 1
                        # Add row-specific errors to global errors list
                        for error in row_errors:
                            validation_results['errors'].append(f"Row {row_data['row_number']}: {error}")
                    
                except Exception as e:
                    logger.error(f"Error processing row {index + 2}: {str(e)}")
                    validation_results['invalid_count'] += 1
                    validation_results['errors'].append(f"Row {index + 2}: Processing error - {str(e)}")
            
            logger.info(f"Data processing completed: {validation_results['valid_count']} valid rows, "
                       f"{validation_results['invalid_count']} invalid rows")
            
            return processed_data, validation_results
            
        except Exception as e:
            logger.error(f"Error in data processing: {str(e)}")
            validation_results['errors'].append(f"Data processing error: {str(e)}")
            return processed_data, validation_results
    
    def get_sample_data_format(self) -> Dict[str, str]:
        """Get sample data format for user reference."""
        return {
            'Date': '4/9/2025',
            'Time': '02:09',
            'Driver': 'MAJCEN Dennis',
            'From': 'NME',
            'To': 'CPS03O',
            'Reason': '(optional)',
            'Shift': '1001'
        }
    
    def export_validation_report(self, processed_data: List[Dict[str, Any]],
                               output_path: str) -> bool:
        """Export validation report to Excel file."""
        try:
            # Create DataFrame from processed data
            report_data = []
            for row in processed_data:
                report_row = {
                    'Row Number': row['row_number'],
                    'Date': row['Date'],
                    'Time': row['Time'],
                    'Driver': row['Driver'],
                    'From': row['From'],
                    'To': row['To'],
                    'Reason': row['Reason'],
                    'Shift': row['Shift'],
                    'Valid': 'Yes' if row['is_valid'] else 'No',
                    'Errors': '; '.join(row['errors']) if row['errors'] else ''
                }
                report_data.append(report_row)
            
            # Create DataFrame and save to Excel
            report_df = pd.DataFrame(report_data)
            report_df.to_excel(output_path, index=False, engine='openpyxl')
            
            logger.info(f"Validation report exported to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting validation report: {str(e)}")
            return False
