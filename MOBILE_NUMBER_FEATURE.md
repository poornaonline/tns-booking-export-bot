# Mobile Number Feature

## Overview

The booking automation now supports an optional **Mobile** column in Excel files. When a mobile number is present, it will be automatically filled in the booking form after entering the driver name.

## Feature Details

### Excel Column

- **Column Name**: `Mobile` (case-insensitive)
- **Status**: Optional - Excel files work with or without this column
- **Format**: Any phone number format (spaces will be automatically removed)

### Behavior

1. **If Mobile column exists and has a value**:
   - Mobile number is cleaned (all spaces removed)
   - Number is filled in input field with ID `input-215`
   - Happens after driver name entry, before clicking Next

2. **If Mobile column is missing or empty**:
   - Automation continues normally
   - No error is thrown
   - Mobile field is skipped

### Space Removal

All spaces in mobile numbers are automatically removed before entry:

| Excel Value | Entered As |
|-------------|------------|
| `0412 345 678` | `0412345678` |
| `04 1234 5678` | `0412345678` |
| `+61 412 345 678` | `+61412345678` |
| `0412345678` | `0412345678` |

**Note**: Only spaces are removed. Other characters (hyphens, parentheses, etc.) are preserved.

## Excel File Structure

### With Mobile Column

```
| Date      | Time  | Driver        | From | To     | Reason | Shift | Mobile        |
|-----------|-------|---------------|------|--------|--------|-------|---------------|
| 4/9/2025  | 02:09 | MAJCEN Dennis | NME  | CPS03O |        | 1001  | 0412 345 678  |
| 4/9/2025  | 03:00 | John Smith    | NME  | CPS03O |        | 1001  | 0412345678    |
| 4/9/2025  | 04:00 | Jane Doe      | NME  | CPS03O |        | 1001  |               |
```

### Without Mobile Column (Still Works)

```
| Date      | Time  | Driver        | From | To     | Reason | Shift |
|-----------|-------|---------------|------|--------|--------|-------|
| 4/9/2025  | 02:09 | MAJCEN Dennis | NME  | CPS03O |        | 1001  |
| 4/9/2025  | 03:00 | John Smith    | NME  | CPS03O |        | 1001  |
```

## Workflow Integration

### Updated Step 1: Driver Name Entry

```
1. Fill driver name
2. Wait 1 second
3. Check for mobile number ✨ NEW
   - If mobile exists and is valid:
     * Clean mobile (remove spaces)
     * Fill input-215 with cleaned mobile
     * Wait 0.5 seconds
   - If mobile is missing/empty:
     * Skip mobile field
     * Continue to next step
4. Wait for Next button to enable
5. Click Next
```

### Complete Workflow (5 Steps)

1. **Step 1**: Driver name + Mobile (optional)
2. **Step 2**: Address, date, time
3. **Step 3**: Intermediate page (click Next)
4. **Step 4**: Fill "Metro" in input-163
5. **Step 5**: Click Book button

## Technical Implementation

### Excel Processor Changes

**File**: `src/excel/processor.py`

Added Mobile to row data extraction:

```python
row_data = {
    'Date': row.get('Date', ''),
    'Time': row.get('Time', ''),
    'Driver': row.get('Driver', ''),
    'From': row.get('From', ''),
    'To': row.get('To', ''),
    'Reason': row.get('Reason', ''),
    'Shift': row.get('Shift', ''),
    'Mobile': row.get('Mobile', '')  # Optional mobile column
}
```

### Automation Changes

**File**: `src/web/automation.py`

Added mobile number handling after driver name entry:

```python
# After filling driver name...

# Check if mobile number exists and fill it
mobile_number = first_booking.get('Mobile', '')
if mobile_number and str(mobile_number).strip() and str(mobile_number).lower() != 'nan':
    # Clean the mobile number - remove all spaces
    mobile_clean = str(mobile_number).replace(' ', '').strip()
    
    logger.info(f"Mobile number found: {mobile_number} (cleaned: {mobile_clean})")
    
    try:
        # Find the mobile input field with ID "input-215"
        mobile_field = self.page.wait_for_selector('#input-215', timeout=5000)
        
        # Click and fill the mobile number
        mobile_field.click()
        mobile_field.fill('')
        mobile_field.type(mobile_clean, delay=50)
        
        logger.info(f"Successfully filled mobile number: {mobile_clean}")
        time.sleep(0.5)  # Brief wait after filling
        
    except Exception as e:
        logger.warning(f"Could not fill mobile number (field may not exist): {e}")
        # Continue anyway - mobile field is optional
else:
    logger.info("No mobile number found in booking data")

# Continue with Next button...
```

## Logging

### With Mobile Number

```
INFO - Filling driver name: MAJCEN Dennis
INFO - Mobile number found: 0412 345 678 (cleaned: 0412345678)
INFO - Successfully filled mobile number: 0412345678
INFO - Waiting for Next button to become enabled...
```

### Without Mobile Number

```
INFO - Filling driver name: MAJCEN Dennis
INFO - No mobile number found in booking data
INFO - Waiting for Next button to become enabled...
```

### Mobile Field Not Found

```
INFO - Filling driver name: MAJCEN Dennis
INFO - Mobile number found: 0412 345 678 (cleaned: 0412345678)
WARNING - Could not fill mobile number (field may not exist): Timeout 5000ms exceeded
INFO - Waiting for Next button to become enabled...
```

## Error Handling

### Graceful Degradation

The mobile number feature is designed to fail gracefully:

1. **If Mobile column doesn't exist**: Automation continues normally
2. **If Mobile value is empty**: Field is skipped
3. **If input-215 field not found**: Warning logged, automation continues
4. **If filling fails**: Warning logged, automation continues

### No Breaking Changes

- Existing Excel files without Mobile column continue to work
- Existing workflows are not affected
- Mobile field is completely optional

## Testing

### Test Script

Run the mobile handling test:

```bash
python3 test_mobile_handling.py
```

Expected output:
```
✅ ALL MOBILE HANDLING TESTS PASSED

Mobile number handling is correctly implemented:
  ✓ Mobile numbers are cleaned (spaces removed)
  ✓ Mobile field is optional (won't fail if missing)
  ✓ Empty/invalid mobiles are skipped
  ✓ Valid mobiles are filled in input-215
  ✓ Logic matches automation code
```

### Manual Testing

1. **Test with Mobile column**:
   - Create Excel file with Mobile column
   - Add mobile numbers with spaces (e.g., "0412 345 678")
   - Run automation
   - Verify mobile is filled in input-215

2. **Test without Mobile column**:
   - Use existing Excel file without Mobile column
   - Run automation
   - Verify automation works normally

3. **Test with empty Mobile values**:
   - Create Excel file with Mobile column
   - Leave some Mobile cells empty
   - Run automation
   - Verify empty mobiles are skipped

## Use Cases

### Use Case 1: All Bookings Have Mobile

```
| Driver     | Mobile        |
|------------|---------------|
| John Smith | 0412 345 678  |
| Jane Doe   | 0413 456 789  |
| Bob Jones  | 0414 567 890  |
```

**Result**: All mobile numbers are filled automatically

### Use Case 2: Some Bookings Have Mobile

```
| Driver     | Mobile        |
|------------|---------------|
| John Smith | 0412 345 678  |
| Jane Doe   |               |
| Bob Jones  | 0414 567 890  |
```

**Result**: 
- John Smith: Mobile filled
- Jane Doe: Mobile skipped
- Bob Jones: Mobile filled

### Use Case 3: No Mobile Column

```
| Driver     |
|------------|
| John Smith |
| Jane Doe   |
```

**Result**: Automation works as before, no mobile handling

## Troubleshooting

### Issue: Mobile number not appearing in form

**Check**:
1. Is the column named "Mobile" in Excel?
2. Does the mobile cell have a value?
3. Check logs for "Mobile number found" message

**Solution**:
- Verify column name is exactly "Mobile" (case-insensitive)
- Ensure mobile cell is not empty
- Check logs for warnings about input-215 not found

### Issue: Mobile number has wrong format

**Check**:
1. Are spaces being removed correctly?
2. Check logs for "cleaned" mobile number

**Solution**:
- Spaces are automatically removed
- Other characters (hyphens, etc.) are preserved
- If format is still wrong, check the Excel cell value

### Issue: Automation fails when Mobile column added

**This shouldn't happen** - the feature is designed to be optional.

**If it does**:
1. Check logs for error messages
2. Verify the Mobile column doesn't break Excel validation
3. Report the issue with logs

## Customization

### Change Input Field ID

If the mobile field has a different ID:

1. Open `src/web/automation.py`
2. Find line ~223:
   ```python
   mobile_field = self.page.wait_for_selector('#input-215', timeout=5000)
   ```
3. Change `#input-215` to your field ID:
   ```python
   mobile_field = self.page.wait_for_selector('#input-XXX', timeout=5000)
   ```

### Change Timeout

To increase the timeout for finding the mobile field:

1. Open `src/web/automation.py`
2. Find line ~223:
   ```python
   mobile_field = self.page.wait_for_selector('#input-215', timeout=5000)
   ```
3. Change `timeout=5000` to a higher value (in milliseconds):
   ```python
   mobile_field = self.page.wait_for_selector('#input-215', timeout=10000)
   ```

### Custom Cleaning Logic

To add custom cleaning (e.g., remove hyphens):

1. Open `src/web/automation.py`
2. Find line ~219:
   ```python
   mobile_clean = str(mobile_number).replace(' ', '').strip()
   ```
3. Add additional replacements:
   ```python
   mobile_clean = str(mobile_number).replace(' ', '').replace('-', '').replace('(', '').replace(')', '').strip()
   ```

## Summary

✅ **Mobile number feature successfully implemented!**

- ✅ Optional Mobile column support
- ✅ Automatic space removal
- ✅ Graceful error handling
- ✅ No breaking changes to existing workflows
- ✅ Comprehensive logging
- ✅ Fully tested

Users can now include mobile numbers in their Excel files for automatic entry during booking creation!

---

**Last Updated**: 2025-09-30  
**Version**: 2.2  
**Status**: ✅ Complete and Tested

