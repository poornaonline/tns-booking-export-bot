"""
Logging configuration for TNS Booking Uploader Bot.
"""

import logging
import logging.handlers
from datetime import datetime
from pathlib import Path

# Global logger instance
_logger = None


def _setup_logger():
    """Set up the logger with file and console handlers."""
    global _logger

    if _logger is not None:
        return _logger

    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Create logger
    _logger = logging.getLogger("TNSBookingUploader")
    _logger.setLevel(logging.DEBUG)

    # Prevent duplicate handlers
    if _logger.handlers:
        return _logger

    # Create formatters
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # File handler with rotation
    log_filename = logs_dir / f"tns_uploader_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_filename,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)

    # Add handlers to logger
    _logger.addHandler(file_handler)
    _logger.addHandler(console_handler)

    return _logger


def get_logger():
    """Get the application logger."""
    return _setup_logger()
