#!/usr/bin/env python3
"""
Test script to verify the complete data flow from Excel file to GUI display.
This simulates what happens when a user selects a file.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.excel.processor import ExcelProcessor
from src.utils.logger import get_logger

logger = get_logger()

def simulate_gui_display(booking_data):
    """
    Simulate what the GUI does when displaying booking data.
    This is the same logic as in _on_file_processed() method.
    """
    # This is what the GUI code does (after our fix)
    date_str = booking_data.get('Date', 'N/A')
    if hasattr(date_str, 'strftime'):
        date_str = date_str.strftime('%d/%m/%Y')
    
    time_str = booking_data.get('Time', 'N/A')
    if hasattr(time_str, 'strftime'):
        time_str = time_str.strftime('%H:%M')
    
    driver = booking_data.get('Driver', 'N/A')
    from_loc = booking_data.get('From', 'N/A')
    to_loc = booking_data.get('To', 'N/A')
    
    return {
        'date': date_str,
        'time': time_str,
        'driver': driver,
        'from': from_loc,
        'to': to_loc
    }

def simulate_web_automation(booking_data):
    """
    Simulate what the web automation does when processing booking data.
    This is the same logic as in start_booking_creation() method.
    """
    driver_name = str(booking_data.get('Driver', '')).strip()
    from_location = str(booking_data.get('From', '')).strip()
    to_location = str(booking_data.get('To', '')).strip()
    booking_date = booking_data.get('Date', '')
    booking_time = booking_data.get('Time', '')
    
    return {
        'driver': driver_name,
        'from': from_location,
        'to': to_location,
        'date': booking_date,
        'time': booking_time
    }

def test_complete_data_flow():
    """Test the complete data flow from file selection to display and automation."""
    
    test_file = "sample_booking_data.xlsx"
    
    if not Path(test_file).exists():
        print(f"❌ Test file '{test_file}' not found")
        return False
    
    print(f"\n{'='*70}")
    print(f"Testing Complete Data Flow: File → Processor → GUI → Automation")
    print(f"{'='*70}\n")
    
    # Step 1: User selects file (simulated)
    print(f"📁 Step 1: User selects file")
    print(f"   File: {test_file}")
    print(f"   Path: {Path(test_file).absolute()}\n")
    
    # Step 2: Excel processor reads and processes the file
    print(f"📊 Step 2: Excel Processor reads file")
    processor = ExcelProcessor()
    result = processor.process_file(test_file)
    
    if not result.success:
        print(f"   ❌ Processing failed: {result.error_message}")
        return False
    
    print(f"   ✅ Processing successful")
    print(f"   - Total rows: {result.row_count}")
    print(f"   - Valid rows: {result.valid_rows}")
    print(f"   - Invalid rows: {result.invalid_rows}\n")
    
    if not result.data or len(result.data) == 0:
        print(f"   ❌ No data returned")
        return False
    
    # Step 3: GUI displays the data
    print(f"🖥️  Step 3: GUI displays booking data")
    first_booking = result.data[0]
    
    print(f"   Raw data keys: {list(first_booking.keys())[:7]}")  # Show first 7 keys
    print(f"   Raw data sample:")
    print(f"      Date: {first_booking.get('Date')}")
    print(f"      Time: {first_booking.get('Time')}")
    print(f"      Driver: {first_booking.get('Driver')}")
    print(f"      From: {first_booking.get('From')}")
    print(f"      To: {first_booking.get('To')}\n")
    
    gui_display = simulate_gui_display(first_booking)
    
    print(f"   GUI Display (formatted):")
    print(f"      Date: {gui_display['date']}")
    print(f"      Time: {gui_display['time']}")
    print(f"      Driver: {gui_display['driver']}")
    print(f"      From: {gui_display['from']}")
    print(f"      To: {gui_display['to']}\n")
    
    # Check if GUI display has valid data
    has_valid_data = (
        gui_display['date'] != 'N/A' and
        gui_display['time'] != 'N/A' and
        gui_display['driver'] != 'N/A' and
        gui_display['from'] != 'N/A' and
        gui_display['to'] != 'N/A'
    )
    
    if not has_valid_data:
        print(f"   ❌ GUI display contains 'N/A' values - data not accessible!")
        return False
    
    print(f"   ✅ GUI display shows valid data\n")
    
    # Step 4: Web automation uses the data
    print(f"🌐 Step 4: Web Automation processes booking")
    automation_data = simulate_web_automation(first_booking)
    
    print(f"   Automation data:")
    print(f"      Driver: {automation_data['driver']}")
    print(f"      From: {automation_data['from']}")
    print(f"      To: {automation_data['to']}")
    print(f"      Date: {automation_data['date']}")
    print(f"      Time: {automation_data['time']}\n")
    
    # Check if automation has valid data
    has_valid_automation = (
        automation_data['driver'] and automation_data['driver'] != 'nan' and
        automation_data['from'] and automation_data['from'] != 'nan' and
        automation_data['to'] and automation_data['to'] != 'nan' and
        automation_data['date'] and
        automation_data['time']
    )
    
    if not has_valid_automation:
        print(f"   ❌ Automation data is invalid or empty!")
        return False
    
    print(f"   ✅ Automation has valid data\n")
    
    # Step 5: Verify data consistency
    print(f"🔍 Step 5: Verify data consistency")
    
    # Check that GUI and automation see the same data
    consistency_checks = [
        (gui_display['driver'], automation_data['driver'], "Driver"),
        (gui_display['from'], automation_data['from'], "From"),
        (gui_display['to'], automation_data['to'], "To"),
    ]
    
    all_consistent = True
    for gui_val, auto_val, field_name in consistency_checks:
        if str(gui_val) == str(auto_val):
            print(f"   ✅ {field_name}: GUI and Automation match")
        else:
            print(f"   ❌ {field_name}: Mismatch!")
            print(f"      GUI: {gui_val}")
            print(f"      Automation: {auto_val}")
            all_consistent = False
    
    if not all_consistent:
        return False
    
    print(f"\n   ✅ All data is consistent across components\n")
    
    return True

if __name__ == "__main__":
    success = test_complete_data_flow()
    
    print(f"{'='*70}")
    if success:
        print("✅ COMPLETE DATA FLOW TEST PASSED")
        print("\nThe fix is working correctly:")
        print("  • Excel file is read correctly")
        print("  • Data keys are properly capitalized")
        print("  • GUI can access and display the data")
        print("  • Web automation can access and use the data")
        print("  • Data is consistent across all components")
    else:
        print("❌ COMPLETE DATA FLOW TEST FAILED")
        print("\nThere are still issues with the data flow.")
    print(f"{'='*70}\n")
    
    sys.exit(0 if success else 1)

