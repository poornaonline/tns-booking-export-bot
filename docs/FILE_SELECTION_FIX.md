# Excel File Selection Fix

## Problem Summary

The application had an issue where the GUI was not correctly displaying data from the user-selected Excel file. The root cause was a **key mismatch** between the data structure returned by the Excel processor and the keys used by the GUI to access that data.

## Root Cause

### Key Mismatch Issue

1. **Excel Processor** (`src/excel/processor.py`):
   - Returns booking data with **capitalized keys**: `'Date'`, `'Time'`, `'Driver'`, `'From'`, `'To'`, `'Reason'`, `'Shift'`
   - This is defined in lines 102-109 of `processor.py`

2. **GUI Display Code** (`src/gui/main_window.py`):
   - Was using **lowercase keys** to access the data: `'date'`, `'time'`, `'driver'`, `'from'`, `'to'`
   - This was in the `_on_file_processed()` method at lines 489-499

3. **Result**:
   - When the GUI tried to access `booking.get('date')`, it would return `None` or `'N/A'` because the actual key was `'Date'`
   - This made it appear as if the wrong file was being loaded, when in reality the correct file was loaded but the data couldn't be accessed

## Files Modified

### 1. `src/excel/processor.py`

**Changes Made**:
- Added detailed logging to track which file is being read
- Added logging to confirm successful file reading with row count

**Modified Method**: `_read_excel_file()`

```python
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
```

### 2. `src/gui/main_window.py`

**Changes Made**:

#### A. Enhanced File Selection Logging (`_start_upload()` method)
- Added logging when user selects a file
- Added logging when file path is stored
- Added logging when background thread starts

```python
logger.info(f"User selected file: {file_path}")
# ... validation ...
logger.info(f"File path stored in self.selected_file_path: {self.selected_file_path}")
# ... 
logger.info(f"Starting background thread to process file: {file_path}")
```

#### B. Enhanced Processing Logging (`_process_excel_file()` method)
- Added logging to track which file path is passed to the method
- Added logging before calling the Excel processor

```python
logger.info(f"_process_excel_file called with file_path: {file_path}")
# ...
logger.info(f"Calling excel_processor.process_file with: {file_path}")
```

#### C. **CRITICAL FIX**: Corrected Key Names (`_on_file_processed()` method)
- Changed from lowercase keys to capitalized keys to match the Excel processor output
- Added comment explaining the key format

**Before** (lines 489-499):
```python
date_str = booking.get('date', 'N/A')      # ❌ Wrong key
time_str = booking.get('time', 'N/A')      # ❌ Wrong key
driver = booking.get('driver', 'N/A')      # ❌ Wrong key
from_loc = booking.get('from', 'N/A')      # ❌ Wrong key
to_loc = booking.get('to', 'N/A')          # ❌ Wrong key
```

**After** (lines 493-499):
```python
# Note: Excel processor returns capitalized keys (Date, Time, Driver, From, To)
date_str = booking.get('Date', 'N/A')      # ✅ Correct key
time_str = booking.get('Time', 'N/A')      # ✅ Correct key
driver = booking.get('Driver', 'N/A')      # ✅ Correct key
from_loc = booking.get('From', 'N/A')      # ✅ Correct key
to_loc = booking.get('To', 'N/A')          # ✅ Correct key
```

#### D. Enhanced Booking Creation Logging (`_start_creating_bookings()` method)
- Added logging to show which file is being used for booking creation
- Added logging to show the number of bookings being processed

```python
logger.info(f"Starting booking creation with file: {self.selected_file_path}")
logger.info(f"Number of bookings in processed_data: {len(self.processed_data) if self.processed_data else 0}")
```

## Verification

### Test Script Created: `test_file_selection.py`

A test script was created to verify:
1. ✅ Excel files are read correctly
2. ✅ Data keys are capitalized as expected
3. ✅ No lowercase keys exist in the data
4. ✅ File path logging works correctly

**Test Results**: All tests passed ✅

## Impact

### Before the Fix
- GUI would display "N/A" for all booking fields
- Users would think the wrong file was loaded
- Data appeared to be missing or corrupted

### After the Fix
- GUI correctly displays all booking data from the user-selected file
- Date, Time, Driver, From, and To fields are populated correctly
- Enhanced logging makes it easy to track which file is being processed

## How to Verify the Fix

1. **Run the test script**:
   ```bash
   python3 test_file_selection.py
   ```

2. **Check the logs** (`logs/tns_uploader_YYYYMMDD.log`):
   - Look for: `"User selected file: <path>"`
   - Look for: `"Reading Excel file: <path>"`
   - Look for: `"Successfully read Excel file with X rows"`
   - Look for: `"Starting booking creation with file: <path>"`

3. **Test in the GUI**:
   - Click "Select Booking File"
   - Choose an Excel file
   - Verify that the booking table displays the correct data
   - Check that Date, Time, Driver, From, and To columns are populated

## Additional Notes

### Why This Issue Occurred

The issue likely occurred because:
1. Different parts of the codebase were developed at different times
2. The web automation code (`src/web/automation.py`) correctly uses capitalized keys
3. The GUI display code was written with lowercase keys, possibly assuming a different data format
4. No type checking or schema validation was in place to catch this mismatch

### Prevention for Future

To prevent similar issues:
1. ✅ Added inline comments documenting the expected key format
2. ✅ Added comprehensive logging to track data flow
3. 💡 Consider adding type hints and data classes for booking data
4. 💡 Consider adding unit tests that verify key consistency across modules

## Related Files

- `src/excel/processor.py` - Excel file reading and processing
- `src/gui/main_window.py` - GUI display and user interaction
- `src/web/automation.py` - Web automation (already using correct keys)
- `test_file_selection.py` - Verification test script

