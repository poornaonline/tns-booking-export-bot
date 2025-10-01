# Complete Booking Automation

## Overview

The TNS Booking Uploader Bot now provides **complete end-to-end automation** for creating bookings in the iCabbi portal. The entire booking process is automated from start to finish.

## What's Automated

### Complete Workflow

The automation now handles all steps of the booking creation process:

1. **Step 1: Driver Name Entry**
   - Navigate to create booking page
   - Fill driver name from Excel
   - Wait for Next button to enable
   - Click Next

2. **Step 2: Address, Date, and Time**
   - Resolve location codes to full addresses
   - Fill pickup address with autocomplete
   - Fill destination address with autocomplete
   - Fill date field
   - Fill time field
   - Click Next

3. **Step 3: Intermediate Page** ✨ NEW
   - Wait 3 seconds for page to fully load
   - Click Next button (no fields to fill)

4. **Step 4: Additional Details** ✨ NEW
   - Wait 3 seconds for form to fully load
   - Fill input field (ID: input-163) with "Metro"
   - Click Next

5. **Step 5: Final Confirmation** ✨ NEW
   - Wait for final form to load
   - Click Book button
   - Complete the booking

## How to Use

### Prerequisites

1. **Open iCabbi Portal**
   - Click "Open iCabbi Portal" button
   - Log in to the portal
   - Keep the browser window open

2. **Load Excel File**
   - Click "Select Booking File"
   - Choose your Excel file with booking data
   - Wait for the file to be processed

### Create Booking

1. Click **"Start Processing Bookings"** button

2. The automation will:
   - ✅ Fill all form fields automatically
   - ✅ Navigate through all steps
   - ✅ Click all required buttons
   - ✅ Complete the booking

3. You'll see a success message when done:
   ```
   Booking created successfully!

   The following steps were completed:
   ✓ Step 1: Driver name filled
   ✓ Step 2: Pickup and destination addresses filled
   ✓ Step 2: Date and time filled
   ✓ Step 3: Intermediate page navigated
   ✓ Step 4: Additional details filled (Metro)
   ✓ Step 5: Book button clicked

   Check the browser for confirmation.
   ```

## Technical Details

### New Automation Steps

#### Step 3: Intermediate Page

After clicking Next on the address/date/time form:

```python
# Wait for intermediate page to load
time.sleep(3)  # 3 second wait for page to fully load

# Click Next button (no fields to fill on this page)
next_button = self.page.wait_for_selector('button:has-text("Next"):not([disabled])', timeout=10000)
next_button.click()
time.sleep(2)  # Wait for next page
```

#### Step 4: Fill "Metro" Field

After the intermediate page:

```python
# Wait for form to load
time.sleep(3)  # 3 second wait for page to fully load

# Fill input-163 with "Metro"
input_field = self.page.wait_for_selector('#input-163', timeout=10000)
input_field.click()
input_field.fill('')
input_field.type('Metro', delay=100)

# Click Next
next_button = self.page.wait_for_selector('button:has-text("Next"):not([disabled])', timeout=10000)
next_button.click()
time.sleep(2)  # Wait for final form
```

#### Step 5: Final Confirmation

After filling Metro:

```python
# Wait for final form
time.sleep(2)

# Click Book button
book_button = self.page.wait_for_selector('button:has-text("Book"):not([disabled])', timeout=10000)
book_button.click()

# Wait for confirmation
time.sleep(2)
```

### Logging

The automation provides detailed logging at each step:

```
INFO - Clicking Next button to proceed to step 3...
INFO - Successfully completed booking form step 2 (Address/Date/Time)
INFO - Waiting for step 3 (intermediate page) to load...
INFO - Step 3 page loaded, clicking Next button...
INFO - Successfully clicked Next button on step 3
INFO - Successfully completed step 3 (intermediate page)
INFO - Waiting for step 4 form to load...
INFO - Step 4 page loaded, filling input-163 with 'Metro'...
INFO - Successfully filled 'Metro' in input-163
INFO - Clicking Next button after filling Metro...
INFO - Successfully clicked Next button after step 4
INFO - Successfully completed step 4 (Metro field)
INFO - Waiting for final page with Book button...
INFO - Clicking Book button to complete booking...
INFO - Successfully clicked Book button
INFO - Booking creation completed successfully!
```

### Error Handling

Each step includes error handling:

- If input-163 cannot be found, an error is logged and the process stops
- If Next button is not enabled, the automation waits up to 10 seconds
- If Book button is not found, an error is logged
- All errors are reported to the user via the GUI

## Configuration

### Customizing the "Metro" Value

If you need to change the value entered in the input-163 field:

1. Open `src/web/automation.py`
2. Find line ~265: `input_field.type('Metro', delay=100)`
3. Change `'Metro'` to your desired value

### Adjusting Wait Times

If the forms load slower on your system:

1. Open `src/web/automation.py`
2. Adjust the `time.sleep()` values:
   - Line ~262: `time.sleep(3)` - Wait for step 3 form
   - Line ~280: `time.sleep(2)` - Wait for final form
   - Line ~290: `time.sleep(2)` - Wait for confirmation

## Troubleshooting

### Issue: "Error filling input-163"

**Possible causes:**
- The form structure has changed
- The input field has a different ID
- The page hasn't fully loaded

**Solutions:**
1. Increase the wait time before step 3 (change `time.sleep(3)` to `time.sleep(5)`)
2. Check the browser console for the actual input field ID
3. Update the selector in the code if the ID has changed

### Issue: "Error clicking Book button"

**Possible causes:**
- The Book button is disabled
- Required fields are not filled
- The button text has changed

**Solutions:**
1. Check the browser to see if any fields are missing
2. Verify that all previous steps completed successfully
3. Check the logs for any errors in earlier steps

### Issue: Booking not created

**Possible causes:**
- Network issues
- Form validation errors
- Browser session expired

**Solutions:**
1. Check the browser for error messages
2. Verify your login session is still active
3. Check the logs for detailed error information
4. Try creating a booking manually to verify the form works

## Comparison: Before vs After

### Before (Manual Steps Required)

```
✅ Step 1: Driver name (automated)
✅ Step 2: Address, date, time (automated)
❌ Step 3: Intermediate page (manual)
❌ Step 4: Additional details (manual)
❌ Step 5: Click Book (manual)
```

User had to manually:
- Click Next on intermediate page
- Fill additional form fields
- Click Next button
- Click Book button

### After (Fully Automated)

```
✅ Step 1: Driver name (automated)
✅ Step 2: Address, date, time (automated)
✅ Step 3: Intermediate page (automated) ✨ NEW
✅ Step 4: Additional details (automated) ✨ NEW
✅ Step 5: Click Book (automated) ✨ NEW
```

Everything is automated - just click "Start Processing Bookings" and wait!

## Files Modified

### `src/web/automation.py`

**Method**: `start_booking_creation()`

**Changes**:
- Added step 3: Navigate intermediate page (click Next)
- Added step 4: Fill input-163 with "Metro"
- Added step 5: Click Book button
- Enhanced logging for all new steps
- Added error handling for all new steps

**Lines**: 253-320

### `src/gui/main_window.py`

**Method**: `_start_creating_bookings()`

**Changes**:
- Updated success message to reflect complete automation
- Added checklist of completed steps

**Lines**: 327-344

## Testing

### Manual Test

1. Start the application: `python3 main.py`
2. Click "Open iCabbi Portal" and log in
3. Click "Select Booking File" and choose an Excel file
4. Click "Start Processing Bookings"
5. Watch the automation complete all steps
6. Verify the booking is created in the browser

### Expected Behavior

- All form fields should be filled automatically
- All buttons should be clicked automatically
- The booking should be created without manual intervention
- A success message should appear when complete

### Verification

Check the logs (`logs/tns_uploader_YYYYMMDD.log`) for:

```
INFO - Starting booking creation for X valid bookings
INFO - Filling driver name: [Name]
INFO - Successfully filled driver name and clicked Next button
INFO - Filling pickup address, destination, date, and time...
INFO - Successfully completed booking form step 2
INFO - Waiting for step 3 form to load...
INFO - Successfully filled 'Metro' in input-163
INFO - Successfully clicked Next button
INFO - Successfully clicked Book button
INFO - Booking creation completed successfully!
```

## Future Enhancements

Possible future improvements:

1. **Multiple Bookings**: Process all bookings in the Excel file automatically
2. **Custom Values**: Allow users to configure the "Metro" value via GUI
3. **Retry Logic**: Automatically retry if a step fails
4. **Progress Tracking**: Show progress for each booking in the GUI
5. **Booking Confirmation**: Capture and display booking confirmation numbers

## Summary

✅ **Complete automation achieved!**

The booking creation process is now fully automated from start to finish. Users simply:
1. Open the portal and log in
2. Select their Excel file
3. Click "Start Processing Bookings"
4. Wait for the automation to complete

No manual intervention required! 🎉

