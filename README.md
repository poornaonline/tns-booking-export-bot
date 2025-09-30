# TNS Booking Uploader Bot

A Python desktop application that automates the process of uploading booking data from Excel files to the iCabbi web portal using Playwright for web automation.

## Features

- **Cross-Platform Compatibility**: Runs on both macOS and Windows
- **User-Friendly GUI**: Simple interface with two main buttons
- **Excel File Processing**: Parses Excel files with booking data
- **Web Browser Integration**: Opens iCabbi portal in Chrome or Edge browser (never Safari)
- **Data Validation**: Validates Excel file format and data integrity
- **Error Handling**: Comprehensive error handling and user feedback
- **Logging**: Built-in logging for debugging and monitoring

## Requirements

- Python 3.8 or higher
- **Chrome or Microsoft Edge browser** (required - Safari not supported)
- Internet connection for web automation
- Excel files (.xlsx or .xls format)

## Installation

1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install Playwright browsers:
   ```bash
   playwright install
   ```

## Usage

1. Run the application:
   ```bash
   python main.py
   ```
2. Use the "Open iCabbi Portal" button to open the web portal in Chrome or Edge
3. Use the "Start Booking Upload" button to select and process Excel files

## Excel File Format

The application expects Excel files with the following column structure:
```
Date | Time | Driver | From | To | Reason | Shift
```

Example data:
```
4/9/2025 | 02:09 | MAJCEN Dennis | NME | CPS03O | | 1001
4/9/2025 | 02:41 | JAMES Quin | FKND | KANS09 | | 211
```

## Project Structure

```
tns-booking-uploader-bot/
├── main.py                 # Main application entry point
├── src/
│   ├── __init__.py
│   ├── gui/
│   │   ├── __init__.py
│   │   └── main_window.py  # GUI implementation
│   ├── excel/
│   │   ├── __init__.py
│   │   └── processor.py    # Excel file processing
│   ├── web/
│   │   ├── __init__.py
│   │   └── automation.py   # Web automation logic
│   └── utils/
│       ├── __init__.py
│       ├── logger.py       # Logging configuration
│       └── validators.py   # Data validation utilities
├── tests/
│   ├── __init__.py
│   ├── test_excel.py
│   ├── test_gui.py
│   └── test_web.py
├── requirements.txt
└── README.md
```

## Development

### Running Tests
```bash
pytest tests/
```

### Code Formatting
```bash
black src/ tests/
```

### Linting
```bash
flake8 src/ tests/
```

## Building Executable

To create a standalone executable:
```bash
pyinstaller --onefile --windowed main.py
```

## License

This project is for internal use only.
