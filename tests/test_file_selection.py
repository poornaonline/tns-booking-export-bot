#!/usr/bin/env python3
"""
Test script to verify that the correct Excel file is being read and processed.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.excel.processor import ExcelProcessor
from src.utils.logger import get_logger

logger = get_logger()

def test_file_processing():
    """Test that the Excel processor reads the correct file."""
    
    # Test with the sample file
    test_file = "sample_booking_data.xlsx"
    
    if not Path(test_file).exists():
        print(f"❌ Test file '{test_file}' not found")
        return False
    
    print(f"\n{'='*60}")
    print(f"Testing Excel File Processing")
    print(f"{'='*60}\n")
    
    print(f"📁 Test file: {test_file}")
    print(f"📍 Full path: {Path(test_file).absolute()}\n")
    
    # Create processor and process file
    processor = ExcelProcessor()
    result = processor.process_file(test_file)
    
    if result.success:
        print(f"✅ File processed successfully!")
        print(f"   - Total rows: {result.row_count}")
        print(f"   - Valid rows: {result.valid_rows}")
        print(f"   - Invalid rows: {result.invalid_rows}")
        
        if result.data and len(result.data) > 0:
            print(f"\n📊 First booking data:")
            first_booking = result.data[0]
            print(f"   - Date: {first_booking.get('Date', 'N/A')}")
            print(f"   - Time: {first_booking.get('Time', 'N/A')}")
            print(f"   - Driver: {first_booking.get('Driver', 'N/A')}")
            print(f"   - From: {first_booking.get('From', 'N/A')}")
            print(f"   - To: {first_booking.get('To', 'N/A')}")
            print(f"   - Reason: {first_booking.get('Reason', 'N/A')}")
            print(f"   - Shift: {first_booking.get('Shift', 'N/A')}")
            
            # Verify keys are capitalized
            print(f"\n🔑 Verifying data keys:")
            expected_keys = ['Date', 'Time', 'Driver', 'From', 'To', 'Reason', 'Shift']
            for key in expected_keys:
                if key in first_booking:
                    print(f"   ✅ '{key}' key found")
                else:
                    print(f"   ❌ '{key}' key NOT found")
                    
            # Check for lowercase keys (should not exist)
            lowercase_keys = ['date', 'time', 'driver', 'from', 'to', 'reason', 'shift']
            lowercase_found = False
            for key in lowercase_keys:
                if key in first_booking:
                    print(f"   ⚠️  Lowercase key '{key}' found (unexpected)")
                    lowercase_found = True
            
            if not lowercase_found:
                print(f"   ✅ No lowercase keys found (correct)")
        
        return True
    else:
        print(f"❌ File processing failed: {result.error_message}")
        return False

if __name__ == "__main__":
    success = test_file_processing()
    print(f"\n{'='*60}")
    if success:
        print("✅ Test PASSED")
    else:
        print("❌ Test FAILED")
    print(f"{'='*60}\n")
    
    sys.exit(0 if success else 1)

