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

            # Add Status column if it doesn't exist
            df = self._ensure_status_column(df, file_path)

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
            logger.info(f"Reading Excel file: {file_path}")
            df = pd.read_excel(file_path)
            logger.info(f"Successfully read Excel file with {len(df)} rows")
            return df
        except Exception as e:
            logger.error(f"Error reading Excel file '{file_path}': {str(e)}")
            return None

    def _ensure_status_column(self, df: pd.DataFrame, file_path: str) -> pd.DataFrame:
        """Ensure the Excel file has a Status column. If not, add it and save."""
        try:
            # Normalize column names
            df.columns = df.columns.str.strip()

            # Check if Status column exists
            if 'Status' not in df.columns:
                logger.info("Status column not found. Adding Status column to Excel file...")

                # Add Status column with empty values
                df['Status'] = ''

                # Save the updated DataFrame back to Excel
                df.to_excel(file_path, index=False)
                logger.info(f"✅ Status column added and saved to: {file_path}")
            else:
                logger.info("✅ Status column found in Excel file")

                # Log existing statuses
                status_counts = df['Status'].value_counts()
                if not status_counts.empty:
                    logger.info("Existing statuses in file:")
                    for status, count in status_counts.items():
                        if status and str(status).strip():
                            logger.info(f"  - {status}: {count} booking(s)")

            return df

        except Exception as e:
            logger.error(f"Error ensuring Status column: {str(e)}")
            # Return original DataFrame if there's an error
            return df

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
                        'Shift': row.get('Shift', ''),
                        'Mobile': row.get('Mobile', ''),  # Optional mobile column
                        'Status': row.get('Status', '')  # Status column
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
                        # Log detailed error for this invalid row
                        logger.warning(f"❌ Invalid row {row_data['row_number']}:")
                        for error in row_errors:
                            logger.warning(f"   - {error}")
                            validation_results['errors'].append(f"Row {row_data['row_number']}: {error}")
                    
                except Exception as e:
                    logger.error(f"Error processing row {index + 2}: {str(e)}")
                    validation_results['invalid_count'] += 1
                    validation_results['errors'].append(f"Row {index + 2}: Processing error - {str(e)}")
            
            # Log summary
            logger.info("="*70)
            logger.info("DATA PROCESSING SUMMARY")
            logger.info("="*70)
            logger.info(f"✅ Valid rows: {validation_results['valid_count']}")
            logger.info(f"❌ Invalid rows: {validation_results['invalid_count']}")

            if validation_results['invalid_count'] > 0:
                logger.warning("")
                logger.warning("INVALID ROWS DETAILS:")
                logger.warning("-"*70)
                for error in validation_results['errors']:
                    logger.warning(f"  {error}")
                logger.warning("-"*70)

            logger.info("="*70)

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

    def update_booking_status(self, file_path: str, row_number: int, status: str) -> bool:
        """Update the status of a specific booking in the Excel file.

        Args:
            file_path: Path to the Excel file
            row_number: Row number in Excel (1-indexed, including header)
            status: Status to set ('Done', 'Error', etc.)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Read the Excel file
            df = pd.read_excel(file_path)

            # Normalize column names
            df.columns = df.columns.str.strip()

            # Ensure Status column exists
            if 'Status' not in df.columns:
                df['Status'] = ''

            # Calculate DataFrame index (row_number - 2 because Excel is 1-indexed and has header)
            df_index = row_number - 2

            # Validate index
            if df_index < 0 or df_index >= len(df):
                logger.error(f"Invalid row number: {row_number}")
                return False

            # Update status
            df.at[df_index, 'Status'] = status

            # Save back to Excel
            df.to_excel(file_path, index=False)

            logger.info(f"✅ Updated row {row_number} status to '{status}' in {file_path}")
            return True

        except Exception as e:
            logger.error(f"Error updating booking status: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
