# Session Persistence & Mobile Format Update

## Overview

Two important improvements have been implemented:

1. **Session Persistence** - Users no longer need to login repeatedly
2. **International Mobile Format** - Automatic conversion of +61 numbers to local format

## Feature 1: Session Persistence

### What's New

The browser now maintains login sessions across application restarts. Once you log in, you won't need to log in again unless you explicitly clear the session.

### How It Works

#### Persistent Browser Context

The application now uses Playwright's `launch_persistent_context` which:
- Saves all cookies, local storage, and session data
- Stores data in `browser_data/` directory
- Automatically restores session on next launch
- Works like using your regular browser

#### Fallback Mechanism

If persistent context fails, the app falls back to:
- Regular browser with state file (`browser_state.json`)
- Manual state save/restore on browser close

### User Experience

#### Before
```
1. Open application
2. Click "Open iCabbi Portal"
3. Login with username/password ❌ Every time
4. Use application
5. Close application
6. Next time: Login again ❌ Every time
```

#### After
```
1. Open application
2. Click "Open iCabbi Portal"
3. Login with username/password ✅ First time only
4. Use application
5. Close application
6. Next time: Already logged in! ✅ Automatic
```

### Technical Details

#### Browser Data Storage

**Location**: `browser_data/` directory in application folder

**Contents**:
- Cookies
- Local storage
- Session storage
- IndexedDB
- Service workers
- Cache storage

**Persistence**: Data persists across:
- Application restarts
- System reboots
- Browser closes

#### Implementation

**File**: `src/web/automation.py`

```python
# Create persistent context
self.context = self.playwright.chromium.launch_persistent_context(
    user_data_dir=str(self.user_data_dir),
    headless=False,
    args=['--disable-blink-features=AutomationControlled'],
    viewport={'width': 1280, 'height': 720}
)
```

### Logging

#### First Launch (New Session)
```
INFO - Launching browser with persistent context for automatic login
INFO - Using persistent browser context - login session will be saved
INFO - Opening iCabbi portal: https://...
INFO - iCabbi portal opened successfully
```

#### Subsequent Launches (Existing Session)
```
INFO - Launching browser with persistent context for automatic login
INFO - Using persistent browser context - login session will be saved
INFO - Opening iCabbi portal: https://...
INFO - iCabbi portal opened successfully
```

**Note**: You'll be automatically logged in if session is valid

### Clearing Session

If you need to logout or clear the session:

#### Option 1: Delete Browser Data Directory
```bash
rm -rf browser_data/
```

#### Option 2: Use Application (if implemented)
```python
automation.clear_browser_state()
```

#### Option 3: Logout in Browser
- Click logout in the iCabbi portal
- Session will be cleared

### Troubleshooting

#### Issue: Still asking for login

**Possible Causes**:
1. Session expired (server-side timeout)
2. Browser data corrupted
3. Cookies cleared by website

**Solution**:
1. Delete `browser_data/` directory
2. Restart application
3. Login again - session will be saved

#### Issue: Browser data directory growing large

**Cause**: Cache and storage accumulating over time

**Solution**:
1. Periodically delete `browser_data/` directory
2. Login again to create fresh session

---

## Feature 2: International Mobile Format Conversion

### What's New

Mobile numbers with international format (+61 or 61 prefix) are automatically converted to local Australian format (0...).

### Conversion Rules

| Input Format | Output Format | Example |
|--------------|---------------|---------|
| `+61 412 345 678` | `0412345678` | +61 → 0 |
| `+61412345678` | `0412345678` | +61 → 0 |
| `61 412 345 678` | `0412345678` | 61 → 0 |
| `61412345678` | `0412345678` | 61 → 0 |
| `0412 345 678` | `0412345678` | No change |
| `0412345678` | `0412345678` | No change |

### Why This Change?

The iCabbi portal expects Australian mobile numbers in local format:
- ✅ `0412345678` - Accepted
- ❌ `+61412345678` - May not be accepted
- ❌ `61412345678` - May not be accepted

### Implementation

**File**: `src/web/automation.py`

```python
# Clean the mobile number - remove all spaces
mobile_clean = str(mobile_number).replace(' ', '').strip()

# Remove +61 prefix and convert to local format (0...)
if mobile_clean.startswith('+61'):
    mobile_clean = '0' + mobile_clean[3:]  # Replace +61 with 0
elif mobile_clean.startswith('61') and len(mobile_clean) >= 11:
    # Handle 61412345678 format (without +)
    mobile_clean = '0' + mobile_clean[2:]
```

### Excel Examples

#### Before (Would Fail or Be Rejected)

```
| Driver     | Mobile           |
|------------|------------------|
| John Smith | +61 412 345 678  |
| Jane Doe   | 61412345678      |
```

#### After (Automatically Converted)

```
| Driver     | Mobile           | Entered As   |
|------------|------------------|--------------|
| John Smith | +61 412 345 678  | 0412345678   |
| Jane Doe   | 61412345678      | 0412345678   |
```

### Logging

#### International Format Detected
```
INFO - Mobile number found: +61 412 345 678
INFO - Converted international format to local: +61 412 345 678 → 0412345678
INFO - Successfully filled mobile number: 0412345678
```

#### Local Format (No Conversion)
```
INFO - Mobile number found: 0412 345 678 (cleaned: 0412345678)
INFO - Successfully filled mobile number: 0412345678
```

### Edge Cases

#### Case 1: Short Number Starting with 61
```
Input: 61234
Output: 61234 (no conversion - too short)
```

**Logic**: Only converts if length >= 11 characters (61 + 9 digits)

#### Case 2: Number with Hyphens
```
Input: +61-412-345-678
Output: 0412-345-678
```

**Note**: Only spaces are removed, hyphens are preserved

#### Case 3: Already Local Format
```
Input: 0412 345 678
Output: 0412345678
```

**Note**: No conversion needed, just space removal

---

## Testing

### Test Session Persistence

1. **First Run**:
   ```bash
   python3 main.py
   ```
   - Click "Open iCabbi Portal"
   - Login with credentials
   - Close application

2. **Second Run**:
   ```bash
   python3 main.py
   ```
   - Click "Open iCabbi Portal"
   - **Should be already logged in!** ✅

### Test Mobile Format Conversion

```bash
python3 test_mobile_handling.py
```

Expected output:
```
✅ ALL MOBILE HANDLING TESTS PASSED

Mobile number handling is correctly implemented:
  ✓ Mobile numbers are cleaned (spaces removed)
  ✓ International format converted to local (0...)
  ✓ Mobile field is optional (won't fail if missing)
  ✓ Empty/invalid mobiles are skipped
  ✓ Valid mobiles are filled in input-215
```

---

## Files Modified

### 1. `src/web/automation.py`

**Session Persistence** (lines 31-48, 143-175):
- Added `USER_DATA_DIR` constant
- Added `user_data_dir` attribute
- Implemented `launch_persistent_context`
- Added fallback to regular browser

**Mobile Format Conversion** (lines 215-248):
- Added +61 prefix detection
- Added conversion logic
- Enhanced logging

### 2. `test_mobile_handling.py`

- Updated test cases for international format
- Added conversion logic tests
- Updated expected outputs

---

## Summary

### ✅ Session Persistence

- **Benefit**: No repeated logins
- **Storage**: `browser_data/` directory
- **Persistence**: Across restarts and reboots
- **Fallback**: State file if persistent context fails

### ✅ Mobile Format Conversion

- **Benefit**: Automatic international to local conversion
- **Formats**: +61 and 61 prefixes converted to 0
- **Compatibility**: Works with iCabbi portal requirements
- **Logging**: Clear conversion messages

### User Impact

1. **Better UX**: Login once, use forever
2. **Flexibility**: Accept any mobile format in Excel
3. **Reliability**: Automatic format correction
4. **Transparency**: Clear logging of all conversions

---

**Version**: 2.3  
**Date**: 2025-09-30  
**Status**: ✅ Complete and Tested

