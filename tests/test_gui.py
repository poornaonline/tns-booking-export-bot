#!/usr/bin/env python3
"""
Simplified GUI tests focusing on core business logic without complex mocking.
"""

import pytest
import sys
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestMainWindowComponents:
    """Test MainWindow components without GUI setup."""
    
    def test_component_imports(self):
        """Test that all required components can be imported."""
        from src.gui.main_window import MainWindow
        from src.excel.processor import ExcelProcessor
        from src.web.automation import WebAutomation
        
        # Test that classes exist and can be instantiated
        processor = ExcelProcessor()
        automation = WebAutomation()
        
        assert processor is not None
        assert automation is not None
        assert MainWindow.WINDOW_TITLE == "TNS Booking Uploader Bot"
    
    def test_excel_processor_integration(self):
        """Test Excel processor integration."""
        from src.excel.processor import ExcelProcessor
        
        processor = ExcelProcessor()
        
        # Test that processor has required methods
        assert hasattr(processor, 'process_file')
        assert hasattr(processor, 'get_sample_data_format')
        
        # Test sample data format
        sample_format = processor.get_sample_data_format()
        assert isinstance(sample_format, dict)  # Returns a dict, not a list
        assert len(sample_format) > 0
    
    def test_web_automation_integration(self):
        """Test web automation integration."""
        from src.web.automation import WebAutomation
        
        automation = WebAutomation()
        
        # Test that automation has required URLs
        assert automation.ICABBI_PORTAL_URL == "https://silvertopcorporate.business.icabbi.com/trips/all-trips"
        assert automation.ICABBI_CREATE_URL == "https://silvertopcorporate.business.icabbi.com/create-v2"
        
        # Test that automation has required methods
        assert hasattr(automation, 'open_portal_in_browser')
        assert hasattr(automation, 'start_booking_creation')
        assert hasattr(automation, 'close_browser')
        assert hasattr(automation, 'clear_browser_state')
        
        # Test browser state file path
        assert automation.browser_state_path.name == "browser_state.json"
    
    def test_persistent_context_methods(self):
        """Test persistent context methods."""
        from src.web.automation import WebAutomation

        automation = WebAutomation()

        # Test state management methods exist
        assert hasattr(automation, '_save_browser_state')
        assert hasattr(automation, '_load_browser_state')

        # Clear any existing state first
        automation.clear_browser_state()

        # Test that methods can be called without errors
        state = automation._load_browser_state()
        assert state is None  # Should be None when no state file exists

        # Test clear state (should not error)
        automation.clear_browser_state()
    
    def test_button_configuration(self):
        """Test button configuration constants."""
        from src.gui.main_window import MainWindow
        
        # Test that MainWindow has required constants
        assert hasattr(MainWindow, 'WINDOW_TITLE')
        assert MainWindow.WINDOW_TITLE == "TNS Booking Uploader Bot"


class TestWorkflowIntegration:
    """Test workflow integration without GUI."""
    
    def test_excel_to_web_data_flow(self):
        """Test data flow from Excel processing to web automation."""
        from src.excel.processor import ExcelProcessor
        from src.web.automation import WebAutomation
        
        processor = ExcelProcessor()
        automation = WebAutomation()
        
        # Test that processed data format is compatible with web automation
        sample_data = [
            {
                'is_valid': True,
                'Driver': 'Test Driver',
                'Date': '2024-01-01',
                'Time': '10:00',
                'From': 'Location A',
                'To': 'Location B',
                'Reason': 'Business',
                'Shift': 'Day'
            }
        ]
        
        # Test that web automation can handle this data format
        # (This would normally fail without browser, but we're testing the interface)
        result = automation.start_booking_creation(sample_data)
        assert isinstance(result, bool)  # Should return a boolean
    
    def test_error_handling(self):
        """Test error handling in components."""
        from src.excel.processor import ExcelProcessor
        from src.web.automation import WebAutomation
        
        processor = ExcelProcessor()
        automation = WebAutomation()
        
        # Test Excel processor with invalid file
        result = processor.process_file("nonexistent_file.xlsx")
        assert result.success == False
        assert result.error_message is not None
        
        # Test web automation with empty data
        result = automation.start_booking_creation([])
        assert result == False
        
        # Test web automation with invalid data
        invalid_data = [{'is_valid': False, 'Driver': 'Test'}]
        result = automation.start_booking_creation(invalid_data)
        assert result == False


if __name__ == "__main__":
    pytest.main([__file__])
