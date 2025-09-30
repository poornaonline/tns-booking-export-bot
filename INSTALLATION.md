# TNS Booking Uploader Bot - Installation Guide

## Prerequisites

- **Python 3.8 or higher** (recommended: Python 3.10+)
- **Operating System**: macOS or Windows
- **Chrome or Microsoft Edge browser** (required - Safari not supported)
- **Internet connection** for downloading dependencies and web automation

## Installation Steps

### 1. Install Python Dependencies

```bash
# Install required packages
pip install -r requirements.txt

# Install Playwright browsers (required for web automation)
playwright install
```

### 2. Verify Installation

```bash
# Run tests to verify everything is working
python3 run_tests.py

# Create sample data for testing
python3 create_sample_data.py
```

### 3. Run the Application

```bash
# Start the GUI application
python3 main.py
```

## Quick Start Guide

### Using the Application

1. **Launch the Application**
   ```bash
   python3 main.py
   ```

2. **Open iCabbi Portal**
   - Click the "Open iCabbi Portal" button
   - This will open Chrome or Edge browser and navigate to the iCabbi portal
   - **Important**: Safari is not supported and will not be used
   - If neither Chrome nor Edge is available, you'll get an error message
   - Log in to your account manually

3. **Upload Booking Data**
   - Click the "Start Booking Upload" button
   - Select an Excel file (.xlsx or .xls) with your booking data
   - The application will validate and process the file
   - View the results in the status area

### Excel File Format

Your Excel file must have these columns in this order:
```
Date | Time | Driver | From | To | Reason | Shift
```

**Example data:**
```
4/9/2025  | 02:09 | MAJCEN Dennis | NME    | CPS03O | | 1001
4/9/2025  | 02:41 | JAMES Quin    | FKND   | KANS09 | | 211
4/10/2025 | 08:15 | SMITH John    | CPS03O | NME    | Medical | 1002
```

**Notes:**
- Date formats supported: MM/DD/YYYY, DD/MM/YYYY, YYYY-MM-DD
- Time formats supported: HH:MM, HH:MM AM/PM
- Reason column is optional (can be empty)
- All other columns are required

## Troubleshooting

### Common Issues

1. **"Command not found: python"**
   - Use `python3` instead of `python`
   - Ensure Python is installed and in your PATH

2. **"No module named 'playwright'"**
   - Run: `pip install playwright`
   - Then: `playwright install`

3. **"Invalid Excel file" error**
   - Check that your file has the correct column structure
   - Ensure the file is not corrupted
   - Try saving the file in .xlsx format

4. **GUI doesn't appear (macOS)**
   - Ensure you're running from Terminal, not SSH
   - Check that tkinter is installed: `python3 -m tkinter`

5. **Browser doesn't open or opens Safari**
   - **Install Chrome**: https://www.google.com/chrome/
   - **Install Edge**: https://www.microsoft.com/edge/
   - The application will NOT use Safari - only Chrome or Edge
   - Try opening the URL manually: https://silvertopcorporate.business.icabbi.com/trips/all-trips

### Getting Help

1. **Check the logs**
   - Logs are saved in the `logs/` directory
   - Look for error messages and stack traces

2. **Run tests**
   ```bash
   python3 run_tests.py
   ```

3. **Validate your Excel file**
   - Use the sample file created by `create_sample_data.py` as a reference
   - Check column names and data formats

## Development Setup

If you want to modify or extend the application:

```bash
# Install development dependencies
pip install -r requirements.txt

# Install additional dev tools
pip install pytest black flake8

# Run tests
python3 run_tests.py

# Format code
black src/ tests/

# Check code style
flake8 src/ tests/
```

## Building Executable

To create a standalone executable:

```bash
# Install PyInstaller
pip install pyinstaller

# Build executable
pyinstaller --onefile --windowed main.py

# The executable will be in the dist/ directory
```

## System Requirements

### Minimum Requirements
- **RAM**: 512 MB
- **Storage**: 100 MB free space
- **Python**: 3.8+

### Recommended Requirements
- **RAM**: 2 GB
- **Storage**: 500 MB free space
- **Python**: 3.10+
- **Browser**: Chrome (preferred), Firefox, or Safari as fallback

## Security Notes

- This application opens web browsers and processes Excel files
- Only use trusted Excel files
- Ensure your system is up to date
- The application logs activities for debugging purposes

## Support

For technical support or questions:
1. Check this documentation
2. Review the logs in the `logs/` directory
3. Run the test suite to identify issues
4. Contact the development team with specific error messages
