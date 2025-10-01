# Testing the File Selection Fix

## Quick Test

To verify that the file selection fix is working correctly, follow these steps:

### 1. Run Automated Tests

```bash
# Test 1: Verify Excel processor reads files correctly
python3 test_file_selection.py

# Test 2: Verify complete data flow from file to GUI to automation
python3 test_data_flow.py
```

Both tests should show ✅ PASSED.

### 2. Manual GUI Test

1. **Start the application**:
   ```bash
   python3 main.py
   ```

2. **Select a file**:
   - Click the "Select Booking File" button
   - Choose an Excel file (e.g., `sample_booking_data.xlsx`)

3. **Verify the display**:
   - Check that the booking table shows data in all columns:
     - ✅ Date column should show dates (e.g., "04/09/2025")
     - ✅ Time column should show times (e.g., "02:09")
     - ✅ Driver column should show driver names (e.g., "MAJCEN Dennis")
     - ✅ From column should show locations (e.g., "NME")
     - ✅ To column should show locations (e.g., "CPS03O")
   - ❌ If you see "N/A" in these columns, the fix is not working

4. **Check the logs**:
   - Open the log file: `logs/tns_uploader_YYYYMMDD.log`
   - Look for these log entries:
     ```
     INFO - User selected file: /path/to/your/file.xlsx
     INFO - File path stored in self.selected_file_path: /path/to/your/file.xlsx
     INFO - Starting background thread to process file: /path/to/your/file.xlsx
     INFO - _process_excel_file called with file_path: /path/to/your/file.xlsx
     INFO - Reading Excel file: /path/to/your/file.xlsx
     INFO - Successfully read Excel file with X rows
     ```
   - These logs confirm that the correct file is being processed

5. **Test booking creation** (optional):
   - Click "Open iCabbi Portal" and log in
   - Click "Start Processing Bookings"
   - Verify that the driver name is filled correctly
   - Check the logs for:
     ```
     INFO - Starting booking creation with file: /path/to/your/file.xlsx
     INFO - Number of bookings in processed_data: X
     ```

## What Was Fixed

### The Problem
The GUI was using **lowercase keys** (`'date'`, `'time'`, `'driver'`, `'from'`, `'to'`) to access booking data, but the Excel processor returns data with **capitalized keys** (`'Date'`, `'Time'`, `'Driver'`, `'From'`, `'To'`).

This caused the GUI to display "N/A" for all fields, making it appear as if the wrong file was loaded.

### The Solution
Changed the GUI code to use the correct capitalized keys that match the Excel processor output.

**File**: `src/gui/main_window.py`  
**Method**: `_on_file_processed()`  
**Lines**: 493-499

**Before**:
```python
date_str = booking.get('date', 'N/A')      # ❌ Wrong
time_str = booking.get('time', 'N/A')      # ❌ Wrong
driver = booking.get('driver', 'N/A')      # ❌ Wrong
from_loc = booking.get('from', 'N/A')      # ❌ Wrong
to_loc = booking.get('to', 'N/A')          # ❌ Wrong
```

**After**:
```python
date_str = booking.get('Date', 'N/A')      # ✅ Correct
time_str = booking.get('Time', 'N/A')      # ✅ Correct
driver = booking.get('Driver', 'N/A')      # ✅ Correct
from_loc = booking.get('From', 'N/A')      # ✅ Correct
to_loc = booking.get('To', 'N/A')          # ✅ Correct
```

### Additional Improvements
- Added comprehensive logging to track which file is being processed at each step
- Added logging to show the number of bookings being processed
- Added comments in the code to document the expected key format

## Troubleshooting

### If the GUI still shows "N/A" values:

1. **Check the Excel file format**:
   - Make sure the file has the required columns: Date, Time, Driver, From, To, Reason, Shift
   - Column names should match exactly (case-insensitive)

2. **Check the logs**:
   - Look for error messages in `logs/tns_uploader_YYYYMMDD.log`
   - Common issues:
     - "Column validation failed" - Excel file has wrong column names
     - "Failed to read Excel file" - File is corrupted or not a valid Excel file
     - "Invalid Excel file" - File doesn't exist or has wrong extension

3. **Verify the fix was applied**:
   - Open `src/gui/main_window.py`
   - Go to line 493 (in the `_on_file_processed` method)
   - Verify it says `booking.get('Date', 'N/A')` with capital 'D'
   - If it says `booking.get('date', 'N/A')` with lowercase 'd', the fix was not applied

4. **Run the test scripts**:
   ```bash
   python3 test_file_selection.py
   python3 test_data_flow.py
   ```
   - If tests fail, there may be an issue with the fix

### If booking creation doesn't work:

1. **Check that the browser is open**:
   - Click "Open iCabbi Portal" first
   - Log in to the portal
   - Then click "Start Processing Bookings"

2. **Check the logs**:
   - Look for: `"Starting booking creation with file: <path>"`
   - This confirms which file is being used for booking creation

3. **Verify data is loaded**:
   - The booking table should show data before clicking "Start Processing Bookings"
   - If the table is empty, the file wasn't processed correctly

## Files Modified

- `src/excel/processor.py` - Added logging for file reading
- `src/gui/main_window.py` - Fixed key names and added logging
- `test_file_selection.py` - New test script
- `test_data_flow.py` - New comprehensive test script
- `FILE_SELECTION_FIX.md` - Detailed documentation of the fix

## Summary

✅ **The fix ensures that**:
1. The correct Excel file selected by the user is read and processed
2. The GUI displays data from the user-selected file
3. The web automation uses data from the user-selected file
4. Comprehensive logging tracks the file path at every step
5. Data is consistent across all components (GUI, automation, processor)

The issue was **not** that the wrong file was being loaded, but that the GUI couldn't access the data due to a key mismatch. This has now been fixed.

