#!/usr/bin/env python3
"""
TNS Booking Uploader Bot - Main Application Entry Point

A Python desktop application that automates the process of uploading booking data
from Excel files to the iCabbi web portal.

Author: TNS Development Team
Version: 1.0.0
"""

import sys
import traceback
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.utils.logger import get_logger
from src.gui.main_window import MainWindow

logger = get_logger()


def main():
    """Main entry point."""
    try:
        main_window = MainWindow()
        main_window.run()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
