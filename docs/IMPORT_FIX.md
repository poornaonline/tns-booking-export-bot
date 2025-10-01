# Import Fix - Missing Type Hints

## Issue

When running the application, got this error:

```
Traceback (most recent call last):
  File "/Users/poornajay/Desktop/tns-booking-uploader-bot/main.py", line 20, in <module>
    from src.gui.main_window import MainWindow
  File "/Users/poornajay/Desktop/tns-booking-uploader-bot/src/gui/main_window.py", line 20, in <module>
    class MainWindow:
  File "/Users/poornajay/Desktop/tns-booking-uploader-bot/src/gui/main_window.py", line 980, in MainWindow
    def _execute_single_booking_from_action(self, booking_index: int, booking: Dict[str, Any], item_id: str):
                                                                               ^^^^
NameError: name 'Dict' is not defined. Did you mean: 'dict'?
```

## Root Cause

The `Dict` and `Any` type hints were used in method signatures but not imported from the `typing` module.

## Solution

Added missing imports to `src/gui/main_window.py`:

**Before**:
```python
from typing import Optional
```

**After**:
```python
from typing import Optional, Dict, Any
```

## Files Modified

- `src/gui/main_window.py` (Line 10): Added `Dict, Any` to imports

## Status

✅ **Fixed** - Application now runs without errors.

