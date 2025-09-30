"""
Data validation utilities for TNS Booking Uploader Bot.
"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

from .logger import get_logger

logger = get_logger()


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class Validator:
    """Consolidated validator for files and data."""

    SUPPORTED_EXCEL_EXTENSIONS = {'.xlsx', '.xls'}
    REQUIRED_COLUMNS = ['Date', 'Time', 'Driver', 'From', 'To', 'Reason', 'Shift']

    DATE_FORMATS = ['%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d', '%m-%d-%Y', '%d-%m-%Y']
    TIME_FORMATS = ['%H:%M', '%I:%M %p', '%H:%M:%S', '%I:%M:%S %p']

    @staticmethod
    def is_valid_excel_file(file_path: str) -> bool:
        """Check if the file is a valid Excel file."""
        try:
            path = Path(file_path)

            if not path.exists() or not path.is_file():
                return False

            if path.suffix.lower() not in Validator.SUPPORTED_EXCEL_EXTENSIONS:
                return False

            if path.stat().st_size == 0:
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating file: {str(e)}")
            return False

    @staticmethod
    def validate_column_structure(columns: List[str]) -> bool:
        """Validate Excel file column structure."""
        try:
            # Clean and normalize column names
            columns_clean = []
            for col in columns:
                if col is not None:
                    # Remove any non-printable characters and normalize whitespace
                    clean_col = ''.join(char for char in str(col) if char.isprintable()).strip()
                    columns_clean.append(clean_col)

            columns_lower = [col.lower() for col in columns_clean if col]
            required_lower = [col.lower() for col in Validator.REQUIRED_COLUMNS]

            missing_columns = [col for col in required_lower if col not in columns_lower]

            if missing_columns:
                logger.error(f"Column validation failed. Missing: {missing_columns}")
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating column structure: {str(e)}")
            return False
    
    @staticmethod
    def validate_date_format(date_value) -> bool:
        """Validate date format - handles both strings and datetime objects."""
        if date_value is None or str(date_value).strip() == '' or str(date_value).lower() == 'nan':
            return False

        # If it's already a datetime object (from Excel), it's valid
        if hasattr(date_value, 'strftime'):
            return True

        # If it's a string, try to parse it
        date_str = str(date_value).strip()
        for date_format in Validator.DATE_FORMATS:
            try:
                datetime.strptime(date_str, date_format)
                return True
            except ValueError:
                continue

        return False
    
    @staticmethod
    def validate_time_format(time_value) -> bool:
        """Validate time format - handles both strings and time objects."""
        if time_value is None or str(time_value).strip() == '' or str(time_value).lower() == 'nan':
            return False

        # If it's already a time object (from Excel), it's valid
        if hasattr(time_value, 'hour') and hasattr(time_value, 'minute'):
            return True

        # If it's a string, try to parse it and validate the time
        time_str = str(time_value).strip()

        # Check for invalid times like 24:57, 25:21, etc.
        if ':' in time_str:
            try:
                parts = time_str.split(':')
                if len(parts) >= 2:
                    hour = int(parts[0])
                    minute = int(parts[1])
                    # Valid time ranges: hour 0-23, minute 0-59
                    if hour > 23 or minute > 59:
                        return False
            except ValueError:
                pass  # Will be caught by format validation below

        for time_format in Validator.TIME_FORMATS:
            try:
                datetime.strptime(time_str, time_format)
                return True
            except ValueError:
                continue

        return False
    
    @staticmethod
    def validate_row_data(row_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate a single row of booking data.
        
        Args:
            row_data: Dictionary containing row data
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        try:
            # Validate date
            if not Validator.validate_date_format(row_data.get('Date', '')):
                errors.append("Invalid or missing date")

            # Validate time
            if not Validator.validate_time_format(row_data.get('Time', '')):
                errors.append("Invalid or missing time")
            
            # Validate driver (should not be empty)
            driver = str(row_data.get('Driver', '')).strip()
            if not driver or driver.lower() == 'nan':
                errors.append("Driver name is required")
            
            # Validate From location (should not be empty)
            from_location = str(row_data.get('From', '')).strip()
            if not from_location or from_location.lower() == 'nan':
                errors.append("From location is required")
            
            # Validate To location (should not be empty)
            to_location = str(row_data.get('To', '')).strip()
            if not to_location or to_location.lower() == 'nan':
                errors.append("To location is required")
            
            # Validate Shift (should be numeric)
            shift = str(row_data.get('Shift', '')).strip()
            if shift and shift.lower() != 'nan':
                try:
                    int(shift)
                except ValueError:
                    errors.append("Shift must be a number")
            
            # Reason is optional, so no validation needed
            
            is_valid = len(errors) == 0
            return is_valid, errors
            
        except Exception as e:
            logger.error(f"Error validating row data: {str(e)}")
            return False, [f"Validation error: {str(e)}"]
