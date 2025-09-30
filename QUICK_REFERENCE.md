# Quick Reference Guide - TNS Booking Uploader Bot

## 🚀 Quick Start

### 1. Run the Application
```bash
python3 main.py
```

### 2. Follow the Workflow
1. **Click "Open iCabbi Portal"** → Opens browser with Playwright
2. **Click "Select Booking File"** → Choose your Excel file
3. **Click "Start Processing Bookings"** → Automation begins

### 3. Watch the Magic ✨
- ✅ Fills driver name
- ✅ Fills pickup address (with autocomplete)
- ✅ Fills destination address (with autocomplete)
- ✅ Fills date and time
- ✅ Clicks Next automatically
- ⏸️ Leaves browser open for you to continue

---

## 📋 Excel File Format

### Required Columns

| Column | Format | Example | Notes |
|--------|--------|---------|-------|
| **Date** | dd/mm/yyyy or Excel date | 04/09/2025 | Any common format works |
| **Time** | HH:MM (24-hour) | 14:30 or 02:09 | Must be 24-hour format |
| **Driver** | First Last | MAJCEN Dennis | Full name with space |
| **From** | Short code or address | NME or "123 Main St" | See short codes below |
| **To** | Short code or address | CPS03O or "456 Park Ave" | See short codes below |
| **Reason** | Text | Business | Optional |
| **Shift** | Text/Number | 1001 | Optional |

### Example Excel Data

```
Date         | Time  | Driver         | From | To      | Reason | Shift
-------------|-------|----------------|------|---------|--------|------
04/09/2025   | 02:09 | MAJCEN Dennis  | NME  | CPS03O  |        | 1001
04/09/2025   | 14:30 | SMITH John     | FSS  | PKE     | Work   | 1002
05/09/2025   | 09:00 | DOE Jane       | BBH  | GWY     | Meeting| 1003
```

---

## 🗺️ Location Short Codes

### Common Depot Codes

| Code | Full Address |
|------|--------------|
| **NME** | Metro Trains North Melbourne Maintenance Depot |
| **CPS** | Metro Trains Calder Park Depot |
| **FSS** | Metro Trains Flinders St Station Taxi Pick Up |
| **PKE** | Metro Trains Pakenham East Depot Taxi Pick Up |
| **BBH** | Metro Trains Brighton Beach Sidings |
| **GWY** | Metro Trains Glen Waverley Station Taxi Pick Up |
| **EPP** | Metro Trains Epping Station/Cooper St Taxi Pick Up |
| **DNG** | Metro Trains Dandenong Station Taxi Pick Up |
| **CAR** | Metro Trains Carrum Station Taxi Pick Up |
| **RWD** | Metro Trains Ringwood Taxi Pick Up |

### Common Station Codes

| Code | Full Address |
|------|--------------|
| **AZC** | Anzac Station |
| **ARN** | Arden Station |
| **PKV** | Parkville Station |
| **HKN** | Hawksburn Station |
| **BBN** | Blackburn Station |
| **CTM** | Cheltenham Station |
| **GRN** | Greensborough Station |
| **HDB** | Heidelberg station |
| **ALM** | Alamein Station |
| **BOX** | Box Hill Station |

**📖 Full list**: See `metro-locations.json` for all 1500+ short codes

---

## 🎯 What Gets Automated

### Step 1: Driver Name ✅
- Navigates to create booking page
- Fills driver name from Excel
- Waits for Next button to enable
- Clicks Next

### Step 2: Address, Date, Time ✅
- Resolves short codes to full addresses
- Fills pickup address with autocomplete
- Fills destination address with autocomplete
- Fills date (converts to dd/mm/yyyy)
- Fills time (24-hour format)
- Waits for Next button to enable
- Clicks Next

### Step 3: Manual Continuation ⏸️
- Browser stays open
- You continue manually from here
- (Future: Will be automated)

---

## 🔍 Address Resolution

### How It Works

1. **Short Code** (e.g., "NME")
   - Looks up in `metro-locations.json`
   - Finds: "Metro Trains North Melbourne Maintenance Depot"
   - Uses full address in form

2. **Full Address** (e.g., "123 Main Street")
   - Detects spaces/commas
   - Uses as-is in form

3. **Unknown Code** (e.g., "XYZ")
   - Not found in metro-locations.json
   - Uses "XYZ" as-is
   - Logs warning

### Examples

```
Input: "NME"
Output: "Metro Trains North Melbourne Maintenance Depot"

Input: "123 Main Street, Melbourne"
Output: "123 Main Street, Melbourne"

Input: "UNKNOWN"
Output: "UNKNOWN" (with warning)
```

---

## 📊 Console Output

### Successful Run

```
INFO - Starting booking creation process...
INFO - Resolved 'NME' to 'Metro Trains North Melbourne Maintenance Depot'
INFO - Resolved 'CPS03O' to 'CPS Metro Trains Calder Park Depot'
INFO - Pickup: Metro Trains North Melbourne Maintenance Depot
INFO - Destination: CPS Metro Trains Calder Park Depot
INFO - Date: 04/09/2025, Time: 02:09
INFO - Filling Pickup Address: Metro Trains North Melbourne Maintenance Depot
INFO - Pickup Address selected from dropdown
INFO - Filling Destination Address: CPS Metro Trains Calder Park Depot
INFO - Destination Address selected from dropdown
INFO - Setting date: 04/09/2025, time: 02:09
INFO - Date and time filled successfully
INFO - Clicking Next button...
INFO - Successfully completed booking form step 2
```

### With Warnings

```
WARNING - No address found for code 'XYZ', using as-is
WARNING - Dropdown selection failed for Pickup Address: timeout
```

---

## ⚠️ Common Issues & Solutions

### Issue: "No address found for code 'XXX'"

**Cause**: Short code not in metro-locations.json

**Solution**:
- Check spelling of short code
- Use full address instead
- Add code to metro-locations.json if needed

---

### Issue: Dropdown doesn't appear

**Cause**: Address doesn't match portal database

**Solution**:
- Automation continues anyway
- Check if typed address is accepted
- Try a different address format

---

### Issue: Date field shows wrong date

**Cause**: Date format mismatch

**Solution**:
- Use dd/mm/yyyy format in Excel
- Ensure date is valid
- Check date is not in the past

---

### Issue: Time shows "ASAP" instead of time

**Cause**: Time field not filled properly

**Solution**:
- Use HH:MM format (24-hour)
- Ensure time is not empty in Excel
- Check time is valid (00:00 to 23:59)

---

## 🧪 Testing

### Run All Tests
```bash
python3 run_tests.py
```

### Expected Output
```
================================================== 32 passed in 0.41s ==================================================
```

---

## 📁 Important Files

| File | Purpose |
|------|---------|
| `main.py` | Start the application |
| `metro-locations.json` | Short code to address mapping |
| `src/web/automation.py` | Web automation logic |
| `src/excel/processor.py` | Excel file processing |
| `src/gui/main_window.py` | GUI interface |
| `logs/tns_uploader_*.log` | Application logs |

---

## 🎨 Button States

### "Open iCabbi Portal"
- **Enabled**: Always
- **Action**: Opens browser with Playwright
- **Result**: Browser stays open

### "Select Booking File"
- **Enabled**: Always
- **Action**: Opens file dialog
- **Result**: Processes Excel file, enables next button

### "Start Processing Bookings"
- **Disabled**: Until file is selected *(gray appearance)*
- **Enabled**: After valid file is selected
- **Action**: Starts automation
- **Result**: Fills form automatically

### "Clear Browser State"
- **Enabled**: Always
- **Action**: Clears saved login state
- **Result**: Next portal open requires login

---

## 🔄 Workflow Diagram

```
┌─────────────────────────────────────────────────────────┐
│ 1. Open iCabbi Portal                                   │
│    └─> Browser opens with Playwright                   │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ 2. Select Booking File                                  │
│    └─> Choose Excel file                               │
│    └─> Validates columns and data                      │
│    └─> Enables "Start Processing" button               │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ 3. Start Processing Bookings                            │
│    └─> Navigates to create page                        │
│    └─> Fills driver name → Next                        │
│    └─> Resolves addresses from short codes             │
│    └─> Fills pickup address (autocomplete)             │
│    └─> Fills destination address (autocomplete)        │
│    └─> Fills date and time                             │
│    └─> Clicks Next                                      │
│    └─> Browser stays open for manual continuation      │
└─────────────────────────────────────────────────────────┘
```

---

## 💡 Pro Tips

1. **Keep browser open**: Don't close the browser between steps
2. **Use short codes**: Faster and more accurate than typing addresses
3. **Check logs**: Look in `logs/` folder for detailed information
4. **Test with one booking**: Start with a single row to verify
5. **Stay logged in**: Browser state is saved between sessions
6. **24-hour time**: Always use 24-hour format (14:30, not 2:30 PM)

---

## 📞 Need Help?

1. **Check logs**: `logs/tns_uploader_YYYYMMDD.log`
2. **Run tests**: `python3 run_tests.py`
3. **Read docs**: 
   - `ADDRESS_DATE_TIME_AUTOMATION.md` - Detailed guide
   - `IMPLEMENTATION_SUMMARY.md` - Technical details
   - `BOOKING_AUTOMATION_FIX.md` - Previous fixes

---

## ✅ Checklist Before Running

- [ ] Excel file has all required columns
- [ ] Date format is correct (dd/mm/yyyy)
- [ ] Time format is 24-hour (HH:MM)
- [ ] Driver names are complete (First Last)
- [ ] Short codes are valid or full addresses used
- [ ] Browser is not already open from previous run
- [ ] Internet connection is stable

---

## 🎉 Success Indicators

✅ **Console shows**: "Successfully completed booking form step 2"
✅ **Browser shows**: Next page of booking form
✅ **No errors**: No red ERROR messages in console
✅ **Fields filled**: All address, date, time fields populated
✅ **Next clicked**: Automatically moved to next step

**You're ready to continue the booking process manually!** 🚀
