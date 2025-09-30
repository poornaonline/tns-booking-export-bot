# Field Mapping Reference Card

## Quick Reference for iCabbi Portal Field IDs

### ✅ Correct Field IDs (v2.4)

| Step | Field Name | Field ID | Value Source | Notes |
|------|------------|----------|--------------|-------|
| **Step 1** | Driver Name | (varies) | Excel: Driver | Text input |
| **Step 1** | Mobile Number | `input-440` | Excel: Mobile | ✅ **CORRECTED** from input-215 |
| **Step 2** | Pickup Address | (multiselect) | Excel: From | Autocomplete dropdown |
| **Step 2** | Destination | (multiselect) | Excel: To | Autocomplete dropdown |
| **Step 2** | Date | (Vue picker) | Excel: Date | Format: DD/MM/YYYY |
| **Step 2** | Time | (Vue picker) | Excel: Time | Format: HH:MM |
| **Step 3** | (No fields) | - | - | Just click Next |
| **Step 4** | Ordered By | `input-351` | - | Optional (not filled) |
| **Step 4** | Booking Reason | `input-356` | - | Dropdown (not filled) |
| **Step 4** | Division Dept BU | `input-360` | - | Dropdown (not filled) |
| **Step 4** | Passenger Type | `input-364` | - | Dropdown (not filled) |
| **Step 4** | Num Travellers | `input-368` | - | Optional (not filled) |
| **Step 4** | Project Name | `input-373` | "Metro" | ✅ **CORRECTED** from input-163 |
| **Step 5** | Book Button | "Book now" | Click | ✅ **CORRECTED** from "Book" |

---

## ❌ Incorrect Field IDs (Removed)

| Field ID | Reason | Corrected To |
|----------|--------|--------------|
| `input-215` | Wrong mobile field | `input-440` |
| `input-163` | Doesn't exist on final page | `input-373` |
| "Book" button | Wrong button text | "Book now" |

---

## HTML Element Examples

### Mobile Number Field (Step 1)

```html
<input id="input-440" 
       placeholder="Enter phone number" 
       type="text" 
       autocomplete="off">
```

**Selector**: `#input-440`  
**Action**: Fill with mobile number (converted to local format)

---

### Project Name Field (Step 4)

```html
<input id="input-373" type="text">
```

**Label**: "Project Name if Applicable"  
**Selector**: `#input-373`  
**Action**: Fill with "Metro"

---

### Book Now Button (Step 5)

```html
<button type="button" 
        class="white--text v-btn v-btn--has-bg theme--light v-size--default">
    <span class="v-btn__content"> Book now </span>
</button>
```

**Selector**: `button:has-text("Book now"):not([disabled])`  
**Action**: Click to complete booking

---

## Mobile Number Conversion

### Format Conversion Rules

| Input Format | Output Format | Conversion |
|--------------|---------------|------------|
| `+61 412 345 678` | `0412345678` | +61 → 0, remove spaces |
| `+61412345678` | `0412345678` | +61 → 0 |
| `61 412 345 678` | `0412345678` | 61 → 0, remove spaces |
| `61412345678` | `0412345678` | 61 → 0 |
| `0412 345 678` | `0412345678` | Remove spaces |
| `0412345678` | `0412345678` | No change |

### Conversion Logic

```python
# Remove spaces
mobile_clean = str(mobile_number).replace(' ', '').strip()

# Convert international to local
if mobile_clean.startswith('+61'):
    mobile_clean = '0' + mobile_clean[3:]  # +61 → 0
elif mobile_clean.startswith('61') and len(mobile_clean) >= 11:
    mobile_clean = '0' + mobile_clean[2:]  # 61 → 0
```

---

## Workflow Steps Summary

### Step 1: Driver & Mobile
- Fill driver name
- **If mobile exists**: Convert format and fill `input-440`
- Click Next

### Step 2: Address & Time
- Fill pickup address (autocomplete)
- Fill destination address (autocomplete)
- Fill date (DD/MM/YYYY)
- Fill time (HH:MM)
- Click Next

### Step 3: Intermediate
- Wait 3 seconds
- Click Next (no fields)

### Step 4: Final Form
- Wait 3 seconds
- Fill `input-373` with "Metro"
- Other fields remain empty

### Step 5: Complete
- Click "Book now" button
- Wait for confirmation

---

## UI Table Columns

### Table Layout (v2.4)

```
| Date       | Time  | Driver        | Mobile      | From | To     | Status  |
|------------|-------|---------------|-------------|------|--------|---------|
| 30/10/2025 | 02:41 | BILLSON M.    | 0403197449  | FKND | KANS09 | Pending |
| 30/10/2025 | 03:00 | SMITH J.      | 0412345678  | NME  | CPS    | Pending |
| 30/10/2025 | 04:00 | DOE J.        |             | FKND | KANS09 | Pending |
```

**Columns**: Date, Time, Driver, **Mobile** (new), From, To, Status

---

## Excel Format

### Required Columns

| Column | Required | Format | Example |
|--------|----------|--------|---------|
| Date | ✅ Yes | Date | 30/10/2025 |
| Time | ✅ Yes | Time | 02:41 |
| Driver | ✅ Yes | Text | BILLSON Michelle |
| From | ✅ Yes | Code | FKND |
| To | ✅ Yes | Code | KANS09 |
| Reason | ❌ No | Text | - |
| Shift | ❌ No | Text | 1001 |
| **Mobile** | ❌ No | Text | 0403 197 449 |

### Mobile Column Examples

```
| Driver        | Mobile           | Will Be Entered As |
|---------------|------------------|--------------------|
| BILLSON M.    | 0403 197 449     | 0403197449         |
| SMITH J.      | +61 412 345 678  | 0412345678         |
| DOE J.        | 61412345678      | 0412345678         |
| JONES B.      |                  | (skipped)          |
```

---

## Troubleshooting

### Mobile Field Not Filled

**Symptom**: Mobile number not appearing in browser

**Check**:
1. Field ID is `input-440` (not `input-215`)
2. Mobile column exists in Excel
3. Mobile value is not empty

**Logs**:
```
INFO - Mobile number found: 0403 197 449 (cleaned: 0403197449)
INFO - Successfully filled mobile number: 0403197449
```

### Project Name Field Not Found

**Symptom**: Error "input-163 not found"

**Check**:
1. Field ID is `input-373` (not `input-163`)
2. Waiting for page to load (3 seconds)
3. On correct page (step 4)

**Logs**:
```
INFO - Filling 'Project Name if Applicable' field (input-373) with 'Metro'...
INFO - Successfully filled 'Metro' in Project Name field (input-373)
```

### Book Button Not Found

**Symptom**: Error "Book button not found"

**Check**:
1. Button text is "Book now" (not "Book")
2. Button is enabled (not disabled)
3. All required fields filled

**Logs**:
```
INFO - Clicking 'Book now' button to complete booking...
INFO - Successfully clicked 'Book now' button
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v2.4 | 2025-09-30 | Fixed field IDs: input-440, input-373, "Book now" |
| v2.3 | 2025-09-30 | Added session persistence, mobile format conversion |
| v2.2 | 2025-09-30 | Added mobile number support |
| v2.1 | 2025-09-30 | Added 5-step workflow |
| v1.0 | 2025-09-30 | Initial Excel processing |

---

**Quick Tip**: Always check the browser's developer console (F12) to verify field IDs if automation fails!

**Version**: 2.4  
**Date**: 2025-09-30  
**Status**: ✅ Verified and Tested

