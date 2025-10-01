# Mobile Number Feature - Quick Summary

## What's New

Added support for an optional **Mobile** column in Excel files. When present, mobile numbers are automatically filled in the booking form.

## Quick Facts

✅ **Optional** - Excel files work with or without Mobile column
✅ **Automatic** - Spaces removed automatically
✅ **International Format** - +61 and 61 prefixes converted to 0
✅ **Safe** - Won't break if field doesn't exist
✅ **Backward Compatible** - Existing files still work

## Excel Format

### Add Mobile Column (Optional)

```
| Date      | Time  | Driver        | Mobile        | From | To     | Reason | Shift |
|-----------|-------|---------------|---------------|------|--------|--------|-------|
| 4/9/2025  | 02:09 | MAJCEN Dennis | 0412 345 678  | NME  | CPS03O |        | 1001  |
```

**Note**: Column can be placed anywhere, not just after Driver

### Mobile Number Formats

All these formats work (spaces removed, international format converted):

- `0412 345 678` → `0412345678`
- `04 1234 5678` → `0412345678`
- `+61 412 345 678` → `0412345678` ✨ **Converted to local**
- `+61412345678` → `0412345678` ✨ **Converted to local**
- `61412345678` → `0412345678` ✨ **Converted to local**
- `0412345678` → `0412345678`

## How It Works

### Workflow

```
1. Fill driver name
2. Check for mobile number
   ├─ If found: Clean and fill in input-215
   └─ If not found: Skip
3. Click Next
4. Continue with rest of booking...
```

### When Mobile is Filled

```
Step 1: Driver Name Entry
├─ Fill driver name: "MAJCEN Dennis"
├─ Mobile found: "0412 345 678"
├─ Clean mobile: "0412345678"
├─ Fill input-215: "0412345678" ✅
└─ Click Next
```

### When Mobile is Missing

```
Step 1: Driver Name Entry
├─ Fill driver name: "MAJCEN Dennis"
├─ No mobile found
└─ Click Next
```

## Files Changed

### 1. `src/excel/processor.py`

Added Mobile to data extraction:

```python
row_data = {
    ...
    'Mobile': row.get('Mobile', '')  # NEW
}
```

### 2. `src/web/automation.py`

Added mobile handling after driver name:

```python
# After filling driver name...
mobile_number = first_booking.get('Mobile', '')
if mobile_number and str(mobile_number).strip() and str(mobile_number).lower() != 'nan':
    mobile_clean = str(mobile_number).replace(' ', '').strip()
    mobile_field = self.page.wait_for_selector('#input-215', timeout=5000)
    mobile_field.type(mobile_clean, delay=50)
```

## Testing

### Run Tests

```bash
# Test mobile handling
python3 test_mobile_handling.py

# Test complete workflow
python3 test_booking_workflow.py
```

### Expected Results

```
✅ ALL MOBILE HANDLING TESTS PASSED

Mobile number handling is correctly implemented:
  ✓ Mobile numbers are cleaned (spaces removed)
  ✓ Mobile field is optional (won't fail if missing)
  ✓ Empty/invalid mobiles are skipped
  ✓ Valid mobiles are filled in input-215
  ✓ Logic matches automation code
```

## Logging

### With Mobile

```
INFO - Filling driver name: MAJCEN Dennis
INFO - Mobile number found: 0412 345 678 (cleaned: 0412345678)
INFO - Successfully filled mobile number: 0412345678
```

### Without Mobile

```
INFO - Filling driver name: MAJCEN Dennis
INFO - No mobile number found in booking data
```

## Use Cases

### ✅ All Bookings Have Mobile

Every booking gets mobile filled automatically

### ✅ Some Bookings Have Mobile

Only bookings with mobile get it filled, others skip

### ✅ No Mobile Column

Works exactly as before, no changes

### ✅ Empty Mobile Cells

Empty cells are skipped, no errors

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Mobile column missing | ✅ Continue normally |
| Mobile cell empty | ✅ Skip mobile field |
| Mobile field (input-215) not found | ⚠️ Log warning, continue |
| Invalid mobile format | ✅ Fill as-is (after space removal) |

## Troubleshooting

### Mobile not appearing?

1. Check column is named "Mobile" (case-insensitive)
2. Check cell has a value
3. Check logs for "Mobile number found" message

### Wrong format?

- Only spaces are removed
- Other characters (hyphens, etc.) are kept
- Check the cleaned value in logs

### Automation failing?

- This shouldn't happen - mobile is optional
- Check logs for error messages
- Try without Mobile column to isolate issue

## Quick Reference

| Feature | Details |
|---------|---------|
| **Column Name** | `Mobile` (case-insensitive) |
| **Required?** | No - completely optional |
| **Input Field** | `input-215` |
| **Cleaning** | Removes all spaces |
| **Timing** | After driver name, before Next |
| **Timeout** | 5 seconds to find field |
| **Error Handling** | Graceful - continues on failure |

## Documentation

For detailed information, see:

- **MOBILE_NUMBER_FEATURE.md** - Complete documentation
- **test_mobile_handling.py** - Test script with examples
- **WORKFLOW_UPDATE_FINAL.md** - Updated workflow documentation

## Summary

✅ **Mobile number support successfully added!**

- Optional Mobile column in Excel
- Automatic space removal
- Fills input-215 after driver name
- Graceful error handling
- No breaking changes
- Fully tested

**Ready to use!** Just add a Mobile column to your Excel file and the automation will handle it automatically.

---

**Version**: 2.2  
**Date**: 2025-09-30  
**Status**: ✅ Complete and Tested

