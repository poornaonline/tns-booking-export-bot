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

        # UI callback for keeping interface responsive
        self.ui_callback = None

    def set_ui_callback(self, callback):
        """Set a callback function to be called periodically to keep UI responsive.

        Args:
            callback: Function that returns True if processing should stop, False otherwise
        """
        self.ui_callback = callback

    def _call_ui_callback(self):
        """Call the UI callback if set, and check if we should stop."""
        if self.ui_callback:
            try:
                should_stop = self.ui_callback()
                if should_stop:
                    logger.info("Stop requested via UI callback")
                    return True
            except Exception as e:
                logger.error(f"Error in UI callback: {e}")
        return False

    def _sleep_with_ui_update(self, seconds):
        """Sleep while keeping UI responsive by calling callback periodically.

        Args:
            seconds: Number of seconds to sleep
        """
        # Break sleep into smaller chunks to keep UI responsive
        chunk_size = 0.1  # 100ms chunks
        chunks = int(seconds / chunk_size)
        remainder = seconds % chunk_size

        for _ in range(chunks):
            time.sleep(chunk_size)
            if self._call_ui_callback():
                # Stop requested
                raise Exception("Processing stopped by user")

        if remainder > 0:
            time.sleep(remainder)
            if self._call_ui_callback():
                raise Exception("Processing stopped by user")

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

    def create_single_booking(self, booking: Dict[str, Any]) -> bool:
        """
        Create a single booking.

        Args:
            booking: Dictionary containing booking data

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if browser is initialized
            if not self.page:
                logger.error("Browser not initialized")
                return False

            # Navigate to create booking page
            logger.info(f"Navigating to: {self.ICABBI_CREATE_URL}")
            self.page.goto(self.ICABBI_CREATE_URL)
            self.page.wait_for_load_state('networkidle')

            # Extract booking data
            driver_name = str(booking.get('Driver', '')).strip()

            if not driver_name or driver_name.lower() == 'nan':
                logger.error("No valid driver name found in booking")
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
            self._sleep_with_ui_update(1)

            # Dismiss any dropdown that may have appeared by clicking outside
            # Sometimes typing a name triggers an autocomplete dropdown
            try:
                logger.info("Checking for autocomplete dropdown to dismiss...")
                # Click on a neutral area (the form title) to dismiss any dropdown
                form_title = self.page.query_selector('.booking-form-title')
                if form_title:
                    form_title.click()
                    logger.info("Clicked outside to dismiss any dropdown")
                    self._sleep_with_ui_update(0.5)
            except Exception as e:
                logger.debug(f"No dropdown to dismiss or error clicking outside: {e}")

            # Check if mobile number exists and fill it
            mobile_number = booking.get('Mobile', '')
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
                    self._sleep_with_ui_update(0.5)  # Brief wait after filling

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
            self._sleep_with_ui_update(2)

            # Now fill in the pickup address, destination, date, and time
            logger.info("Filling pickup address, destination, date, and time...")

            # Get address data from booking
            from_location = str(booking.get('From', '')).strip()
            to_location = str(booking.get('To', '')).strip()
            booking_date = booking.get('Date', '')
            booking_time = booking.get('Time', '')

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
            self._sleep_with_ui_update(3)  # Wait 3 seconds for page to fully load

            logger.info("Step 3 page loaded, clicking Next button...")
            try:
                next_button = self.page.wait_for_selector('button:has-text("Next"):not([disabled])', timeout=10000)
                next_button.click()
                logger.info("Successfully clicked Next button on step 3")
                self._sleep_with_ui_update(2)  # Wait for next page to load
            except Exception as e:
                logger.error(f"Error clicking Next button on step 3: {e}")
                raise

            logger.info("Successfully completed step 3 (intermediate page)")

            # Step 4: Fill final booking form fields
            logger.info("Waiting for step 4 (final booking form) to load...")
            self._sleep_with_ui_update(3)  # Wait 3 seconds for page to fully load

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
                self._sleep_with_ui_update(1)
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

                # Wait for booking to complete (5 seconds minimum)
                logger.info("Waiting for booking to complete...")
                self._sleep_with_ui_update(5)

                # Check if booking was successful by looking for success indicators
                # (You can add more specific checks here if needed)
                logger.info("Booking completion wait finished")

            except Exception as e:
                logger.error(f"Error clicking 'Book now' button: {e}")
                raise

            logger.info("Booking creation completed successfully!")
            return True

        except Exception as e:
            logger.error(f"Error during booking creation: {e}")
            return False

    def start_booking_creation(self, processed_data: List[Dict[str, Any]]) -> bool:
        """
        Start the booking creation process with processed Excel data.
        This method processes only the first booking for backward compatibility.

        Args:
            processed_data: List of booking dictionaries

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Filter valid rows only
            valid_bookings = [row for row in processed_data if row.get('is_valid', False)]

            if not valid_bookings:
                logger.error("No valid bookings found in processed data")
                return False

            logger.info(f"Processing first booking out of {len(valid_bookings)} valid bookings")

            # Process first booking
            return self.create_single_booking(valid_bookings[0])

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
            self._sleep_with_ui_update(0.5)

            # Now find the input field within this multiselect
            # The input becomes visible after clicking
            address_field = multiselect.query_selector('input.multiselect__input')

            if not address_field:
                raise Exception(f"Could not find input field for {field_name}")

            # Type the address with delay to trigger autocomplete
            address_field.fill('')
            address_field.type(address, delay=100)

            # Wait for dropdown to appear and populate
            self._sleep_with_ui_update(2)

            # Wait for dropdown options to appear
            # The dropdown uses multiselect__option class
            try:
                # Wait for dropdown options to be visible within this multiselect
                # Use the multiselect's content wrapper to ensure we're looking at the right dropdown
                content_wrapper = multiselect.query_selector('.multiselect__content-wrapper')
                if content_wrapper:
                    # Wait a bit more for options to populate
                    self._sleep_with_ui_update(1)

                    # Find options within this specific multiselect
                    options = content_wrapper.query_selector_all('.multiselect__option:not(.multiselect__option--disabled)')

                    if options and len(options) > 0:
                        logger.info(f"Found {len(options)} dropdown options for {field_name}")

                        # Find the best matching option
                        best_match = None
                        best_score = 0

                        # Get the search text (what we typed)
                        search_text = address.lower().strip()

                        for i, option in enumerate(options):
                            option_text = option.text_content().strip()
                            logger.info(f"  Option {i+1}: {option_text}")

                            # Calculate match score
                            option_lower = option_text.lower()
                            score = 0

                            # Exact match gets highest score
                            if option_lower == search_text:
                                score = 1000
                            # Starts with search text
                            elif option_lower.startswith(search_text):
                                score = 500
                            # Contains search text
                            elif search_text in option_lower:
                                score = 250
                            # Contains all words from search text
                            else:
                                search_words = search_text.split()
                                matching_words = sum(1 for word in search_words if word in option_lower)
                                score = matching_words * 50

                            # Prefer shorter matches (more specific)
                            if score > 0:
                                score -= len(option_text) * 0.1

                            logger.debug(f"    Score: {score}")

                            if score > best_score:
                                best_score = score
                                best_match = (i, option, option_text)

                        if best_match:
                            idx, option, option_text = best_match
                            logger.info(f"✅ Best match (score {best_score:.1f}): Option {idx+1} - {option_text}")
                            option.click()
                            logger.info(f"{field_name} selected from dropdown")
                            self._sleep_with_ui_update(0.5)
                        else:
                            # No good match, use first option as fallback
                            logger.warning(f"No good match found, using first option as fallback")
                            options[0].click()
                            logger.info(f"{field_name} selected from dropdown (first option)")
                            self._sleep_with_ui_update(0.5)
                    else:
                        logger.warning(f"No dropdown options found for {field_name}, continuing...")
                else:
                    logger.warning(f"No dropdown content wrapper found for {field_name}")
            except Exception as e:
                logger.warning(f"Dropdown selection failed for {field_name}: {e}")
                # Continue anyway - the typed address might be accepted

            self._sleep_with_ui_update(1)

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
            logger.info("="*70)
            logger.info("DATE/TIME CONVERSION AND SETTING - DETAILED LOGGING")
            logger.info("="*70)

            # Log raw input
            logger.info(f"📥 RAW INPUT from Excel:")
            logger.info(f"   Date type: {type(booking_date).__name__}")
            logger.info(f"   Date value: {booking_date}")
            logger.info(f"   Time type: {type(booking_time).__name__}")
            logger.info(f"   Time value: {booking_time}")

            # Convert date to datetime object for parsing
            if isinstance(booking_date, datetime):
                dt = booking_date
                logger.info(f"✅ Date is already datetime object")
            else:
                # Try to parse the date
                logger.info(f"🔄 Attempting to parse date string...")
                try:
                    if isinstance(booking_date, str):
                        # Try parsing common formats
                        parsed = False
                        for fmt in ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y']:
                            try:
                                dt = datetime.strptime(booking_date, fmt)
                                logger.info(f"✅ Successfully parsed with format: {fmt}")
                                parsed = True
                                break
                            except:
                                logger.debug(f"   Format {fmt} didn't match")
                                continue

                        if not parsed:
                            # If all parsing fails, try pandas Timestamp
                            logger.info(f"⚠️  Standard formats failed, trying pandas...")
                            import pandas as pd
                            dt = pd.to_datetime(booking_date)
                            logger.info(f"✅ Parsed with pandas")
                    else:
                        logger.info(f"⚠️  Date is not string, trying pandas...")
                        import pandas as pd
                        dt = pd.to_datetime(booking_date)
                        logger.info(f"✅ Parsed with pandas")
                except Exception as e:
                    logger.error(f"❌ Could not parse date: {booking_date}, error: {e}")
                    raise

            # Log parsed datetime
            logger.info(f"")
            logger.info(f"📅 PARSED DATETIME OBJECT:")
            logger.info(f"   Year: {dt.year}")
            logger.info(f"   Month: {dt.month}")
            logger.info(f"   Day: {dt.day}")
            logger.info(f"   Full datetime: {dt}")

            # Format date in full text format (e.g., "October 30, 2025")
            # This is what the Vue.js date picker expects based on the logs
            date_str = dt.strftime('%B %d, %Y')  # Full month name, day, year
            logger.info(f"")
            logger.info(f"📝 FORMATTED DATE STRING (Full text format):")
            logger.info(f"   Display format: {date_str}")
            logger.info(f"   Format used: %B %d, %Y (e.g., October 30, 2025)")

            # Convert time to string format
            if isinstance(booking_time, datetime):
                time_str = booking_time.strftime('%H:%M')
                logger.info(f"")
                logger.info(f"⏰ TIME CONVERSION:")
                logger.info(f"   Time is datetime object")
                logger.info(f"   Formatted as: {time_str}")
            else:
                time_str = str(booking_time).strip()
                logger.info(f"")
                logger.info(f"⏰ TIME CONVERSION:")
                logger.info(f"   Time is string: {time_str}")

            logger.info(f"")
            logger.info(f"🎯 FINAL VALUES TO SET:")
            logger.info(f"   Date: {date_str}")
            logger.info(f"   Time: {time_str}")
            logger.info("="*70)

            # Parse the date components for Vue.js date picker
            day = dt.day
            month = dt.month
            year = dt.year

            # First, check what format the date field expects
            logger.info(f"")
            logger.info(f"🔍 CHECKING DATE FIELD CURRENT STATE:")
            check_date_field_js = """
            (() => {
                const headers = document.querySelectorAll('h5.section-title');
                for (const header of headers) {
                    if (header.textContent.includes('Date')) {
                        const parent = header.closest('.col');
                        if (parent) {
                            const dateInput = parent.querySelector('input[readonly][type="text"]');
                            if (dateInput) {
                                return {
                                    currentValue: dateInput.value,
                                    placeholder: dateInput.placeholder,
                                    defaultValue: dateInput.defaultValue,
                                    pattern: dateInput.pattern,
                                    title: dateInput.title
                                };
                            }
                        }
                    }
                }
                return { error: 'Date field not found' };
            })()
            """
            field_info = self.page.evaluate(check_date_field_js)
            if field_info and not field_info.get('error'):
                logger.info(f"   Current value: '{field_info.get('currentValue')}'")
                logger.info(f"   Placeholder: '{field_info.get('placeholder')}'")
                logger.info(f"   Default value: '{field_info.get('defaultValue')}'")
                logger.info(f"   Pattern: '{field_info.get('pattern')}'")
                logger.info(f"   Title: '{field_info.get('title')}'")

                # Try to detect expected format from placeholder
                placeholder = field_info.get('placeholder', '')
                if placeholder:
                    logger.info(f"   📋 Detected format hint from placeholder: {placeholder}")
            else:
                logger.warning(f"   ⚠️  Could not check field: {field_info.get('error')}")

            # Instead of trying to set the date via JavaScript, we'll interact with the date picker
            # like a user would - by clicking on it and selecting the date
            logger.info(f"")
            logger.info(f"🖱️  INTERACTING WITH DATE PICKER:")
            logger.info(f"   Approach: Click date field → Open picker → Select date")

            try:
                # Find and click the date input field to open the picker
                logger.info(f"   Step 1: Finding date input field...")
                date_input = None
                headers = self.page.query_selector_all('h5.section-title')
                for header in headers:
                    if 'Date' in header.text_content():
                        parent = header.evaluate_handle('el => el.closest(".col")')
                        if parent:
                            date_input = parent.as_element().query_selector('input[readonly][type="text"]')
                            if date_input:
                                logger.info(f"   ✅ Found date input field")
                                break

                if not date_input:
                    logger.error(f"   ❌ Could not find date input field")
                    raise Exception("Date input field not found")

                # Click the date input to open the date picker
                logger.info(f"   Step 2: Clicking date field to open picker...")
                date_input.click()
                self._sleep_with_ui_update(1)  # Wait for picker to open

                # Now we need to set the date in the Vue date picker
                # The picker should be visible now
                logger.info(f"   Step 3: Setting date in picker via Vue...")

                # Use JavaScript to directly set the Vue component's date value
                js_set_date = f"""
                (() => {{
                    // Find the date input
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

                    // ISO date format for Vue
                    const isoDate = '{year}-{month:02d}-{day:02d}';

                    console.log('Setting date to:', isoDate);

                    // Find the Vue component instance
                    let element = dateInput;
                    let vueInstance = null;
                    let level = 0;

                    // Traverse up to find Vue instance
                    while (element && level < 15) {{
                        if (element.__vue__) {{
                            vueInstance = element.__vue__;
                            break;
                        }}
                        element = element.parentElement;
                        level++;
                    }}

                    if (vueInstance) {{
                        console.log('Found Vue instance at level:', level);

                        // Try to find the parent component that manages the date picker
                        let parent = vueInstance.$parent;
                        let parentLevel = 0;
                        while (parent && parentLevel < 10) {{
                            // Look for date-related properties
                            if (parent.$data) {{
                                for (const key in parent.$data) {{
                                    if (key.toLowerCase().includes('date') ||
                                        key.toLowerCase().includes('picker') ||
                                        key === 'internalValue' ||
                                        key === 'lazyValue') {{
                                        console.log('Setting parent.$data.' + key + ' to:', isoDate);
                                        parent.$data[key] = isoDate;
                                    }}
                                }}
                            }}

                            // Try setting direct properties
                            if (parent.internalValue !== undefined) {{
                                parent.internalValue = isoDate;
                                console.log('Set parent.internalValue');
                            }}
                            if (parent.lazyValue !== undefined) {{
                                parent.lazyValue = isoDate;
                                console.log('Set parent.lazyValue');
                            }}

                            // Emit input event
                            if (parent.$emit) {{
                                parent.$emit('input', isoDate);
                                console.log('Emitted input event on parent');
                            }}

                            parent = parent.$parent;
                            parentLevel++;
                        }}

                        // Also try on the instance itself
                        if (vueInstance.internalValue !== undefined) {{
                            vueInstance.internalValue = isoDate;
                        }}
                        if (vueInstance.lazyValue !== undefined) {{
                            vueInstance.lazyValue = isoDate;
                        }}
                        if (vueInstance.$emit) {{
                            vueInstance.$emit('input', isoDate);
                        }}
                    }}

                    // Set the input value directly
                    dateInput.value = '{date_str}';

                    // Trigger events
                    dateInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    dateInput.dispatchEvent(new Event('change', {{ bubbles: true }}));

                    console.log('Final date value:', dateInput.value);

                    return {{ success: true, value: dateInput.value, hadVue: !!vueInstance }};
                }})()
                """

                date_result = self.page.evaluate(js_set_date)

                # Try alternative approach: Click on the date in the calendar picker
                logger.info(f"   Step 4 (Alternative): Looking for calendar picker...")
                logger.info(f"   Target date: {year}-{month:02d}-{day:02d}")
                try:
                    # Wait a bit for the calendar to render
                    self._sleep_with_ui_update(1)

                    # Look for the date picker calendar
                    # Vuetify date pickers typically have v-date-picker-table class
                    picker = self.page.query_selector('.v-picker, .v-date-picker')

                    if picker:
                        logger.info(f"   ✅ Found date picker")

                        # First, we need to navigate to the correct month/year
                        # Check current month/year displayed
                        header = picker.query_selector('.v-date-picker-header, .v-picker__title')
                        if header:
                            current_display = header.text_content()
                            logger.info(f"   Current picker display: {current_display}")

                        # Navigate to correct month/year if needed
                        # Click on month/year header to open month/year selector
                        month_year_button = picker.query_selector('button.v-date-picker-header__value, .v-picker__title__btn')
                        if month_year_button:
                            logger.info(f"   Clicking month/year selector...")
                            month_year_button.click()
                            self._sleep_with_ui_update(0.5)

                            # Now we should see year selector
                            # Click on the target year
                            year_button = picker.query_selector(f'button:has-text("{year}")')
                            if year_button:
                                logger.info(f"   Clicking year {year}...")
                                year_button.click()
                                self._sleep_with_ui_update(0.5)

                            # Now we should see month selector
                            # Month names in English
                            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                         'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                            target_month_name = month_names[month - 1]

                            month_button = picker.query_selector(f'button:has-text("{target_month_name}")')
                            if month_button:
                                logger.info(f"   Clicking month {target_month_name}...")
                                month_button.click()
                                self._sleep_with_ui_update(0.5)

                        # Now we should be on the correct month, click the day
                        logger.info(f"   Looking for day {day} button...")

                        # Find the calendar table
                        calendar_table = picker.query_selector('.v-date-picker-table, [role="grid"]')
                        if calendar_table:
                            # Look for button with the day number
                            # Need to be careful to select the right day (not from adjacent months)
                            day_buttons = calendar_table.query_selector_all('button')

                            for button in day_buttons:
                                button_text = button.text_content().strip()
                                if button_text == str(day):
                                    # Check if button is not disabled (adjacent month)
                                    classes = button.get_attribute('class') or ''
                                    if 'v-btn--disabled' not in classes and 'v-btn--outlined' not in classes:
                                        logger.info(f"   ✅ Clicking day {day} button...")
                                        button.click()
                                        self._sleep_with_ui_update(0.5)
                                        break
                            else:
                                logger.warning(f"   ⚠️  Could not find clickable day {day} button")
                        else:
                            logger.warning(f"   ⚠️  Calendar table not found")
                    else:
                        logger.warning(f"   ⚠️  Date picker not found, trying to close with Escape")
                        self.page.keyboard.press('Escape')

                except Exception as calendar_error:
                    logger.warning(f"   ⚠️  Could not interact with calendar: {calendar_error}")
                    logger.warning(f"   Error details: {type(calendar_error).__name__}: {str(calendar_error)}")
                    # Try to close picker
                    try:
                        self.page.keyboard.press('Escape')
                    except:
                        pass

                self._sleep_with_ui_update(0.5)

            except Exception as e:
                logger.error(f"   ❌ Error interacting with date picker: {e}")
                # Fall back to direct JavaScript setting
                date_result = {'success': False, 'error': str(e)}

            logger.info(f"")
            logger.info(f"📤 DATE SETTING RESULT:")
            if date_result and date_result.get('success'):
                logger.info(f"   ✅ Success!")
                logger.info(f"   Value in field: {date_result.get('value')}")
                logger.info(f"   Expected value: {date_str}")
                if date_result.get('value') == date_str:
                    logger.info(f"   ✅ Values match!")
                else:
                    logger.warning(f"   ⚠️  Values don't match!")
            else:
                error = date_result.get('error', 'Unknown error') if date_result else 'No result'
                logger.error(f"   ❌ Failed: {error}")

            self._sleep_with_ui_update(2)  # Wait for Vue to process updates

            # Verify the date field after Vue processing
            logger.info(f"")
            logger.info(f"🔍 VERIFYING DATE FIELD AFTER 2 SECOND WAIT:")
            verify_date_js = """
            (() => {
                const headers = document.querySelectorAll('h5.section-title');
                for (const header of headers) {
                    if (header.textContent.includes('Date')) {
                        const parent = header.closest('.col');
                        if (parent) {
                            const dateInput = parent.querySelector('input[readonly][type="text"]');
                            if (dateInput) {
                                return {
                                    value: dateInput.value,
                                    placeholder: dateInput.placeholder,
                                    classList: Array.from(dateInput.classList)
                                };
                            }
                        }
                    }
                }
                return { error: 'Date field not found' };
            })()
            """
            verify_result = self.page.evaluate(verify_date_js)
            if verify_result and not verify_result.get('error'):
                logger.info(f"   Current value: {verify_result.get('value')}")
                logger.info(f"   Placeholder: {verify_result.get('placeholder')}")
                logger.info(f"   Classes: {verify_result.get('classList')}")

                # Check if it shows as invalid
                classes = verify_result.get('classList', [])
                if 'error--text' in classes or 'v-input--error' in classes:
                    logger.error(f"   ❌ Field shows as INVALID (has error class)")
                else:
                    logger.info(f"   ✅ Field appears valid (no error class)")
            else:
                logger.warning(f"   ⚠️  Could not verify: {verify_result.get('error')}")

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

            logger.info(f"")
            logger.info(f"📤 TIME SETTING RESULT:")
            if time_result and time_result.get('success'):
                logger.info(f"   ✅ Success!")
                logger.info(f"   Value in field: {time_result.get('value')}")
                logger.info(f"   Expected value: {time_str}")
                if time_result.get('value') == time_str:
                    logger.info(f"   ✅ Values match!")
                else:
                    logger.warning(f"   ⚠️  Values don't match!")
            else:
                error = time_result.get('error', 'Unknown error') if time_result else 'No result'
                logger.error(f"   ❌ Failed: {error}")

            logger.info(f"")
            logger.info(f"✅ Date and time filling process completed")
            logger.info("="*70)

            self._sleep_with_ui_update(2)  # Wait for form validation

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




