# Dynamic Selector Fix - Stable Element Selection

## Version 2.5 - Stable Selectors for Dynamic IDs

### 🎉 Problem Solved

**Issue**: Field IDs change dynamically across page loads, causing automation to fail

**Examples of changing IDs**:
- Mobile field: `input-440` → `input-215` → `input-XXX`
- Ordered By field: `input-373` → `input-163` → `input-351` → `input-158` → `input-XXX`

**Solution**: Use stable selectors based on placeholder text and section titles instead of IDs

---

## The Problem

### Why IDs Fail

Vue.js applications often generate dynamic IDs that change:
- On page reload
- Between sessions
- After form interactions
- During development/deployment

**Example from logs**:
```
ERROR - Error filling input-373: Timeout waiting for #input-373
```

The field exists, but with a different ID (e.g., `input-158` instead of `input-373`)!

### What Changes vs What Stays Stable

| Element Property | Stability | Example |
|------------------|-----------|---------|
| ID attribute | ❌ Changes | `input-440` → `input-215` |
| Placeholder text | ✅ Stable | `"Enter phone number"` |
| Section titles | ✅ Stable | `"Ordered By"` |
| Button text | ✅ Stable | `"Book now"` |
| Class names | ⚠️ Usually stable | `section-title` |

---

## Solution 1: Mobile Number Field

### Old Approach (ID-based) ❌

```python
# This fails when ID changes
mobile_field = self.page.wait_for_selector('#input-440', timeout=5000)
```

**Problem**: ID changes from `input-440` to `input-215` to other values

### New Approach (Placeholder-based) ✅

```python
# This works regardless of ID
mobile_field = self.page.wait_for_selector('input[placeholder="Enter phone number"]', timeout=5000)
```

**Why it works**:
- Placeholder text `"Enter phone number"` doesn't change
- Only one field has this placeholder
- Works across all page loads

**HTML Element**:
```html
<input id="input-XXX" placeholder="Enter phone number" type="text" autocomplete="off">
       ↑ Changes                ↑ Stable
```

---

## Solution 2: Ordered By Field

### Old Approach (ID-based) ❌

```python
# This fails when ID changes
project_field = self.page.wait_for_selector('#input-373', timeout=10000)
```

**Problem**: ID changes from `input-373` to `input-163` to `input-351` to `input-158`

### New Approach (Section Title-based) ✅

```python
# Find by section title, then navigate to input
ordered_by_section = self.page.locator('h5.section-title:has-text("Ordered By")')
ordered_by_row = ordered_by_section.locator('..').locator('..')
ordered_by_input = ordered_by_row.locator('input[type="text"]').first
```

**Why it works**:
- Section title `"Ordered By"` doesn't change
- Navigate from stable element to target element
- Works regardless of ID

**HTML Structure**:
```html
<div class="row">
  <div class="col">
    <h5 class="section-title pb-2">Ordered By</h5>  ← Find this (stable)
    <div>
      <div class="v-input...">
        <div class="v-input__slot">
          <div class="v-text-field__slot">
            <input id="input-XXX" type="text">  ← Navigate to this
                   ↑ Changes
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
```

**Navigation Steps**:
1. Find `h5` with text "Ordered By"
2. Go up to parent row (`.locator('..')` twice)
3. Find `input[type="text"]` within that row
4. Take first match (`.first`)

---

## Solution 3: Book Now Button

### Already Stable ✅

```python
# Button text is stable
book_button = self.page.wait_for_selector('button:has-text("Book now"):not([disabled])', timeout=10000)
```

**Why it works**:
- Button text `"Book now"` doesn't change
- No ID needed

---

## Complete Updated Workflow

### Step 1: Driver & Mobile

```python
# Fill driver name (existing code works)
driver_field.type(driver_name, delay=100)

# Fill mobile using PLACEHOLDER selector
mobile_field = self.page.wait_for_selector('input[placeholder="Enter phone number"]', timeout=5000)
mobile_field.type(mobile_clean, delay=50)
```

### Step 4: Ordered By Field

```python
# Find "Ordered By" section and fill with "Metro"
ordered_by_section = self.page.locator('h5.section-title:has-text("Ordered By")')
ordered_by_row = ordered_by_section.locator('..').locator('..')
ordered_by_input = ordered_by_row.locator('input[type="text"]').first
ordered_by_input.wait_for(state='visible', timeout=10000)
ordered_by_input.type('Metro', delay=100)
```

### Step 5: Book Now

```python
# Click "Book now" button (already stable)
book_button = self.page.wait_for_selector('button:has-text("Book now"):not([disabled])', timeout=10000)
book_button.click()
```

---

## Selector Strategy Guide

### When to Use Each Strategy

| Strategy | Use When | Example |
|----------|----------|---------|
| **Placeholder** | Field has unique placeholder | `input[placeholder="Enter phone number"]` |
| **Section Title** | Field is under a labeled section | Find "Ordered By" → navigate to input |
| **Button Text** | Button has visible text | `button:has-text("Book now")` |
| **Class Name** | Element has unique class | `.multiselect.address-select` |
| **Attribute** | Element has unique attribute | `input[type="text"][readonly]` |

### Avoid These

| Strategy | Why to Avoid | Alternative |
|----------|--------------|-------------|
| **ID** | Changes dynamically | Use placeholder or section title |
| **Index** | Fragile if order changes | Use unique identifier |
| **XPath** | Hard to maintain | Use CSS selectors |

---

## Playwright Locator API

### Key Methods

```python
# Find element
page.locator('selector')
page.wait_for_selector('selector', timeout=5000)

# Navigate DOM
element.locator('..')  # Parent
element.locator('child-selector')  # Child

# Text matching
page.locator('h5:has-text("Ordered By")')
page.locator('button:has-text("Book now")')

# Get first/last
locator.first
locator.last

# Wait for state
locator.wait_for(state='visible', timeout=10000)

# Interact
locator.click()
locator.fill('text')
locator.type('text', delay=100)
```

---

## Testing

### Test Mobile Field

1. **Open portal** and navigate to Step 1
2. **Check HTML**: Look for `<input placeholder="Enter phone number">`
3. **Verify**: Field ID may be different each time
4. **Test**: Selector `input[placeholder="Enter phone number"]` should work

**Expected Logs**:
```
INFO - Mobile number found: 0403 197 449 (cleaned: 0403197449)
INFO - Successfully filled mobile number: 0403197449
```

### Test Ordered By Field

1. **Navigate to Step 4** (final form)
2. **Check HTML**: Look for `<h5 class="section-title">Ordered By</h5>`
3. **Verify**: Input ID may be different each time
4. **Test**: Section title navigation should work

**Expected Logs**:
```
INFO - Filling 'Ordered By' field with 'Metro'...
INFO - Successfully filled 'Metro' in Ordered By field
```

### Test Book Now Button

1. **On Step 4** after filling fields
2. **Check HTML**: Look for `<button>...<span>Book now</span></button>`
3. **Test**: Button text selector should work

**Expected Logs**:
```
INFO - Clicking 'Book now' button to complete booking...
INFO - Successfully clicked 'Book now' button
INFO - Booking creation completed successfully!
```

---

## Troubleshooting

### Mobile Field Not Found

**Error**: `Timeout waiting for input[placeholder="Enter phone number"]`

**Check**:
1. Is the placeholder text exactly `"Enter phone number"`?
2. Is the field visible on the page?
3. Are you on the correct step (Step 1)?

**Debug**:
```python
# Check if field exists
fields = page.query_selector_all('input[placeholder*="phone"]')
print(f"Found {len(fields)} phone fields")
```

### Ordered By Field Not Found

**Error**: `Timeout waiting for h5:has-text("Ordered By")`

**Check**:
1. Is the section title exactly `"Ordered By"`?
2. Is the class name `section-title`?
3. Are you on the correct step (Step 4)?

**Debug**:
```python
# Check section titles
sections = page.query_selector_all('h5.section-title')
for section in sections:
    print(f"Section: {section.text_content()}")
```

### Book Now Button Not Enabled

**Error**: `Button is disabled`

**Check**:
1. Are all required fields filled?
2. Is the form valid?
3. Wait longer for validation?

**Solution**:
```python
# Wait for button to be enabled
page.wait_for_selector('button:has-text("Book now"):not([disabled])', timeout=15000)
```

---

## Files Modified

### `src/web/automation.py`

**Line 257**: Mobile field selector
```python
# Before
mobile_field = self.page.wait_for_selector('#input-440', timeout=5000)

# After
mobile_field = self.page.wait_for_selector('input[placeholder="Enter phone number"]', timeout=5000)
```

**Lines 334-364**: Ordered By field selector
```python
# Before
project_field = self.page.wait_for_selector('#input-373', timeout=10000)

# After
ordered_by_section = self.page.locator('h5.section-title:has-text("Ordered By")')
ordered_by_row = ordered_by_section.locator('..').locator('..')
ordered_by_input = ordered_by_row.locator('input[type="text"]').first
```

---

## Summary

### ✅ Stable Selectors Implemented

| Field | Old Selector | New Selector | Stability |
|-------|--------------|--------------|-----------|
| Mobile | `#input-440` | `input[placeholder="Enter phone number"]` | ✅ High |
| Ordered By | `#input-373` | Section title navigation | ✅ High |
| Book Now | `button:has-text("Book now")` | (already stable) | ✅ High |

### ✅ Benefits

- **Reliable**: Works across page reloads
- **Maintainable**: Selectors based on visible text
- **Robust**: Handles dynamic ID generation
- **Future-proof**: Less likely to break with updates

### ✅ Key Principles

1. **Avoid IDs** for dynamic forms
2. **Use placeholder text** for input fields
3. **Use section titles** for grouped fields
4. **Use button text** for buttons
5. **Navigate from stable to dynamic** elements

---

**Version**: 2.5  
**Date**: 2025-09-30  
**Status**: ✅ Complete and Tested

**Ready to handle dynamic IDs!** 🎉

