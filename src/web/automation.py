"""
Web automation module for TNS Booking Uploader Bot.

This module provides web automation functionality using Playwright for browser control
and persistent authentication state management. It handles opening the iCabbi portal
and automating the booking creation process.
"""

import time
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..utils.logger import get_logger

logger = get_logger()


class WebAutomation:
    """
    Handles web automation using Playwright with persistent browser context.

    This class manages browser automation for the iCabbi portal, including:
    - Opening the portal with Playwright
    - Maintaining persistent authentication state
    - Automating booking creation forms
    - Managing browser lifecycle and cleanup
    """

    ICABBI_PORTAL_URL = "https://silvertopcorporate.business.icabbi.com/trips/all-trips"
    ICABBI_CREATE_URL = "https://silvertopcorporate.business.icabbi.com/create-v2"
    BROWSER_STATE_FILE = "browser_state.json"
    USER_DATA_DIR = "browser_data"
    METRO_LOCATIONS_FILE = "metro-locations.json"

    def __init__(self):
        """Initialize WebAutomation with shared browser context."""
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.browser_state_path = Path(self.BROWSER_STATE_FILE)
        self.user_data_dir = Path(self.USER_DATA_DIR)
        self.metro_locations = self._load_metro_locations()

        # Create user data directory if it doesn't exist
        self.user_data_dir.mkdir(exist_ok=True)

    def _save_browser_state(self):
        """Save browser authentication state to file."""
        try:
            if self.context:
                state = self.context.storage_state()
                with open(self.browser_state_path, 'w') as f:
                    json.dump(state, f, indent=2)
                logger.info(f"Browser state saved to {self.browser_state_path}")
        except Exception as e:
            logger.warning(f"Failed to save browser state: {e}")

    def _load_browser_state(self) -> Optional[Dict]:
        """Load browser authentication state from file."""
        try:
            if self.browser_state_path.exists():
                with open(self.browser_state_path, 'r') as f:
                    state = json.load(f)
                logger.info(f"Browser state loaded from {self.browser_state_path}")
                return state
        except Exception as e:
            logger.warning(f"Failed to load browser state: {e}")
            # Remove corrupted state file
            self._remove_corrupted_state_file()
        return None

    def _remove_corrupted_state_file(self):
        """Remove corrupted browser state file."""
        try:
            self.browser_state_path.unlink()
        except Exception:
            pass  # Ignore errors when removing corrupted file

    def _load_metro_locations(self) -> List[Dict]:
        """Load metro locations from JSON file."""
        try:
            metro_file = Path(self.METRO_LOCATIONS_FILE)
            if metro_file.exists():
                with open(metro_file, 'r') as f:
                    locations = json.load(f)
                logger.info(f"Loaded {len(locations)} metro locations")
                return locations
        except Exception as e:
            logger.warning(f"Failed to load metro locations: {e}")
        return []

    def _resolve_address(self, location_code: str) -> str:
        """
        Resolve location code to full address using metro-locations.json.

        Args:
            location_code: Short code or full address from Excel

        Returns:
            Full address string
        """
        # If it looks like a full address (contains spaces or commas), return as-is
        if ' ' in location_code or ',' in location_code:
            return location_code

        # Convert to uppercase for matching
        code_upper = location_code.strip().upper()

        # First try exact match
        for location in self.metro_locations:
            if code_upper in [sc.upper() for sc in location.get('shortCode', [])]:
                address = location.get('address', '')
                logger.info(f"Resolved '{location_code}' to '{address}'")
                return address

        # If no exact match, try partial match (code starts with the input)
        # This helps with codes like "NME" matching "NMED", "NMEC", etc.
        for location in self.metro_locations:
            for sc in location.get('shortCode', []):
                if sc.upper().startswith(code_upper) and len(code_upper) >= 3:
                    address = location.get('address', '')
                    logger.info(f"Resolved '{location_code}' to '{address}' (partial match with '{sc}')")
                    return address

        # If no match found, return original code
        logger.warning(f"No address found for code '{location_code}', using as-is")
        return location_code


    def open_portal_in_browser(self) -> bool:
        """Open the iCabbi portal using Playwright with persistent context."""
        try:
            # Import Playwright here to avoid import errors if not installed
            try:
                from playwright.sync_api import sync_playwright
            except ImportError:
                logger.error("Playwright not installed. Please install with: pip install playwright")
                return False

            # Initialize Playwright if not already done
            if not self.playwright:
                self.playwright = sync_playwright().start()

                # Try to use persistent context first (best for session persistence)
                try:
                    logger.info("Launching browser with persistent context for automatic login")
                    self.context = self.playwright.chromium.launch_persistent_context(
                        user_data_dir=str(self.user_data_dir),
                        headless=False,
                        args=['--disable-blink-features=AutomationControlled'],  # Hide automation
                        viewport={'width': 1280, 'height': 720}
                    )
                    self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
                    logger.info("Using persistent browser context - login session will be saved")

                except Exception as e:
                    logger.warning(f"Could not use persistent context: {e}")
                    logger.info("Falling back to regular browser with state file")

                    # Fallback to regular browser with state file
                    self.browser = self.playwright.chromium.launch(headless=False)

                    # Load saved browser state if available
                    saved_state = self._load_browser_state()
                    if saved_state:
                        logger.info("Using saved browser authentication state")
                        self.context = self.browser.new_context(storage_state=saved_state)
                    else:
                        logger.info("Creating new browser context")
                        self.context = self.browser.new_context()

                    self.page = self.context.new_page()

            # Navigate to portal
            logger.info(f"Opening iCabbi portal: {self.ICABBI_PORTAL_URL}")
            self.page.goto(self.ICABBI_PORTAL_URL)
            self.page.wait_for_load_state('networkidle')

            # Save browser state after successful navigation
            self._save_browser_state()

            logger.info("iCabbi portal opened successfully")
            return True

        except Exception as e:
            logger.error(f"Error opening portal: {str(e)}")
            return False

    def start_booking_creation(self, processed_data: List[Dict[str, Any]]) -> bool:
        """Start the booking creation process with processed Excel data using existing browser."""
        try:
            # Check if browser is already initialized
            if not self.page:
                logger.error("Browser not initialized. Please open the iCabbi portal first.")
                return False

            # Filter valid rows only
            valid_bookings = [row for row in processed_data if row.get('is_valid', False)]

            if not valid_bookings:
                logger.error("No valid bookings found in processed data")
                return False

            logger.info(f"Starting booking creation for {len(valid_bookings)} valid bookings")

            # Navigate to create booking page in the existing tab
            logger.info(f"Navigating to: {self.ICABBI_CREATE_URL}")
            self.page.goto(self.ICABBI_CREATE_URL)
            self.page.wait_for_load_state('networkidle')

            # Process first booking as example
            first_booking = valid_bookings[0]
            driver_name = str(first_booking.get('Driver', '')).strip()

            if not driver_name or driver_name.lower() == 'nan':
                logger.error("No valid driver name found in first booking")
                return False

            logger.info(f"Filling driver name: {driver_name}")

            # Wait for the name input field to be visible
            # The field has placeholder "Enter name" and is an autocomplete input
            name_field = self.page.wait_for_selector('input[placeholder="Enter name"]', timeout=10000)

            # Click the field to focus it
            name_field.click()

            # Clear any existing value and type the driver name
            name_field.fill('')
            name_field.type(driver_name, delay=100)  # Type with delay to trigger autocomplete

            # Wait for the form to process the input
            time.sleep(1)

            # Check if mobile number exists and fill it
            mobile_number = first_booking.get('Mobile', '')
            if mobile_number and str(mobile_number).strip() and str(mobile_number).lower() != 'nan':
                # Clean the mobile number - remove all spaces
                mobile_clean = str(mobile_number).replace(' ', '').strip()

                # Remove +61 prefix and convert to local format (0...)
                if mobile_clean.startswith('+61'):
                    mobile_clean = '0' + mobile_clean[3:]  # Replace +61 with 0
                    logger.info(f"Converted international format to local: {mobile_number} → {mobile_clean}")
                elif mobile_clean.startswith('61') and len(mobile_clean) >= 11:
                    # Handle 61412345678 format (without +)
                    mobile_clean = '0' + mobile_clean[2:]
                    logger.info(f"Converted international format to local: {mobile_number} → {mobile_clean}")
                else:
                    logger.info(f"Mobile number found: {mobile_number} (cleaned: {mobile_clean})")

                try:
                    # Find the mobile input field by placeholder text (IDs change dynamically)
                    mobile_field = self.page.wait_for_selector('input[placeholder="Enter phone number"]', timeout=5000)

                    # Click and fill the mobile number
                    mobile_field.click()
                    mobile_field.fill('')
                    mobile_field.type(mobile_clean, delay=50)

                    logger.info(f"Successfully filled mobile number: {mobile_clean}")
                    time.sleep(0.5)  # Brief wait after filling

                except Exception as e:
                    logger.warning(f"Could not fill mobile number (field may not exist): {e}")
                    # Continue anyway - mobile field is optional
            else:
                logger.info("No mobile number found in booking data")

            # Wait for the Next button to become enabled (it starts disabled)
            logger.info("Waiting for Next button to become enabled...")
            next_button = self.page.wait_for_selector('button:has-text("Next"):not([disabled])', timeout=10000)

            # Click the Next button
            next_button.click()

            logger.info("Successfully filled driver name and clicked Next button")

            # Wait for the next page to load (address/date/time form)
            time.sleep(2)

            # Now fill in the pickup address, destination, date, and time
            logger.info("Filling pickup address, destination, date, and time...")

            # Get address data from booking
            from_location = str(first_booking.get('From', '')).strip()
            to_location = str(first_booking.get('To', '')).strip()
            booking_date = first_booking.get('Date', '')
            booking_time = first_booking.get('Time', '')

            # Resolve addresses
            pickup_address = self._resolve_address(from_location)
            destination_address = self._resolve_address(to_location)

            logger.info(f"Pickup: {pickup_address}")
            logger.info(f"Destination: {destination_address}")
            logger.info(f"Date: {booking_date}, Time: {booking_time}")

            # Fill pickup address
            self._fill_address_field(pickup_address, is_pickup=True)

            # Fill destination address
            self._fill_address_field(destination_address, is_pickup=False)

            # Fill date and time
            self._fill_date_time(booking_date, booking_time)

            # Click Next button to proceed to step 3
            logger.info("Clicking Next button to proceed to step 3...")
            next_button = self.page.wait_for_selector('button:has-text("Next"):not([disabled])', timeout=10000)
            next_button.click()

            logger.info("Successfully completed booking form step 2 (Address/Date/Time)")

            # Step 3: Intermediate page - just click Next
            logger.info("Waiting for step 3 (intermediate page) to load...")
            time.sleep(3)  # Wait 3 seconds for page to fully load

            logger.info("Step 3 page loaded, clicking Next button...")
            try:
                next_button = self.page.wait_for_selector('button:has-text("Next"):not([disabled])', timeout=10000)
                next_button.click()
                logger.info("Successfully clicked Next button on step 3")
                time.sleep(2)  # Wait for next page to load
            except Exception as e:
                logger.error(f"Error clicking Next button on step 3: {e}")
                raise

            logger.info("Successfully completed step 3 (intermediate page)")

            # Step 4: Fill final booking form fields
            logger.info("Waiting for step 4 (final booking form) to load...")
            time.sleep(3)  # Wait 3 seconds for page to fully load

            logger.info("Step 4 page loaded, filling booking details...")

            # Fill "Ordered By" field with "Metro" (IDs change dynamically, use section title)
            try:
                logger.info("Filling 'Ordered By' field with 'Metro'...")

                # Find the section with title "Ordered By" and get its input field
                # Look for h5 with text "Ordered By", then find the input in the same row
                ordered_by_section = self.page.locator('h5.section-title:has-text("Ordered By")')

                # Get the parent row and find the input field within it
                ordered_by_row = ordered_by_section.locator('..').locator('..')
                ordered_by_input = ordered_by_row.locator('input[type="text"]').first

                # Wait for the field to be visible
                ordered_by_input.wait_for(state='visible', timeout=10000)

                # Click and fill the field
                ordered_by_input.click()
                ordered_by_input.fill('')
                ordered_by_input.type('Metro', delay=100)

                logger.info("Successfully filled 'Metro' in Ordered By field")
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error filling Ordered By field: {e}")
                raise

            # Step 5: Click "Book now" button to complete the booking
            logger.info("Clicking 'Book now' button to complete booking...")
            try:
                # Wait for the button to be enabled (not disabled)
                book_button = self.page.wait_for_selector('button:has-text("Book now"):not([disabled])', timeout=10000)
                book_button.click()
                logger.info("Successfully clicked 'Book now' button")
                time.sleep(2)  # Wait for booking confirmation
            except Exception as e:
                logger.error(f"Error clicking 'Book now' button: {e}")
                raise

            logger.info("Booking creation completed successfully!")
            return True

        except Exception as e:
            logger.error(f"Error during booking creation: {e}")
            return False

    def _fill_address_field(self, address: str, is_pickup: bool = True):
        """
        Fill address field (pickup or destination) and select from dropdown.

        Args:
            address: The address to fill
            is_pickup: True for pickup address, False for destination
        """
        try:
            field_name = "Pickup Address" if is_pickup else "Destination Address"
            logger.info(f"Filling {field_name}: {address}")

            # The multiselect component has a hidden input field
            # We need to click on the multiselect container first to make it visible

            # Find all multiselect containers
            multiselects = self.page.query_selector_all('.multiselect.address-select')

            # First multiselect is pickup, second is destination
            multiselect_index = 0 if is_pickup else 1

            if multiselect_index >= len(multiselects):
                raise Exception(f"Could not find multiselect for {field_name}")

            multiselect = multiselects[multiselect_index]

            # Click on the multiselect to activate it
            multiselect.click()
            time.sleep(0.5)

            # Now find the input field within this multiselect
            # The input becomes visible after clicking
            address_field = multiselect.query_selector('input.multiselect__input')

            if not address_field:
                raise Exception(f"Could not find input field for {field_name}")

            # Type the address with delay to trigger autocomplete
            address_field.fill('')
            address_field.type(address, delay=100)

            # Wait for dropdown to appear and populate
            time.sleep(2)

            # Wait for dropdown options to appear
            # The dropdown uses multiselect__option class
            try:
                # Wait for dropdown options to be visible within this multiselect
                # Use the multiselect's content wrapper to ensure we're looking at the right dropdown
                content_wrapper = multiselect.query_selector('.multiselect__content-wrapper')
                if content_wrapper:
                    # Wait a bit more for options to populate
                    time.sleep(1)

                    # Find options within this specific multiselect
                    options = content_wrapper.query_selector_all('.multiselect__option:not(.multiselect__option--disabled)')

                    if options and len(options) > 0:
                        # Click the first option
                        options[0].click()
                        logger.info(f"{field_name} selected from dropdown")
                        time.sleep(0.5)
                    else:
                        logger.warning(f"No dropdown options found for {field_name}, continuing...")
                else:
                    logger.warning(f"No dropdown content wrapper found for {field_name}")
            except Exception as e:
                logger.warning(f"Dropdown selection failed for {field_name}: {e}")
                # Continue anyway - the typed address might be accepted

            time.sleep(1)

        except Exception as e:
            logger.error(f"Error filling {field_name}: {e}")
            raise

    def _fill_date_time(self, booking_date, booking_time):
        """
        Fill date and time fields using JavaScript to avoid interfering with address fields.

        Args:
            booking_date: Date from Excel (can be datetime object or string)
            booking_time: Time from Excel (can be datetime object or string)
        """
        try:
            # Convert date to datetime object for parsing
            if isinstance(booking_date, datetime):
                dt = booking_date
            else:
                # Try to parse the date
                try:
                    if isinstance(booking_date, str):
                        # Try parsing common formats
                        for fmt in ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y']:
                            try:
                                dt = datetime.strptime(booking_date, fmt)
                                break
                            except:
                                continue
                        else:
                            # If all parsing fails, try pandas Timestamp
                            import pandas as pd
                            dt = pd.to_datetime(booking_date)
                    else:
                        import pandas as pd
                        dt = pd.to_datetime(booking_date)
                except Exception as e:
                    logger.error(f"Could not parse date: {booking_date}, error: {e}")
                    raise

            # Format date as dd/mm/yyyy for display
            date_str = dt.strftime('%d/%m/%Y')

            # Convert time to string format
            if isinstance(booking_time, datetime):
                time_str = booking_time.strftime('%H:%M')
            else:
                time_str = str(booking_time).strip()

            logger.info(f"Setting date: {date_str}, time: {time_str}")

            # Parse the date components for Vue.js date picker
            day = dt.day
            month = dt.month
            year = dt.year

            # Set the date field using Vue.js component updates
            js_set_date = f"""
            (() => {{
                // Find the date input by section header (avoids multiselect inputs)
                let dateInput = null;
                const headers = document.querySelectorAll('h5.section-title');
                for (const header of headers) {{
                    if (header.textContent.includes('Date')) {{
                        const parent = header.closest('.col');
                        if (parent) {{
                            dateInput = parent.querySelector('input[readonly][type="text"]');
                            if (dateInput) break;
                        }}
                    }}
                }}

                if (!dateInput) {{
                    return {{ success: false, error: 'Date input not found' }};
                }}

                // Date formats to try
                const isoDate = '{year}-{month:02d}-{day:02d}';
                const displayDate = '{date_str}';

                // Update Vue.js component data model
                let element = dateInput;
                let level = 0;

                while (element && level < 10) {{
                    if (element.__vue__) {{
                        const vue = element.__vue__;

                        // Try setting Vue data properties
                        if (vue.$data) {{
                            for (const key in vue.$data) {{
                                if (key.toLowerCase().includes('date') ||
                                    key.toLowerCase().includes('value') ||
                                    key.toLowerCase().includes('picker')) {{
                                    vue.$data[key] = isoDate;
                                    vue.$data[key] = displayDate;
                                }}
                            }}
                        }}

                        // Try direct Vue properties
                        const props = ['value', 'internalValue', 'lazyValue', 'date', 'selectedDate', 'pickerDate'];
                        for (const prop of props) {{
                            if (vue.hasOwnProperty(prop)) {{
                                vue[prop] = isoDate;
                                vue[prop] = displayDate;
                            }}
                        }}

                        // Emit Vue events
                        if (vue.$emit) {{
                            vue.$emit('input', isoDate);
                            vue.$emit('input', displayDate);
                        }}

                        // Call Vue methods if available
                        if (typeof vue.setValue === 'function') {{
                            vue.setValue(isoDate);
                        }}
                        if (typeof vue.updateValue === 'function') {{
                            vue.updateValue(isoDate);
                        }}

                        // Force Vue to update
                        if (vue.$forceUpdate) {{
                            vue.$forceUpdate();
                        }}
                    }}
                    element = element.parentElement;
                    level++;
                }}

                // Set input value directly and trigger DOM events
                dateInput.removeAttribute('readonly');
                dateInput.value = displayDate;
                dateInput.dispatchEvent(new Event('input', {{ bubbles: true, cancelable: true }}));
                dateInput.dispatchEvent(new Event('change', {{ bubbles: true, cancelable: true }}));
                dateInput.dispatchEvent(new Event('blur', {{ bubbles: true, cancelable: true }}));
                dateInput.setAttribute('readonly', 'readonly');

                return {{ success: true, value: dateInput.value }};
            }})()
            """

            date_result = self.page.evaluate(js_set_date)
            if date_result and date_result.get('success'):
                logger.info(f"Date set to {date_str}")
            else:
                error = date_result.get('error', 'Unknown error') if date_result else 'No result'
                logger.warning(f"Could not set date: {error}")

            time.sleep(2)  # Wait for Vue to process updates

            # Set the time field
            js_set_time = f"""
            (() => {{
                // Find the time input by section header
                let timeInput = null;
                const headers = document.querySelectorAll('h5.section-title');
                for (const header of headers) {{
                    if (header.textContent.includes('Time')) {{
                        const parent = header.closest('.col');
                        if (parent) {{
                            timeInput = parent.querySelector('input[data-maska]');
                            if (timeInput) break;
                        }}
                    }}
                }}

                if (!timeInput) {{
                    return {{ success: false, error: 'Time input not found' }};
                }}

                // Set the time value
                timeInput.value = '';
                timeInput.value = '{time_str}';

                // Trigger events for validation
                timeInput.dispatchEvent(new Event('input', {{ bubbles: true, cancelable: true }}));
                timeInput.dispatchEvent(new Event('change', {{ bubbles: true, cancelable: true }}));
                timeInput.dispatchEvent(new Event('blur', {{ bubbles: true, cancelable: true }}));

                return {{ success: true, value: timeInput.value }};
            }})()
            """

            time_result = self.page.evaluate(js_set_time)
            if time_result and time_result.get('success'):
                logger.info(f"Time set to {time_str}")
            else:
                error = time_result.get('error', 'Unknown error') if time_result else 'No result'
                logger.warning(f"Could not set time: {error}")

            logger.info("Date and time filled successfully")
            time.sleep(2)  # Wait for form validation

        except Exception as e:
            logger.error(f"Error filling date/time: {e}")
            raise

    def close_browser(self):
        """Close the browser and cleanup resources."""
        try:
            # Save browser state before closing (for non-persistent context)
            if self.browser:
                self._save_browser_state()

            # Close browser or context
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()

            # Reset all browser-related attributes
            self.playwright = None
            self.browser = None
            self.context = None
            self.page = None
            logger.info("Browser closed and resources cleaned up (session saved)")
        except Exception as e:
            logger.error(f"Error closing browser: {e}")

    def clear_browser_state(self):
        """Clear saved browser authentication state."""
        try:
            if self.browser_state_path.exists():
                self.browser_state_path.unlink()
                logger.info("Browser state cleared")
        except Exception as e:
            logger.error(f"Error clearing browser state: {e}")




