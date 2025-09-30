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
    METRO_LOCATIONS_FILE = "metro-locations.json"

    def __init__(self):
        """Initialize WebAutomation with shared browser context."""
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.browser_state_path = Path(self.BROWSER_STATE_FILE)
        self.metro_locations = self._load_metro_locations()

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

            # Click Next button
            logger.info("Clicking Next button...")
            next_button = self.page.wait_for_selector('button:has-text("Next"):not([disabled])', timeout=10000)
            next_button.click()

            logger.info("Successfully completed booking form step 2")
            logger.info("Continue with the booking process in the browser")
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

            # Parse the date components for the date picker
            day = dt.day
            month = dt.month
            year = dt.year

            # First, explore the Vue structure to understand the component
            logger.info("Exploring Vue.js date picker structure...")
            explore_result = self.page.evaluate("""
            (() => {
                const results = {
                    inputFound: false,
                    vueInstances: [],
                    dataProperties: {},
                    methods: []
                };

                // Find the date input more specifically
                // Look for the input that's in the Date section (after h5 with "Date" text)
                let dateInput = null;

                // Strategy 1: Find by looking for Date section
                const headers = document.querySelectorAll('h5.section-title');
                for (const header of headers) {
                    if (header.textContent.includes('Date')) {
                        // Found the Date header, now find the input in the same parent
                        const parent = header.closest('.col');
                        if (parent) {
                            dateInput = parent.querySelector('input[readonly][type="text"]');
                            if (dateInput) {
                                results.foundBy = 'date-section';
                                break;
                            }
                        }
                    }
                }

                // Strategy 2: Find by ID if we know it
                if (!dateInput) {
                    dateInput = document.querySelector('#input-95');
                    if (dateInput) {
                        results.foundBy = 'id';
                    }
                }

                // Strategy 3: Find all readonly inputs and filter
                if (!dateInput) {
                    const allReadonly = document.querySelectorAll('input[readonly][type="text"]');
                    // The date input should NOT be in a multiselect
                    for (const input of allReadonly) {
                        const parent = input.closest('.multiselect');
                        if (!parent) {
                            // This is not in a multiselect, likely the date field
                            dateInput = input;
                            results.foundBy = 'not-multiselect';
                            break;
                        }
                    }
                }

                if (!dateInput) {
                    return { success: false, error: 'Date input not found', results };
                }

                results.inputFound = true;
                results.inputId = dateInput.id;
                results.currentValue = dateInput.value;

                // Walk up the DOM tree and collect all Vue instances
                let element = dateInput;
                let level = 0;

                while (element && level < 10) {
                    if (element.__vue__) {
                        const vue = element.__vue__;
                        const instanceInfo = {
                            level: level,
                            tag: element.tagName,
                            className: element.className,
                            componentName: vue.$options?.name || 'Unknown',
                            hasData: !!vue.$data,
                            hasParent: !!vue.$parent
                        };

                        // Check for date-related properties
                        const dateProps = [];
                        if (vue.$data) {
                            for (const key in vue.$data) {
                                if (key.toLowerCase().includes('date') ||
                                    key.toLowerCase().includes('value') ||
                                    key.toLowerCase().includes('picker')) {
                                    dateProps.push({
                                        key: key,
                                        value: vue.$data[key],
                                        type: typeof vue.$data[key]
                                    });
                                }
                            }
                        }

                        // Check direct properties
                        for (const key of ['value', 'internalValue', 'lazyValue', 'date', 'selectedDate']) {
                            if (vue.hasOwnProperty(key)) {
                                dateProps.push({
                                    key: key,
                                    value: vue[key],
                                    type: typeof vue[key],
                                    direct: true
                                });
                            }
                        }

                        instanceInfo.dateProps = dateProps;
                        results.vueInstances.push(instanceInfo);
                    }
                    element = element.parentElement;
                    level++;
                }

                return { success: true, results };
            })()
            """)

            logger.info(f"Vue exploration result: {explore_result}")

            # Now try multiple strategies to set the date
            logger.info("Attempting to set date using multiple strategies...")

            # Strategy 1: Direct Vue instance property setting with multiple formats
            js_set_date = f"""
            (() => {{
                // Find the date input more specifically (same logic as exploration)
                let dateInput = null;

                // Strategy 1: Find by Date section
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

                // Strategy 2: Find by ID
                if (!dateInput) {{
                    dateInput = document.querySelector('#input-95');
                }}

                // Strategy 3: Find readonly input NOT in multiselect
                if (!dateInput) {{
                    const allReadonly = document.querySelectorAll('input[readonly][type="text"]');
                    for (const input of allReadonly) {{
                        const parent = input.closest('.multiselect');
                        if (!parent) {{
                            dateInput = input;
                            break;
                        }}
                    }}
                }}

                if (!dateInput) {{
                    return {{ success: false, error: 'Date input not found', strategy: 'none' }};
                }}

                const strategies = [];
                let successStrategy = null;

                // Date formats to try
                const isoDate = '{year}-{month:02d}-{day:02d}';
                const displayDate = '{date_str}';
                const usDate = '{month}/{day}/{year}';

                // Walk up to find Vue instances
                let element = dateInput;
                let level = 0;

                while (element && level < 10 && !successStrategy) {{
                    if (element.__vue__) {{
                        const vue = element.__vue__;

                        // Strategy 1a: Try setting $data properties
                        if (vue.$data) {{
                            for (const key in vue.$data) {{
                                if (key.toLowerCase().includes('date') ||
                                    key.toLowerCase().includes('value') ||
                                    key.toLowerCase().includes('picker')) {{

                                    // Try ISO format
                                    vue.$data[key] = isoDate;
                                    strategies.push({{
                                        strategy: '1a-data-iso',
                                        level: level,
                                        property: key,
                                        value: isoDate
                                    }});

                                    // Try display format
                                    vue.$data[key] = displayDate;
                                    strategies.push({{
                                        strategy: '1a-data-display',
                                        level: level,
                                        property: key,
                                        value: displayDate
                                    }});
                                }}
                            }}
                        }}

                        // Strategy 1b: Try direct properties
                        const directProps = ['value', 'internalValue', 'lazyValue', 'date', 'selectedDate', 'pickerDate'];
                        for (const prop of directProps) {{
                            if (vue.hasOwnProperty(prop)) {{
                                // Try ISO format
                                vue[prop] = isoDate;
                                strategies.push({{
                                    strategy: '1b-direct-iso',
                                    level: level,
                                    property: prop,
                                    value: isoDate
                                }});

                                // Try display format
                                vue[prop] = displayDate;
                                strategies.push({{
                                    strategy: '1b-direct-display',
                                    level: level,
                                    property: prop,
                                    value: displayDate
                                }});
                            }}
                        }}

                        // Strategy 1c: Try emitting input event
                        if (vue.$emit) {{
                            vue.$emit('input', isoDate);
                            strategies.push({{
                                strategy: '1c-emit-iso',
                                level: level,
                                value: isoDate
                            }});

                            vue.$emit('input', displayDate);
                            strategies.push({{
                                strategy: '1c-emit-display',
                                level: level,
                                value: displayDate
                            }});
                        }}

                        // Strategy 1d: Try calling methods
                        if (typeof vue.setValue === 'function') {{
                            vue.setValue(isoDate);
                            strategies.push({{
                                strategy: '1d-method-setValue',
                                level: level,
                                value: isoDate
                            }});
                        }}

                        if (typeof vue.updateValue === 'function') {{
                            vue.updateValue(isoDate);
                            strategies.push({{
                                strategy: '1d-method-updateValue',
                                level: level,
                                value: isoDate
                            }});
                        }}

                        // Force update
                        if (vue.$forceUpdate) {{
                            vue.$forceUpdate();
                        }}
                    }}
                    element = element.parentElement;
                    level++;
                }}

                // Strategy 2: Set input value directly and trigger events
                dateInput.removeAttribute('readonly');
                dateInput.value = displayDate;
                dateInput.dispatchEvent(new Event('input', {{ bubbles: true, cancelable: true }}));
                dateInput.dispatchEvent(new Event('change', {{ bubbles: true, cancelable: true }}));
                dateInput.dispatchEvent(new Event('blur', {{ bubbles: true, cancelable: true }}));
                dateInput.setAttribute('readonly', 'readonly');

                strategies.push({{
                    strategy: '2-direct-input',
                    value: displayDate
                }});

                return {{
                    success: true,
                    strategies: strategies,
                    finalValue: dateInput.value,
                    strategiesCount: strategies.length
                }};
            }})()
            """

            date_result = self.page.evaluate(js_set_date)
            logger.info(f"Date set result: {date_result}")
            logger.info(f"Tried {date_result.get('strategiesCount', 0)} strategies")

            time.sleep(2)  # Wait for Vue to process updates

            # Fill time field using JavaScript as well to be safe
            js_set_time = f"""
            (() => {{
                // Find the time input field more specifically
                let timeInput = null;

                // Strategy 1: Find by Time section
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

                // Strategy 2: Find by data-maska attribute
                if (!timeInput) {{
                    timeInput = document.querySelector('input[data-maska]');
                }}

                if (!timeInput) {{
                    console.log('Time input not found');
                    return {{ success: false, error: 'Time input not found' }};
                }}

                console.log('Time input found:', timeInput.id);
                console.log('Current value:', timeInput.value);
                console.log('Current data-maska-value:', timeInput.getAttribute('data-maska-value'));

                // Clear and set the value
                timeInput.value = '';
                timeInput.value = '{time_str}';

                // Trigger events
                timeInput.dispatchEvent(new Event('input', {{ bubbles: true, cancelable: true }}));
                timeInput.dispatchEvent(new Event('change', {{ bubbles: true, cancelable: true }}));
                timeInput.dispatchEvent(new Event('blur', {{ bubbles: true, cancelable: true }}));

                console.log('Final value:', timeInput.value);
                console.log('Final data-maska-value:', timeInput.getAttribute('data-maska-value'));
                return {{ success: true, value: timeInput.value }};
            }})()
            """

            time_result = self.page.evaluate(js_set_time)
            logger.info(f"Time set result: {time_result}")

            if time_result and time_result.get('success'):
                logger.info(f"Time set to {time_str} using JavaScript")
            else:
                error = time_result.get('error', 'Unknown error') if time_result else 'No result'
                logger.warning(f"Could not set time using JavaScript: {error}")

            # Check if the date field actually has the value now
            check_values = self.page.evaluate("""
            (() => {
                // Find date input
                let dateInput = null;
                const headers = document.querySelectorAll('h5.section-title');
                for (const header of headers) {
                    if (header.textContent.includes('Date')) {
                        const parent = header.closest('.col');
                        if (parent) {
                            dateInput = parent.querySelector('input[readonly][type="text"]');
                            if (dateInput) break;
                        }
                    }
                }

                // Find time input
                let timeInput = null;
                for (const header of headers) {
                    if (header.textContent.includes('Time')) {
                        const parent = header.closest('.col');
                        if (parent) {
                            timeInput = parent.querySelector('input[data-maska]');
                            if (timeInput) break;
                        }
                    }
                }

                return {
                    dateValue: dateInput ? dateInput.value : null,
                    timeValue: timeInput ? timeInput.value : null,
                    timeMaskaValue: timeInput ? timeInput.getAttribute('data-maska-value') : null,
                    dateInputId: dateInput ? dateInput.id : null,
                    timeInputId: timeInput ? timeInput.id : null
                };
            })()
            """)
            logger.info(f"Final field values: {check_values}")

            logger.info("Date and time filled successfully")
            time.sleep(2)  # Wait for form validation

        except Exception as e:
            logger.error(f"Error filling date/time: {e}")
            raise

    def close_browser(self):
        """Close the browser and cleanup resources."""
        try:
            # Save browser state before closing
            self._save_browser_state()

            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()

            # Reset all browser-related attributes
            self.playwright = None
            self.browser = None
            self.context = None
            self.page = None
            logger.info("Browser closed and resources cleaned up")
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




