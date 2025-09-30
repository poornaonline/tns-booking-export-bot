"""
Tests for Excel processing functionality.
"""

import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path
import sys

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.excel.processor import ExcelProcessor
from src.utils.validators import Validator


class TestValidator:
    """Test cases for consolidated Validator."""
    
    def test_valid_xlsx_file(self):
        """Test validation of valid XLSX file."""
        # Create a temporary XLSX file
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            # Create a simple DataFrame and save it
            df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
            df.to_excel(tmp.name, index=False)
            tmp_path = tmp.name
        
        try:
            assert Validator.is_valid_excel_file(tmp_path) == True
        finally:
            os.unlink(tmp_path)
    
    def test_invalid_file_extension(self):
        """Test validation of file with invalid extension."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp:
            tmp.write(b"test content")
            tmp_path = tmp.name
        
        try:
            assert Validator.is_valid_excel_file(tmp_path) == False
        finally:
            os.unlink(tmp_path)
    
    def test_nonexistent_file(self):
        """Test validation of non-existent file."""
        assert Validator.is_valid_excel_file("nonexistent_file.xlsx") == False
    
    def test_empty_file(self):
        """Test validation of empty file."""
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            assert Validator.is_valid_excel_file(tmp_path) == False
        finally:
            os.unlink(tmp_path)


    def test_valid_column_structure(self):
        """Test validation of correct column structure."""
        columns = ['Date', 'Time', 'Driver', 'From', 'To', 'Reason', 'Shift']
        assert Validator.validate_column_structure(columns) == True

    def test_invalid_column_structure_missing_columns(self):
        """Test validation with missing columns."""
        columns = ['Date', 'Time', 'Driver']  # Missing columns
        assert Validator.validate_column_structure(columns) == False

    def test_case_insensitive_column_validation(self):
        """Test that column validation is case-insensitive."""
        columns = ['date', 'TIME', 'Driver', 'from', 'TO', 'reason', 'SHIFT']
        assert Validator.validate_column_structure(columns) == True

    def test_extra_columns_allowed(self):
        """Test that extra columns beyond required ones are allowed."""
        columns = ['Date', 'Time', 'Driver', 'From', 'To', 'Reason', 'Shift', 'Extra1', 'Notes', 'Status']
        assert Validator.validate_column_structure(columns) == True

    def test_valid_date_formats(self):
        """Test validation of various date formats."""
        valid_dates = ['4/9/2025', '04/09/2025', '2025-04-09', '09-04-2025']

        for date_str in valid_dates:
            assert Validator.validate_date_format(date_str) == True

    def test_invalid_date_formats(self):
        """Test validation of invalid date formats."""
        invalid_dates = ['', 'nan', 'invalid_date', '32/13/2025', None]

        for date_str in invalid_dates:
            assert Validator.validate_date_format(date_str) == False

    def test_valid_time_formats(self):
        """Test validation of various time formats."""
        valid_times = ['02:09', '14:30', '02:09 AM', '02:09:00']

        for time_str in valid_times:
            assert Validator.validate_time_format(time_str) == True

    def test_invalid_time_formats(self):
        """Test validation of invalid time formats."""
        invalid_times = ['', 'nan', 'invalid_time', '25:00', None]

        for time_str in invalid_times:
            assert Validator.validate_time_format(time_str) == False

    def test_valid_row_data(self):
        """Test validation of valid row data."""
        row_data = {
            'Date': '4/9/2025',
            'Time': '02:09',
            'Driver': 'MAJCEN Dennis',
            'From': 'NME',
            'To': 'CPS03O',
            'Reason': '',
            'Shift': '1001'
        }

        is_valid, errors = Validator.validate_row_data(row_data)
        assert is_valid == True
        assert len(errors) == 0

    def test_invalid_row_data(self):
        """Test validation of invalid row data."""
        row_data = {
            'Date': 'invalid_date',
            'Time': 'invalid_time',
            'Driver': '',
            'From': '',
            'To': '',
            'Reason': '',
            'Shift': 'invalid_shift'
        }

        is_valid, errors = Validator.validate_row_data(row_data)
        assert is_valid == False
        assert len(errors) > 0


class TestExcelProcessor:
    """Test cases for ExcelProcessor."""
    
    def create_test_excel_file(self, data, file_path):
        """Helper method to create test Excel files."""
        df = pd.DataFrame(data)
        df.to_excel(file_path, index=False)
    
    def test_process_valid_excel_file(self):
        """Test processing of valid Excel file."""
        # Create test data
        test_data = {
            'Date': ['4/9/2025', '4/9/2025'],
            'Time': ['02:09', '02:41'],
            'Driver': ['MAJCEN Dennis', 'JAMES Quin'],
            'From': ['NME', 'FKND'],
            'To': ['CPS03O', 'KANS09'],
            'Reason': ['', ''],
            'Shift': ['1001', '211']
        }
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            self.create_test_excel_file(test_data, tmp.name)
            tmp_path = tmp.name
        
        try:
            processor = ExcelProcessor()
            result = processor.process_file(tmp_path)
            
            assert result.success == True
            assert result.row_count == 2
            assert result.valid_rows == 2
            assert result.invalid_rows == 0
            assert len(result.data) == 2
            
        finally:
            os.unlink(tmp_path)
    
    def test_process_invalid_excel_file(self):
        """Test processing of Excel file with invalid data."""
        # Create test data with invalid entries
        test_data = {
            'Date': ['invalid_date', '4/9/2025'],
            'Time': ['invalid_time', '02:41'],
            'Driver': ['', 'JAMES Quin'],
            'From': ['', 'FKND'],
            'To': ['', 'KANS09'],
            'Reason': ['', ''],
            'Shift': ['invalid_shift', '211']
        }
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            self.create_test_excel_file(test_data, tmp.name)
            tmp_path = tmp.name
        
        try:
            processor = ExcelProcessor()
            result = processor.process_file(tmp_path)
            
            assert result.success == True
            assert result.row_count == 2
            assert result.valid_rows == 1
            assert result.invalid_rows == 1
            assert len(result.errors) > 0
            
        finally:
            os.unlink(tmp_path)
    
    def test_process_file_with_wrong_columns(self):
        """Test processing of Excel file with wrong column structure."""
        # Create test data with wrong columns
        test_data = {
            'Wrong1': ['value1', 'value2'],
            'Wrong2': ['value3', 'value4']
        }

        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            self.create_test_excel_file(test_data, tmp.name)
            tmp_path = tmp.name

        try:
            processor = ExcelProcessor()
            result = processor.process_file(tmp_path)

            assert result.success == False
            assert 'Invalid column structure' in result.error_message

        finally:
            os.unlink(tmp_path)

    def test_process_file_with_extra_columns(self):
        """Test processing of Excel file with extra columns beyond required ones."""
        # Create test data with required columns plus extra ones
        test_data = {
            'Date': ['4/9/2025', '4/9/2025'],
            'Time': ['02:09', '02:41'],
            'Driver': ['MAJCEN Dennis', 'JAMES Quin'],
            'From': ['NME', 'FKND'],
            'To': ['CPS03O', 'KANS09'],
            'Reason': ['', ''],
            'Shift': ['1001', '211'],
            # Extra columns that should be ignored
            'Extra_Column': ['Extra1', 'Extra2'],
            'Notes': ['Note1', 'Note2'],
            'Status': ['Active', 'Inactive']
        }

        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            self.create_test_excel_file(test_data, tmp.name)
            tmp_path = tmp.name

        try:
            processor = ExcelProcessor()
            result = processor.process_file(tmp_path)

            # Should succeed and extract only required columns
            assert result.success == True
            assert result.row_count == 2
            assert result.valid_rows == 2
            assert result.invalid_rows == 0
            assert len(result.data) == 2

            # Verify that only required columns are extracted
            first_row = result.data[0]
            required_keys = set(['Date', 'Time', 'Driver', 'From', 'To', 'Reason', 'Shift'])
            extracted_required_keys = set(key for key in first_row.keys() if key in required_keys)
            assert extracted_required_keys == required_keys

            # Verify extra columns are not in the extracted data (except metadata)
            assert 'Extra_Column' not in first_row
            assert 'Notes' not in first_row
            assert 'Status' not in first_row

        finally:
            os.unlink(tmp_path)
    
    def test_get_sample_data_format(self):
        """Test getting sample data format."""
        processor = ExcelProcessor()
        sample = processor.get_sample_data_format()
        
        assert isinstance(sample, dict)
        assert 'Date' in sample
        assert 'Time' in sample
        assert 'Driver' in sample
        assert 'From' in sample
        assert 'To' in sample
        assert 'Reason' in sample
        assert 'Shift' in sample


if __name__ == '__main__':
    pytest.main([__file__])
