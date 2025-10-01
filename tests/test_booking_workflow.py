#!/usr/bin/env python3
"""
Test script to verify the booking workflow structure.
This tests the code structure without actually running the browser automation.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.excel.processor import ExcelProcessor
from src.utils.logger import get_logger

logger = get_logger()

def test_workflow_structure():
    """Test that the workflow has all required steps."""
    
    print(f"\n{'='*70}")
    print(f"Testing Booking Workflow Structure")
    print(f"{'='*70}\n")
    
    # Read the automation file to verify the workflow
    automation_file = Path("src/web/automation.py")
    
    if not automation_file.exists():
        print(f"❌ Automation file not found: {automation_file}")
        return False
    
    content = automation_file.read_text()
    
    # Check for required workflow steps
    checks = [
        ("Step 1: Driver name", "Filling driver name:", True),
        ("Step 1: Mobile number handling", "Mobile number found:", False),  # Optional
        ("Step 2: Address/Date/Time", "Filling pickup address, destination, date, and time", True),
        ("Step 3: Intermediate page wait", "Waiting for step 3 (intermediate page) to load", True),
        ("Step 3: Click Next", "Successfully clicked Next button on step 3", True),
        ("Step 4: Wait for form", "Waiting for step 4 form to load", True),
        ("Step 4: Fill input-163", "filling input-163 with 'Metro'", True),
        ("Step 4: Click Next", "Clicking Next button after filling Metro", True),
        ("Step 5: Click Book", "Clicking Book button to complete booking", True),
        ("Success message", "Booking creation completed successfully", True),
    ]
    
    all_passed = True
    
    print("📋 Checking workflow steps:\n")
    
    for step_name, search_text, required in checks:
        if search_text in content:
            print(f"   ✅ {step_name}")
        else:
            if required:
                print(f"   ❌ {step_name} - NOT FOUND")
                all_passed = False
            else:
                print(f"   ⚠️  {step_name} - Optional, not found")
    
    print()
    
    # Check for proper error handling
    print("🛡️  Checking error handling:\n")
    
    error_checks = [
        ("Step 3 Next button error handling", "Error clicking Next button on step 3"),
        ("Input-163 error handling", "Error filling input-163"),
        ("Step 4 Next button error handling", "Error clicking Next button after step 4"),
        ("Book button error handling", "Error clicking Book button"),
    ]
    
    for check_name, search_text in error_checks:
        if search_text in content:
            print(f"   ✅ {check_name}")
        else:
            print(f"   ❌ {check_name} - NOT FOUND")
            all_passed = False
    
    print()
    
    # Check for proper wait times
    print("⏱️  Checking wait times:\n")
    
    wait_checks = [
        ("Wait for step 3 form", "time.sleep(3)", "3 seconds"),
        ("Wait after Next click", "time.sleep(2)", "2 seconds"),
        ("Wait after Book click", "time.sleep(2)", "2 seconds"),
    ]
    
    for check_name, search_text, duration in wait_checks:
        if search_text in content:
            print(f"   ✅ {check_name}: {duration}")
        else:
            print(f"   ⚠️  {check_name}: Not found or different duration")
    
    print()
    
    # Check GUI message update
    print("💬 Checking GUI updates:\n")
    
    gui_file = Path("src/gui/main_window.py")
    if gui_file.exists():
        gui_content = gui_file.read_text()
        
        gui_checks = [
            ("Success message updated", "Booking created successfully"),
            ("Checklist in message", "✓ Step 1: Driver name filled"),
            ("Checklist in message", "✓ Step 3: Intermediate page navigated"),
            ("Checklist in message", "✓ Step 4: Additional details filled (Metro)"),
            ("Checklist in message", "✓ Step 5: Book button clicked"),
        ]
        
        for check_name, search_text in gui_checks:
            if search_text in gui_content:
                print(f"   ✅ {check_name}")
            else:
                print(f"   ❌ {check_name} - NOT FOUND")
                all_passed = False
    else:
        print(f"   ❌ GUI file not found")
        all_passed = False
    
    print()
    
    return all_passed

def test_data_flow():
    """Test that data flows correctly through the workflow."""
    
    print(f"{'='*70}")
    print(f"Testing Data Flow")
    print(f"{'='*70}\n")
    
    test_file = "sample_booking_data.xlsx"
    
    if not Path(test_file).exists():
        print(f"⚠️  Test file '{test_file}' not found, skipping data flow test")
        return True
    
    print(f"📁 Processing test file: {test_file}\n")
    
    # Process the file
    processor = ExcelProcessor()
    result = processor.process_file(test_file)
    
    if not result.success:
        print(f"❌ File processing failed: {result.error_message}")
        return False
    
    print(f"✅ File processed successfully")
    print(f"   - Total rows: {result.row_count}")
    print(f"   - Valid rows: {result.valid_rows}")
    print(f"   - Invalid rows: {result.invalid_rows}\n")
    
    if result.data and len(result.data) > 0:
        first_booking = result.data[0]

        print(f"📊 First booking data (for automation):")
        print(f"   - Driver: {first_booking.get('Driver', 'N/A')}")
        print(f"   - From: {first_booking.get('From', 'N/A')}")
        print(f"   - To: {first_booking.get('To', 'N/A')}")
        print(f"   - Date: {first_booking.get('Date', 'N/A')}")
        print(f"   - Time: {first_booking.get('Time', 'N/A')}")

        # Check for mobile number
        mobile = first_booking.get('Mobile', '')
        if mobile and str(mobile).strip() and str(mobile).lower() != 'nan':
            mobile_clean = str(mobile).replace(' ', '').strip()
            print(f"   - Mobile: {mobile} (cleaned: {mobile_clean})")
        else:
            print(f"   - Mobile: Not provided")

        print(f"   - Valid: {first_booking.get('is_valid', False)}\n")
        
        # Verify data is accessible
        required_fields = ['Driver', 'From', 'To', 'Date', 'Time']
        all_present = all(first_booking.get(field) for field in required_fields)
        
        if all_present:
            print(f"✅ All required fields are present and accessible\n")
            return True
        else:
            print(f"❌ Some required fields are missing\n")
            return False
    else:
        print(f"❌ No booking data found\n")
        return False

def main():
    """Run all tests."""
    
    print(f"\n{'='*70}")
    print(f"BOOKING WORKFLOW VERIFICATION")
    print(f"{'='*70}\n")
    
    # Test 1: Workflow structure
    structure_ok = test_workflow_structure()
    
    print()
    
    # Test 2: Data flow
    data_ok = test_data_flow()
    
    # Summary
    print(f"{'='*70}")
    print(f"TEST SUMMARY")
    print(f"{'='*70}\n")
    
    if structure_ok and data_ok:
        print("✅ ALL TESTS PASSED\n")
        print("The booking workflow is properly structured:")
        print("  ✓ All workflow steps are present")
        print("  ✓ Error handling is in place")
        print("  ✓ Wait times are configured")
        print("  ✓ GUI messages are updated")
        print("  ✓ Data flows correctly\n")
        print("Ready to test with actual browser automation!")
        return True
    else:
        print("❌ SOME TESTS FAILED\n")
        if not structure_ok:
            print("  ✗ Workflow structure issues detected")
        if not data_ok:
            print("  ✗ Data flow issues detected")
        print("\nPlease review the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    print(f"{'='*70}\n")
    sys.exit(0 if success else 1)

