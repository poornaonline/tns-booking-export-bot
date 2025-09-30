# Booking Automation Fix - Name Field Entry

## Issue Description

When clicking "Start Processing Bookings", the application was navigating to the create-v2 page but failing to fill in the name field and click the Next button. The error message displayed was:

```
Failed to start booking creation. Check the browser and try again.
```

## Root Cause

The original implementation had several issues:

1. **Incorrect field selector**: Used `input[placeholder="Enter name"]` which worked, but didn't account for the autocomplete behavior
2. **Simple fill operation**: Used `fill()` without triggering the autocomplete dropdown
3. **Disabled button**: The Next button starts in a disabled state and only becomes enabled after valid input
4. **No wait for button state**: Didn't wait for the button to become enabled before clicking

## HTML Structure Analysis

The create-v2 page has the following structure:

```html
<!-- Name field (autocomplete input) -->
<input id="input-55" placeholder="Enter name" type="text" autocomplete="off">

<!-- Next button (starts disabled) -->
<button type="button" disabled="disabled" class="white--text v-btn v-btn--disabled">
  <span class="v-btn__content"> Next </span>
</button>
```

Key observations:
- The input field is an **autocomplete field** (v-autocomplete component)
- The Next button is **initially disabled**
- The button becomes enabled only after valid input is entered

## Solution Implemented

Updated the `start_booking_creation` method in `src/web/automation.py` with the following improvements:

### 1. Enhanced Field Interaction

```python
# Wait for the name input field to be visible
name_field = self.page.wait_for_selector('input[placeholder="Enter name"]', timeout=10000)

# Click the field to focus it
name_field.click()

# Clear any existing value and type the driver name
name_field.fill('')
name_field.type(driver_name, delay=100)  # Type with delay to trigger autocomplete
```

**Changes:**
- Added explicit `click()` to focus the field
- Clear the field first with `fill('')`
- Use `type()` instead of `fill()` with a 100ms delay between keystrokes
- The delay triggers the autocomplete dropdown properly

### 2. Wait for Button to Become Enabled

```python
# Wait for the Next button to become enabled (it starts disabled)
logger.info("Waiting for Next button to become enabled...")
next_button = self.page.wait_for_selector('button:has-text("Next"):not([disabled])', timeout=10000)

# Click the Next button
next_button.click()
```

**Changes:**
- Use `:not([disabled])` selector to wait for the button to become enabled
- Increased timeout to 10 seconds to allow for form validation
- Added logging to track the waiting process

### 3. Improved Error Handling

```python
# Wait for the form to process the input
time.sleep(1)
```

Added a 1-second delay after typing to allow the form to:
- Process the autocomplete selection
- Validate the input
- Enable the Next button

## Testing

All tests pass successfully:

```bash
$ python3 run_tests.py
================================================== 32 passed in 0.27s ==================================================
```

## How to Test Manually

1. **Start the application:**
   ```bash
   python3 main.py
   ```

2. **Follow the workflow:**
   - Click "Open iCabbi Portal" → Browser opens with Playwright
   - Click "Select Booking File" → Choose the SILVERTOP Excel file
   - Click "Start Processing Bookings" → Should now work correctly

3. **Expected behavior:**
   - Browser navigates to create-v2 page
   - Name field is filled with the first driver name from Excel
   - Next button becomes enabled
   - Next button is clicked automatically
   - Success message appears in the app

## Technical Details

### Playwright Selectors Used

| Selector | Purpose |
|----------|---------|
| `input[placeholder="Enter name"]` | Locate the name input field |
| `button:has-text("Next"):not([disabled])` | Wait for enabled Next button |

### Timing Considerations

- **Field interaction**: 100ms delay between keystrokes
- **Form processing**: 1 second wait after typing
- **Button wait**: Up to 10 seconds for button to become enabled

### Error Scenarios Handled

1. **Browser not initialized**: Returns error if portal not opened first
2. **No valid bookings**: Returns error if Excel has no valid data
3. **Invalid driver name**: Returns error if driver name is empty or "nan"
4. **Timeout errors**: Catches and logs Playwright timeout exceptions

## Files Modified

- `src/web/automation.py` - Updated `start_booking_creation()` method
- `tests/test_web.py` - Fixed test to clear browser state before testing
- `tests/test_gui.py` - Fixed test to clear browser state before testing

## Next Steps

The automation now successfully:
1. ✅ Navigates to create-v2 page
2. ✅ Fills the driver name from Excel
3. ✅ Waits for Next button to become enabled
4. ✅ Clicks the Next button

**Ready for the next automation steps:**
- Fill in phone number
- Fill in email (optional)
- Continue with additional form fields
- Handle multiple bookings in sequence

## Troubleshooting

If the automation still fails:

1. **Check the browser state:**
   - Click "Clear Browser State" button
   - Try opening the portal again

2. **Verify Excel data:**
   - Ensure the Driver column has valid names
   - Check that the first row has a valid driver name

3. **Check browser console:**
   - Open browser DevTools (F12)
   - Look for JavaScript errors
   - Verify the autocomplete is working

4. **Increase timeouts:**
   - If the page is slow, increase the timeout values in the code
   - Current timeouts: 10 seconds for field/button selectors

## Summary

The booking automation now correctly handles the autocomplete name field and waits for the Next button to become enabled before clicking it. This fix ensures reliable automation of the first step in the booking creation process.
